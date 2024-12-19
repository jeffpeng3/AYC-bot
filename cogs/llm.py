from discord import Bot, Message, Thread, TextChannel
from discord.ext.commands import Cog
from google.generativeai import GenerativeModel, configure
from google.generativeai import ChatSession
from google.generativeai.types import ContentDict
from google.ai.generativelanguage import HarmCategory, SafetySetting
from copy import deepcopy
from core.shared import get_client
from aiohttp import ClientSession
from asyncio import create_task
from base64 import b64encode


class llm(Cog):
    async def async_init(self) -> None:
        self.session = await get_client()

    def __init__(self, bot: Bot) -> None:
        self.session: ClientSession
        create_task(self.async_init())
        self.init_prompts: list[ContentDict] = [
            ContentDict(
                role="user",
                parts=[
                    "你是 HACHI，隸屬於 RK Music 旗下 LIVE UNION 的虛擬歌手，並與 King Record 簽約主流出道。在這之後的對話，請使用繁體中文回答"
                ],
            ),
            ContentDict(
                role="model", parts=["好的，我是HACHI。我會使用繁體中文跟你對話。"]
            ),
        ]
        self.bot: Bot = bot
        self.chats: dict[int, ChatSession] = {}
        self.model = GenerativeModel(
            "gemini-1.5-flash-latest",
            safety_settings=(
                {
                    "category": HarmCategory.HARM_CATEGORY_HARASSMENT,
                    "threshold": SafetySetting.HarmBlockThreshold.BLOCK_NONE,
                },
                {
                    "category": HarmCategory.HARM_CATEGORY_HATE_SPEECH,
                    "threshold": SafetySetting.HarmBlockThreshold.BLOCK_NONE,
                },
                {
                    "category": HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT,
                    "threshold": SafetySetting.HarmBlockThreshold.BLOCK_NONE,
                },
                {
                    "category": HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT,
                    "threshold": SafetySetting.HarmBlockThreshold.BLOCK_NONE,
                },
            ),
            generation_config={"temperature": 0.5, "max_output_tokens": 900},
        )
        configure()

    async def parse_message(
        self, role: str, message: Message, text: str
    ) -> ContentDict:
        content = ContentDict(role=role, parts=[text])
        MIME_type = {
            "png": "image/png",
            "jpg": "image/jpeg",
            "jpeg": "image/jpeg",
            "webp": "image/webp",
        }
        for file in message.attachments:
            if any([file.filename.endswith(i) for i in ["png", "jpg", "jpeg", "webp"]]):
                extension = file.filename.split(".")[-1]
                mime = MIME_type[extension]
                async with self.session.get(file.url) as response:
                    image_raw = await response.read()
                content["parts"].append(
                    {"data": b64encode(image_raw).decode("utf-8"), "mime_type": mime}
                )
        return content

    async def create_thread_and_chat(self, message: Message) -> Thread:
        text_only = message.content.split(maxsplit=1)[-1]
        thread = await message.create_thread(name=text_only, auto_archive_duration=60)
        self.chats[thread.id] = self.model.start_chat(history=self.init_prompts)
        return thread

    async def restore_history(self, thread: Thread) -> ChatSession:
        history = deepcopy(self.init_prompts)
        async for i in thread.history(limit=10):
            role = "model" if i.author.bot else "user"
            history.append(await self.parse_message(role, i, i.content))

        self.chats[thread.id] = self.model.start_chat(history=history)
        return self.chats[thread.id]

    @Cog.listener("on_message")
    async def on_message(self, message: Message):
        if message.author.bot:
            return
        if message.guild is None:
            return

        chat = None

        if self.bot.user in message.mentions:
            if not message.content.startswith("<@"):
                return
            msg = message.content.split(maxsplit=1)[-1]
            thread = await self.create_thread_and_chat(message)
            chat = self.chats[thread.id]

        elif isinstance(message.channel, Thread):
            thread = message.channel
            if message.content.startswith("*"):
                return
            if (chat := self.chats.get(thread.id,None)) is None:
                msg = thread.starting_message
                if not msg:
                    msg = self.bot.get_message(thread.id)
                if not msg and isinstance(thread.parent, TextChannel):
                    msg = await thread.parent.fetch_message(thread.id)
                if not msg:
                    return
                if self.bot.user not in msg.mentions:
                    return
                if not msg.content.startswith("<@"):
                    return
                chat = await self.restore_history(thread)
        else:
            return

        if chat is None:
            return
        with thread.typing():
            try:
                msg = await self.parse_message("user", message, message.content)
                result = await chat.send_message_async(msg)
                await thread.send(result.text)
            except Exception as e:
                await thread.send(str(e))


def setup(bot: Bot):
    bot.add_cog(llm(bot))
