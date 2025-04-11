from discord import Bot, Message, Thread, TextChannel
from discord.ext.commands import Cog
from google import genai
from google.genai.chats import AsyncChat
from google.genai.types import (
    Tool,
    GenerateContentConfig,
    GoogleSearch,
    Part,
    Blob,
    SafetySetting,
    HarmCategory,
    HarmBlockThreshold,
)
from pprint import pformat
from core.shared import get_client
from aiohttp import ClientSession
from asyncio import create_task

model = "gemini-2.0-flash"
config = GenerateContentConfig(
    system_instruction="你是 HACHI，隸屬於 RK Music 旗下 LIVE UNION 的虛擬歌手，並與 King Record 簽約主流出道。在這之後的對話，請使用繁體中文回答",
    tools=[Tool(google_search=GoogleSearch())],
    temperature=0.5,
    max_output_tokens=900,
    safety_settings=[
        SafetySetting(
            category=HarmCategory.HARM_CATEGORY_HARASSMENT,
            threshold=HarmBlockThreshold.BLOCK_NONE,
        ),
        SafetySetting(
            category=HarmCategory.HARM_CATEGORY_HATE_SPEECH,
            threshold=HarmBlockThreshold.BLOCK_NONE,
        ),
        SafetySetting(
            category=HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT,
            threshold=HarmBlockThreshold.BLOCK_NONE,
        ),
        SafetySetting(
            category=HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT,
            threshold=HarmBlockThreshold.BLOCK_NONE,
        ),
    ],
)


class llm(Cog):
    async def async_init(self) -> None:
        self.session = await get_client()

    def __init__(self, bot: Bot) -> None:
        self.session: ClientSession
        create_task(self.async_init())
        self.bot: Bot = bot
        self.client = genai.Client()
        self.chats: dict[int, AsyncChat] = {}

    async def parse_message(self, role: str, message: Message, text: str) -> Part:
        part = Part(text=text)
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
                part.inline_data = Blob(data=image_raw, mime_type=mime)
        return part

    async def create_thread_and_chat(self, message: Message) -> Thread:
        text_only = message.content.split(maxsplit=1)[-1]
        thread = await message.create_thread(name=text_only, auto_archive_duration=60)
        self.chats[thread.id] = self.client.aio.chats.create(model=model, config=config)
        return thread

    async def restore_history(self, thread: Thread) -> AsyncChat:
        history = []
        async for i in thread.history(limit=10):
            role = "model" if i.author.bot else "user"
            history.append(await self.parse_message(role, i, i.content))

        self.chats[thread.id] = self.client.chats.create(
            model=model, config=config, history=history
        )
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
            if (chat := self.chats.get(thread.id, None)) is None:
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
                result = await chat.send_message(msg)
                # if result.candidates and result.candidates[0].content:
                #     await thread.send(pformat(result.candidates[0]))
                await thread.send(result.text)
            except Exception as e:
                await thread.send(str(e))


def setup(bot: Bot):
    bot.add_cog(llm(bot))
