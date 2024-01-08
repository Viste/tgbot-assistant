import aiohttp
# from tools.utils import config


class ClientOBS:
    def __init__(self):
        super().__init__()
        self.key = "cdysXNXibLWg1dgGfLVyCW0r2eXrNhG466QPZ2Hn4yYJx5hFqnuVMz0e"
        self.url = "https://obs2.pprfnk.tech/telegram"
        self.session = aiohttp.ClientSession()

    async def send_request(self, message: str, meta: dict):
        headers = {
            "Content-Type": "application/json"
            }
        data = {
            "title": title, "message": message, "meta": meta, "key": self.key
            }
        async with self.session.post(self.url, headers=headers, json=data) as resp:
            return await resp.json()

    async def send_message(self, name: str, message: str):
        meta = {"sender": name}
        return await self.send_request(message, meta)

    async def close(self):
        await self.session.close()
