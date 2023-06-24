import json
import logging
from calendar import monthrange
from datetime import date
from typing import Tuple

import openai
import requests
import tiktoken
from sqlalchemy.ext.asyncio import AsyncSession

from database.manager import UserManager as user_manager
from tools.utils import config

openai.api_key = config.api_key
logger = logging.getLogger(__name__)

args = {
    "temperature": 0,
    "max_tokens": 4096,
    "top_p": 1,
    "frequency_penalty": 0,
    "presence_penalty": 0.8,
    "stop": None
}


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

    async def get_resp(self, query: str, chat_id: int, session: AsyncSession) -> Tuple[str, int]:
        user_manager_instance = user_manager(session)
        dialogs = await user_manager_instance.get_dialogs(chat_id)
        response = await self._query_gpt(chat_id, query, dialogs, session)
        answer = ''
        if response.choices and (len(response.choices) > 1 and self.n_choices > 1 or len(response.choices) >= 0):
            for index, choice in enumerate(response.choices):
                content = choice['message']['content'].strip()
                if index == 0:
                    await user_manager_instance.add_to_history_db(chat_id, role="assistant", content=content)
                answer += f'{index + 1}\u20e3\n'
                answer += content
                answer += '\n\n'
        elif response.choices is None:
            answer = response.error
        else:
            answer = response.choices[0]['message']['content'].strip()
            await user_manager_instance.add_to_history_db(chat_id, role="assistant", content=answer)

        total_tokens = response.usage['total_tokens'] if response.usage else 0
        if response.usage and (self.show_tokens or chat_id == -1001582049557):
            answer += "\n\n---\n" \
                      f"💰 Использовано Токенов: {str(response.usage['total_tokens'])}" \
                      f" ({str(response.usage['prompt_tokens'])} prompt," \
                      f" {str(response.usage['completion_tokens'])} completion)"

        return answer, total_tokens

    async def _query_gpt(self, user_id, query, dialogs, session: AsyncSession):
        self.retries = 0
        result = None
        user_manager_instance = user_manager(session)
        for _ in range(self.max_retries):
            try:
                if not dialogs:
                    await user_manager_instance.reset_history(user_id)
                    dialogs = await user_manager_instance.get_dialogs(user_id)

                await user_manager_instance.add_to_history_db(user_id, role="user", content=query)

                token_count = self._count_tokens(dialogs)
                exceeded_max_tokens = token_count + self.config_tokens > self.max_tokens

                exceeded_max_history_size = len(dialogs) > self.max_history_size
                if exceeded_max_tokens or exceeded_max_history_size:
                    logging.info(f'Chat history for chat ID {user_id} is too long. Summarising...')
                    try:
                        summary = await self._summarise(dialogs[:-1])
                        logging.info(f'Summary: {summary}')
                        await user_manager_instance.reset_history(user_id)
                        await user_manager_instance.add_to_history_db(user_id, role="assistant", content=summary)
                        await user_manager_instance.add_to_history_db(user_id, role="user", content=query)
                        logging.info("Dialog From summary: %s", dialogs)
                    except Exception as e:
                        logging.info(f'Error while summarising chat history: {str(e)}. Popping elements instead...')
                        dialogs = dialogs[-self.max_history_size:]
                        logging.info("Dialog From summary exception: %s", dialogs)

                response = await openai.ChatCompletion.acreate(model=self.model, messages=dialogs, **args)
                print(dialogs)
                result = response
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

    async def get_stats(self, user_id: int, session: AsyncSession) -> tuple[int, int]:
        dialogs = await user_manager(session).get_dialogs(user_id)
        return len(dialogs), self._count_tokens(dialogs)

    async def _summarise(self, dialogs) -> str:
        messages = [{"role": "assistant", "content": "Summarize this conversation in 700 characters or less"},
                    {"role": "user", "content": json.dumps(dialogs)}]
        response = await openai.ChatCompletion.acreate(model=self.model, messages=messages, temperature=0.1)
        return response.choices[0]['message']['content']

    def _count_tokens(self, dialogs) -> int:
        try:
            model = self.model
            encoding = tiktoken.encoding_for_model(model)
        except KeyError:
            encoding = tiktoken.get_encoding("gpt-3.5-turbo-16k-0613")

        tokens_per_message = 4
        tokens_per_name = 1

        num_tokens = sum(tokens_per_message + sum(len(encoding.encode(value)) for key, value in message.items())
                         + (tokens_per_name if "name" in message else 0) for message in dialogs) + 3
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
