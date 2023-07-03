import json
import logging
import os
from calendar import monthrange
from datetime import date
from typing import Tuple, Dict, List

import openai
import requests
import tiktoken
from sqlalchemy.ext.asyncio import AsyncSession

from database.manager import UserManager
from tools.utils import config

openai.api_key = config.api_key
logger = logging.getLogger(__name__)

with open(os.path.join(os.path.dirname(__file__), 'content.txt'), 'r', encoding='utf8') as f:
    sys_msg = f.read()


class UserHistoryManager:
    def __init__(self, session: AsyncSession):
        self.session = session
        self.user_manager = UserManager(session)

    async def get_history(self, user_id: int) -> List[Dict[str, str]]:
        user = await self.user_manager.get_user(user_id)
        return user.history if user else []

    async def add_to_history(self, user_id: int, role: str, content: str) -> None:
        user = await self.user_manager.get_user(user_id)
        if user is not None:
            history = user.history
            history.append({"role": role, "content": content})
            if len(history) > 60:
                history = history[-60:]
            logging.info(f"Adding to history: user_id={user_id}, role={role}, content={content}")
            await self.user_manager.update_user_history_and_commit(user, history)

    async def reset_history(self, user_id: int, content: str) -> None:
        user = await self.user_manager.get_user(user_id)
        if user is not None:
            await self.user_manager.update_user_history_and_commit(user, [{"role": "system", "content": content}])


class OpenAI:
    max_retries: int

    def __init__(self, session: AsyncSession):
        super().__init__()
        self.model = "gpt-3.5-turbo-16k-0613"
        self.session = session
        self.history_manager = UserHistoryManager(self.session)
        self.max_retries = 5
        self.max_tokens = 16096
        self.config_tokens = 4096
        self.max_history_size = 10
        self.n_choices = 1
        self.retries = 0
        self.show_tokens = False
        self.args = {
            "temperature": 0,
            "max_tokens": 4096,
            "top_p": 1,
            "frequency_penalty": 0,
            "presence_penalty": 0.8,
            "stop": None
        }
        self.content = sys_msg

    async def get_resp(self, query: str, chat_id: int) -> Tuple[str, str]:
        user_manager = UserManager(self.session)
        user = await user_manager.get_user(chat_id)

        if user is None:
            user = await user_manager.create_user(chat_id)

        user.system_message = self.content
        await self.history_manager.reset_history(chat_id, self.content)

        response = await self._query_gpt(chat_id, query, self.session)
        answer = ''

        if response.choices and len(response.choices) > 1 and self.n_choices > 1:
            for index, choice in enumerate(response.choices):
                content = choice['message']['content'].strip()
                if index == 0:
                    await self.history_manager.add_to_history(chat_id, role="assistant", content=content)
                answer += f'{index + 1}\u20e3\n'
                answer += content
                answer += '\n\n'
        elif response.choices and len(response.choices) >= 0:
            answer = response.choices[0]['message']['content'].strip()
            await self.history_manager.add_to_history(chat_id, role="assistant", content=answer)
        else:
            answer = response.choices[0]['message']['content'].strip()

        await self.history_manager.add_to_history(chat_id, role="assistant", content=answer)

        total_tokens = response.usage['total_tokens'] if response.usage else 0
        if response.usage and self.show_tokens:
            answer += "\n\n---\n" \
                      f"💰 Использовано Токенов: {str(response.usage['total_tokens'])}" \
                      f" ({str(response.usage['prompt_tokens'])} prompt," \
                      f" {str(response.usage['completion_tokens'])} completion)"

        return answer, total_tokens

    async def _query_gpt(self, user_id, query, session: AsyncSession):
        user_manager = UserManager(session)
        user = await user_manager.get_user(user_id)

        await self.history_manager.add_to_history(user_id, role="user", content=query)

        for _ in range(self.max_retries):
            try:
                if user is None:
                    await self.history_manager.reset_history(user_id, self.content)

                await self.history_manager.add_to_history(user_id, role="user", content=query)

                user = await user_manager.get_user(user_id)
                history_json = json.dumps(user.history, ensure_ascii=False)

                if isinstance(user.history, str):
                    user_history = json.loads(user.history)
                else:
                    user_history = user.history

                token_count = self._count_tokens(history_json)
                exceeded_max_tokens = token_count + self.config_tokens > self.max_tokens
                exceeded_max_history_size = len(user_history) > self.max_history_size

                if exceeded_max_tokens or exceeded_max_history_size:
                    logging.info(f'Chat history for chat ID {user_id} is too long. Summarising...')
                    try:
                        summary = await self._summarise(user_history[:-1])
                        logging.info(f'Summary: {summary}')
                        await self.history_manager.reset_history(user_id, self.content)
                        await self.history_manager.add_to_history(user_id, role="assistant", content=summary)
                        await self.history_manager.add_to_history(user_id, role="user", content=query)
                        logging.info("Dialog From summary: %s", user_history)
                    except Exception as e:
                        logging.info(f'Error while summarising chat history: {str(e)}. Popping elements instead...')
                        user_history = user_history[-self.max_history_size:]
                        logging.info("Dialog From summary exception: %s", user_history)

                logging.info(f"Sending history to OpenAI API: {user_history}")

                response = await openai.ChatCompletion.acreate(model=self.model, messages=user_history, **self.args)
                print(history_json)
                result = response
                logging.info('RESULT-RESPONSE QUERY GPT: %s', result)
                break

            except (openai.error.RateLimitError, openai.error.InvalidRequestError, Exception) as e:
                if isinstance(e, openai.error.RateLimitError):
                    error_msg = f'⚠️OpenAI: Превышены лимиты ⚠️\n{str(e)}'
                elif isinstance(e, openai.error.InvalidRequestError):
                    error_msg = f'⚠️OpenAI: кривой запрос ⚠️\n{str(e)}'
                else:
                    error_msg = f'⚠️Ошибочка вышла ⚠️\n{str(e)}'
                result = {'choices': None, 'error': error_msg}
            else:
                break

        return result

    async def _summarise(self, conversation) -> str:
        messages = [
            {"role": "assistant", "content": "Summarize this conversation in 700 characters or less"},
            {"role": "user", "content": str(conversation)}
        ]
        response = await openai.ChatCompletion.acreate(
            model=self.model,
            messages=messages,
            temperature=0.1
        )
        return response.choices[0]['message']['content']

    def _count_tokens(self, history_json: str) -> int:
        try:
            model = self.model
            encoding = tiktoken.encoding_for_model(model)
        except KeyError:
            encoding = tiktoken.get_encoding("gpt-3.5-turbo-16k-0613")

        history = json.loads(history_json)

        tokens_per_message = 4
        tokens_per_name = 1

        num_tokens = sum(tokens_per_message + sum(len(encoding.encode(value)) for key, value in message.items())
                         + (tokens_per_name if "name" in message else 0) for message in history) + 4
        return num_tokens

    @staticmethod
    def get_money():
        headers = {
            "Authorization": f"Bearer {openai.api_key}"
        }
        today = date.today()
        first_day = date(today.year, today.month, 1)
        _, last_day_of_month = monthrange(today.year, today.month)
        last_day = date(today.year, today.month, last_day_of_month)
        params = {
            "start_date": first_day,
            "end_date": last_day
        }
        response = requests.get("https://api.openai.com/dashboard/billing/usage", headers=headers, params=params)
        billing_data = json.loads(response.text)
        usage_month = billing_data["total_usage"] / 100
        return usage_month
