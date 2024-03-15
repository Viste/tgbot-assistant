import asyncio
import logging

from openai import AsyncOpenAI

from tools.dependencies import container

logger = logging.getLogger(__name__)
config = container.get('config')


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

    async def get_resp(self, query: str, name: str):
        response = await self._query_gpt(query, name)
        answer = response
        logger.info('!Response from assistant: %s', response)
        return answer

    async def _query_gpt(self, query: str, name: str):
        try:
            thread = await self.client.beta.threads.create()
            await self.client.beta.threads.messages.create(role="user", thread_id=thread.id, content=query)
            run = await self.client.beta.threads.runs.create(thread_id=thread.id, assistant_id=self.assistant_id,
                                                             instructions=f"ник того с кем ты разговариваешь {name}, обращайся ко всем по никнейму")

            await asyncio.sleep(160)

            messages = await self.client.beta.threads.messages.list(thread_id=thread.id)
            logger.info('FULL MESSAGE: %s', messages)
            logger.info('DATA: %s', messages.data)
            logger.info('CONTENT: %s', messages.data[0].content[0])
            if messages:
                messages_list = messages.data[0]
                logger.info('LAST MESSAGE FROM IF: %s', messages_list)
                return messages_list.content[0].text.value
            else:
                return "No messages found."

        except Exception as e:
            print(f"An error occurred: {e}")
