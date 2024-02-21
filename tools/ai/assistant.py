import asyncio
import logging

from openai import AsyncOpenAI

from tools.utils import config

logger = logging.getLogger(__name__)


class OpenAIAssist:
    max_retries: int

    def __init__(self):
        super().__init__()
        self.model = "gpt-4-0125-preview"
        self.client = AsyncOpenAI(api_key=config.api_key, base_url='http://176.222.52.92:9000/v1')
        self.max_retries = 5
        self.max_tokens = 128000
        self.assistant_id = 'asst_XbFEiwIoTa196kOWZzi3zJQO'
        self.config_tokens = 1024
        self.max_history_size = 10
        self.n_choices = 1
        self.retries = 0
        self.show_tokens = False

    async def get_resp(self, query: str, chat_id: int, name: str) -> tuple[str, int]:
        response = await self._query_gpt(chat_id, query, name)
        answer = ''

        logger.info('!!!!!Response: %s', response)

        answer = response

        total_tokens = response.usage.total_tokens if response.usage else 0
        if response.usage and self.show_tokens:
            answer += "\n\n---\n" \
                      f"💰 Использовано Токенов: {str(response.usage.total_tokens)}" \
                      f" ({str(response.usage.prompt_tokens)} prompt," \
                      f" {str(response.usage.completion_tokens)} completion)"

        return answer, total_tokens

    async def _query_gpt(self, user_id: int, query: str, name: str):
        while self.retries < self.max_retries:
            while self.retries < self.max_retries:
                try:
                    thread = await self.client.beta.threads.create()
                    await self.client.beta.threads.messages.create(role="user", thread_id=thread.id, content=query)
                    run = await self.client.beta.threads.runs.create(thread_id=thread.id, assistant_id=self.assistant_id, instructions=f"ник того с кем ты разговариваешь {name}")

                    await asyncio.sleep(180)

                    messages = await self.client.beta.threads.messages.list(thread_id=thread.id)
                    logging.info('FULL MESSAGE: %s', messages)
                    logging.info('DATA: %s', messages.data)
                    logging.info('CONTENT: %s', messages.data.content[0])
                    if messages:
                        logging.info('CONTENT FROM IF: %s', messages.data.content[0])
                        return messages.data.content[0].text.value
                    else:
                        return "No messages found."

                except Exception as e:
                    print(f"An error occurred: {e}")
                    self.retries += 1
