from asyncio import sleep
from discord import (
    ApplicationContext,
    Interaction,
    Message,
    Bot,
    default_permissions,
    message_command,
)
from discord.ext.commands import Cog
from core.emoji_list import Emoji
from discord.ui.modal import Modal
from discord.ui.input_text import InputText
from  google.generativeai.generative_models import GenerativeModel
from google.ai.generativelanguage import HarmCategory, SafetySetting


class msg_command(Cog):
    def __init__(self, bot: Bot) -> None:
        self.bot: Bot = bot
        self.model = GenerativeModel(
            "gemini-pro",
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
        )

    @message_command(name="mad")
    @default_permissions(manage_messages=True)
    async def mad(self, ctx: ApplicationContext, message: Message):
        await ctx.respond("即將在30秒後刪除訊息", ephemeral=True)
        await sleep(30)
        try:
            await message.delete()
        except BaseException:
            pass

    @message_command(name="gemini")
    async def gemini(self, ctx: ApplicationContext, message: Message):
        content = message.content
        if not content:
            await ctx.respond("無法取得訊息內容", ephemeral=True)
            return
        await ctx.defer(ephemeral=True)
        chats = [
            {"role": "user", "parts": ["請使用繁體中文回答"]},
            {"role": "model", "parts": ["好的。我會使用繁體中文回答。"]},
        ]
        chats.append(
            {"role": "user", "parts": [content]},
        )
        result = await self.model.generate_content_async(chats)
        await message.reply(f"{result.text}",mention_author=False)
        await ctx.respond("已生成", delete_after=1)

    @message_command(name="true")
    async def true_reaction(self, ctx: ApplicationContext, message: Message):
        await ctx.defer(ephemeral=True)
        emoji = ["🇹", "🇷", "🇺", "🇪"]
        for i in emoji:
            await message.add_reaction(i)
        await ctx.delete()

    @message_command(name="text reaction")
    async def text_reaction(self, ctx: ApplicationContext, message: Message):
        async def callback(modal: Modal, inter: Interaction):
            text = modal.children[0].value
            if not text:
                return
            text = text.lower()
            emoji = []
            sucess = []
            while text:
                if pair := [*filter(text.startswith, Emoji.multi_word)]:
                    for i in pair:
                        temp = Emoji.multi_word[i]
                        sucess = [*filter(lambda x: not emoji.count(x), temp)]
                        if sucess:
                            emoji.append(sucess[0])
                            text = text[len(i) :]
                            continue
                    if sucess:
                        continue

                temp = Emoji.single_word[text[0]]
                sucess = [*filter(lambda x: not emoji.count(x), temp)]
                if sucess:
                    emoji.append(sucess[0])
                    text = text[1:]
                    continue
                else:
                    break
            emoji_str = " ".join(emoji)
            if text:
                prompt = f"無法合成在這之後的文字:{text}\n目前的組合為:{emoji_str}"
                await inter.response.send_message(content=prompt, ephemeral=True)
                return
            await inter.response.send_message(
                content=f"我正在幫你點{emoji_str}", ephemeral=True
            )
            for i in emoji:
                await message.add_reaction(i)

        modal = Modal(
            InputText(label="你想react的文字", placeholder="僅限英文"),
            title="文字反應生成器",
        )
        modal.callback = lambda interaction: callback(modal, interaction)
        await ctx.interaction.response.send_modal(modal)

    @message_command(name="quote")
    async def quote(self, ctx: ApplicationContext, message: Message):
        await ctx.respond(f"> {message.content}", ephemeral=True)


def setup(bot: Bot):
    bot.add_cog(msg_command(bot))
