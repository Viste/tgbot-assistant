import logging

import openai

from tools.utils import config

openai.api_key = config.api_key
logger = logging.getLogger(__name__)


class Moderator:

    def __init__(self):
        super().__init__()
        self.model = "text-moderation-latest"
        self.max_tokens = 8192
        self.max_retries = 10
        self.n_choices = 1
        self.retries = 0
        self.args = {"temperature": 0, "max_tokens": 4096, "top_p": 1, "frequency_penalty": 0,
                     "presence_penalty": 0.8, "stop": None}

    async def _query_gpt_moderate(self, query):
        while self.retries < self.max_retries:
            try:
                response = await openai.Moderation.acreate(model=self.model, input=query)
                result = response
                logging.info("Result: %s", result)
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

    async def get_resp_mod(self, chat_id: int, query: str):
        response = await self._query_gpt_moderate(query)

        print(response["results"][0])
