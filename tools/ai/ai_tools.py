import json
import logging
import os
from calendar import monthrange
from datetime import date
from typing import Tuple

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


class OpenAI:
    max_retries: int

    def __init__(self):
        super().__init__()
        self.model = "gpt-3.5-turbo-16k-0613"
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

    async def get_resp(self, query: str, chat_id: int, session: AsyncSession) -> Tuple[str, str]:
        user_manager = UserManager(session)
        user = await user_manager.get_user(chat_id)

        if user is None:
            user = await user_manager.create_user(chat_id)
        self.content = user.system_message

        response = await self._query_gpt(chat_id, query, session)
        answer = ''

        if response.choices and len(response.choices) > 1 and self.n_choices > 1:
            for index, choice in enumerate(response.choices):
                content = choice['message']['content'].strip()
                if index == 0:
                    await self.add_to_history(chat_id, role="assistant", content=content, session=session)
                answer += f'{index + 1}\u20e3\n'
                answer += content
                answer += '\n\n'
        elif response.choices and len(response.choices) >= 0:
            answer = response.choices[0]['message']['content'].strip()
            await self.add_to_history(chat_id, role="assistant", content=answer, session=session)
        else:
            answer = response.choices[0]['message']['content'].strip()

        await self.add_to_history(chat_id, role="assistant", content=answer, session=session)

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
        for _ in range(self.max_retries):
            try:
                if user is None:
                    await self.reset_history(user_id, session)

                await self.add_to_history(user_id, role="user", content=query, session=session)

                history_json = json.dumps(user.history, ensure_ascii=False)

                token_count = self._count_tokens(history_json)
                exceeded_max_tokens = token_count + self.config_tokens > self.max_tokens
                exceeded_max_history_size = len(user.history) > self.max_history_size

                if exceeded_max_tokens or exceeded_max_history_size:
                    logging.info(f'Chat history for chat ID {user_id} is too long. Summarising...')
                    try:
                        summary = await self._summarise(user.history[:-1])
                        logging.info(f'Summary: {summary}')
                        await self.reset_history(user_id, session)
                        await self.add_to_history(user_id, role="assistant", content=summary, session=session)
                        await self.add_to_history(user_id, role="user", content=query, session=session)
                        logging.info("Dialog From summary: %s", user.history)
                    except Exception as e:
                        logging.info(f'Error while summarising chat history: {str(e)}. Popping elements instead...')
                        user.history = user.history[-self.max_history_size:]
                        logging.info("Dialog From summary exception: %s", user.history)

                logging.info(f"Sending history to OpenAI API: {user.history}")

                response = await openai.ChatCompletion.acreate(model=self.model, messages=user.history, **self.args)
                print(user.history)
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

    async def add_to_history(self, user_id, role, content, session: AsyncSession):
        user_manager = UserManager(session)
        user = await user_manager.get_user(user_id)

        if user is not None:
            history = user.history
            history.append({"role": role, "content": content})

            if len(history) > 60:
                history = history[-60:]

            logging.info(f"Updating history for user_id={user_id}, history={history}")
            await user_manager.update_user_history_and_commit(user, history)

    async def reset_history(self, user_id, session: AsyncSession, content=''):
        if content == '':
            content = self.content
        user_manager = UserManager(session)
        user = await user_manager.get_user(user_id)

        if user is not None:
            await user_manager.update_user_history_and_commit(user, [{"role": "system", "content": content}])

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
