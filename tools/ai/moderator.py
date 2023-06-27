import logging

import openai

from tools.utils import config

openai.api_key = config.api_key
logger = logging.getLogger(__name__)


class Moderator:

    def __init__(self):
        super().__init__()
        self.model = "text-moderation-latest"
        self.max_retries = 10
        self.retries = 0

    async def query_gpt_mod(self, query):
        for retry in range(self.max_retries):
            try:
                response = await openai.Moderation.acreate(model=self.model, input=query)
                result = response["results"][0]
                logging.info("Result: %s", result)
                return result
            except (openai.error.RateLimitError, openai.error.InvalidRequestError, Exception) as e:
                self.retries += 1
                if isinstance(e, openai.error.RateLimitError):
                    error_msg = f'⚠️OpenAI: Превышены лимиты ⚠️\n{str(e)}'
                elif isinstance(e, openai.error.InvalidRequestError):
                    error_msg = f'⚠️OpenAI: кривой запрос ⚠️\n{str(e)}'
                else:
                    error_msg = f'⚠️Ошибочка вышла ⚠️\n{str(e)}'
                result = {'choices': None, 'error': error_msg}
                return result
        logging.warning("Max retries exceeded for query: %s", query)
        return {'choices': None, 'error': 'Max retries exceeded'}
