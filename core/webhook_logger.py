from asyncio import create_task
from os import getenv
from aiohttp import ClientSession
from discord import Bot, Webhook
from discord.ext.commands import Cog
from core.shared import get_client


class WebhookLogger(Cog):
    def __init__(self, bot: Bot, env_key: str):
        self.bot = bot
        self.env_key = env_key
        self.session: ClientSession | None = None
        self.webhook: Webhook | None = None
        create_task(self._init())

    async def _init(self):
        self.session = await get_client()
        url = getenv(self.env_key, "")
        if url:
            self.webhook = Webhook.from_url(url, session=self.session)
