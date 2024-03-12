import logging

from openai import AsyncOpenAI

from tools.utils import config

logger = logging.getLogger(__name__)


class OpenAIVision:
    max_retries: int

    def __init__(self):
        super().__init__()
        self.model = "gpt-4-vision-preview"
        self.max_retries = 10
        self.max_tokens = 8196
        self.config_tokens = 1024
        self.max_history_size = 30
        self.n_choices = 1
        self.retries = 0
        self.show_tokens = False
        self.client = AsyncOpenAI(api_key=config.api_key, base_url='http://176.222.52.92:9000/v1')
        self.args = {"max_tokens": 1024}

    async def get_vision(self, img: str):
        response = await self._query_gpt(img)
        answer = ''

        if response.choices and len(response.choices) > 1 and self.n_choices > 1:
            for index, choice in enumerate(response.choices):
                content = choice.message.content.strip()
                answer += f'{index + 1}\u20e3\n'
                answer += content
                answer += '\n\n'
        elif response.choices and len(response.choices) >= 0:
            answer = response.choices[0].message.content.strip()
        else:
            answer = response.choices[0].message.content.strip()

        return answer

    async def _query_gpt(self, img: str):
        while self.retries < self.max_retries:
            try:

                return await self.client.chat.completions.create(model=self.model, messages=[
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "text",
                                "text": "If there is a man or woman with a clown nose in the image, just answer yes! If not, then no accordingly."},
                            {
                                "type": "image_url",
                                "image_url":
                                    {
                                        "url": f"{img}", }, }, ], }, ], **self.args)

            except Exception as err:
                self.retries += 1
                logger.info("Dialog From custom exception: %s", img)
                if self.retries == self.max_retries:
                    return f'⚠️Ошибочка вышла ⚠️\n{str(err)}', err
