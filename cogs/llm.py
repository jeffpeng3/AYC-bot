from discord import Bot, Message, Thread, TextChannel
from discord.ext.commands import Cog
from google import genai
from google.genai.chats import AsyncChat
from google.genai.types import Content
from core.shared import get_client
from aiohttp import ClientSession
from asyncio import create_task
from core.utils import parse_message, split_markdown_text
from core.config import LLM_MODEL
from core.llm_config import make_llm_config

THREAD_AUTO_ARCHIVE_DURATION = 60
THREAD_HISTORY_LIMIT = 10

SYSTEM_INSTRUCTION = """你是 HACHI，現居於日本北海道，因此時區比其他人快一小時，是隸屬於 RK Music 旗下 LIVE UNION 的虛擬歌手，並與 King Record 簽約主流出道。
請使用繁體中文回答。
在這之後的多人對話，我會在開頭加上說話者的標籤，
格式為
<author>{User Name}({ID})</author>
<content>{text}</content>

你在回覆時，千萬不要使用<author>與<context>標籤。
必須遵照格式 @<ID> 來提及特定的使用者。

例如：
<author>HACHI🐝(551024169442344970)</author>
<content>我是誰</content>

你可以使用以下方式回覆：
你是HACHI🐝，我可以用<@551024169442344970>來提及你
"""

config = make_llm_config(SYSTEM_INSTRUCTION)


class llm(Cog):
    async def _init_session(self) -> None:
        self.session = await get_client()

    def __init__(self, bot: Bot) -> None:
        self.session: ClientSession
        create_task(self._init_session())
        self.bot: Bot = bot
        self.client: genai.Client = genai.Client()
        self.chats: dict[int, AsyncChat] = {}

    async def create_thread_and_chat(self, message: Message) -> Thread:
        text_only = message.content.split(maxsplit=1)[-1][:20]
        thread = await message.create_thread(name=text_only, auto_archive_duration=THREAD_AUTO_ARCHIVE_DURATION)
        self.chats[thread.id] = self.client.aio.chats.create(model=LLM_MODEL, config=config)
        return thread

    async def restore_history(self, thread: Thread) -> AsyncChat:
        history = []
        async for i in thread.history(limit=THREAD_HISTORY_LIMIT):
            role = "model" if i.author.bot else "user"
            history.append(Content(role=role, parts=[await parse_message(i)]))

        self.chats[thread.id] = self.client.aio.chats.create(
            model=LLM_MODEL, config=config, history=history
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
            message.content = message.content.split(">", 1)[-1]
            # print(f"message.content: {message.content}")
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
                msg = await parse_message(message)
                result = await chat.send_message(msg)
                text = result.text
                if text is None:
                    await thread.send("無法產生回應")
                    return

                # 分割長訊息，保持 markdown 格式完整
                chunks = await split_markdown_text(text)
                for chunk in chunks:
                    await thread.send(chunk)
            except Exception as e:
                await thread.send(str(e))


def setup(bot: Bot):
    bot.add_cog(llm(bot))
