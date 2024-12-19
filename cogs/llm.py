from discord import Bot, Message, Thread, TextChannel
from discord.ext.commands import Cog
from google.generativeai import GenerativeModel, configure
from google.generativeai import ChatSession
from google.generativeai.types import ContentDict
from google.ai.generativelanguage import HarmCategory, SafetySetting
from copy import deepcopy

llm_message = list[dict[str, str | list[str]]]


class llm(Cog):
    def __init__(self, bot: Bot) -> None:
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
            generation_config={"temperature": 0.5,'max_output_tokens': 900},
        )
        configure()

    # def restore_context(self, thread_id: int, role: str, content: str) -> None:
    #     if content.startswith("*"):
    #         return
    #     if thread_id not in self.chats:
    #         self.chats[thread_id] =
    #     if self.chats[thread_id][-1]["role"] == role:
    #         self.chats[thread_id][-1]["parts"].append(content)  # type: ignore
    #     else:
    #         self.chats[thread_id].append({"role": role, "parts": [content]})

    @Cog.listener("on_message")
    async def on_message(self, message: Message):
        if message.author.bot:
            return
        if message.guild is None:
            return
        if self.bot.user in message.mentions:
            if not message.content.startswith("<@"):
                return
            msg = message.content.split(maxsplit=1)[-1]
            thread = await message.create_thread(name=msg, auto_archive_duration=60)
            with thread.typing():
                try:
                    self.chats[thread.id] = self.model.start_chat(
                        history=self.init_prompts
                    )
                    result = await self.chats[thread.id].send_message_async(msg)
                    await thread.send(result.text)
                except Exception as e:
                    await thread.send(str(e))
            return

        if isinstance(message.channel, Thread):
            thread = message.channel
            if message.content.startswith("*"):
                return
            if thread.id not in self.chats:
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
                history = deepcopy(self.init_prompts)
                async for i in thread.history(limit=10):
                    if i.author.bot:
                        history.append(ContentDict(role="model", parts=[i.content]))
                    else:
                        history.append(ContentDict(role="user", parts=[i.content]))
                self.chats[thread.id] = self.model.start_chat(history=history)
            with thread.typing():
                try:
                    result = await self.chats[thread.id].send_message_async(message.content)
                    await thread.send(result.text)
                except Exception as e:
                    await thread.send(str(e))


def setup(bot: Bot):
    bot.add_cog(llm(bot))
