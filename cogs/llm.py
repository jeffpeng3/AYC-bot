from discord import Bot, Message, Thread, TextChannel
from discord.ext.commands import Cog
import google.generativeai as genai
from google.ai.generativelanguage import HarmCategory, SafetySetting

llm_message = list[dict[str, str | list[str]]]


class llm(Cog):
    def __init__(self, bot: Bot) -> None:
        self.bot: Bot = bot
        self.chats: dict[int, llm_message] = {}
        self.model = genai.GenerativeModel(
            "models/gemini-1.5-flash",
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
            generation_config={"temperature": 0.5},
        )
        genai.configure()

    def append_message(self, thread_id: int, role: str, content: str) -> None:
        if content.startswith("*"):
            return
        if thread_id not in self.chats:
            self.chats[thread_id] = [
                {"role": "user", "parts": ["請使用繁體中文回答"]},
                {"role": "model", "parts": ["好的。我會使用繁體中文回答。"]},
            ]
        if self.chats[thread_id][-1]["role"] == role:
            self.chats[thread_id][-1]["parts"].append(content)  # type: ignore
        else:
            self.chats[thread_id].append({"role": role, "parts": [content]})

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
                    self.append_message(thread.id, "user", msg)
                    result = await self.model.generate_content_async(
                        self.chats[thread.id],
                        tools={"google_search_retrieval": {},"code_execution": {}},
                    )
                    self.append_message(thread.id, "model", result.text)
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
                async for i in thread.history(limit=10):
                    if i.author.bot:
                        self.append_message(thread.id, "model", i.content)
                    else:
                        self.append_message(thread.id, "user", i.content)

            with thread.typing():
                try:
                    msg = message.content.split(maxsplit=1)[-1]
                    self.append_message(thread.id, "user", msg)
                    result = await self.model.generate_content_async(
                        self.chats[thread.id],
                        tools={"google_search_retrieval": {},"code_execution": {}},
                    )
                    self.append_message(thread.id, "model", result.text)
                    await thread.send(result.text)
                except Exception as e:
                    await thread.send(str(e))


def setup(bot: Bot):
    bot.add_cog(llm(bot))
