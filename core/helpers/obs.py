import aiohttp
# from tools.utils import config


class ClientOBS:
    def __init__(self):
        super().__init__()
        self.key = "cdysXNXibLWg1dgGfLVyCW0r2eXrNhG466QPZ2Hn4yYJx5hFqnuVMz0e"
        self.url = "https://obs2.pprfnk.tech/telegram"
        self.session = aiohttp.ClientSession()

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc, tb):
        await self.close()

    async def send_request(self, name: str, message: str):
        headers = {
            "Content-Type": "application/json"
            }
        data = {
            "name": name,
            "message": message,
            "key": self.key
            }
        async with self.session.post(self.url, headers=headers, json=data) as resp:
            return await resp.json()

    async def close(self):
        await self.session.close()
