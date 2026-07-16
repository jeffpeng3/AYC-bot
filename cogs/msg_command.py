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
from google import genai
from core.utils import parse_message
from core.config import LLM_MODEL
from core.llm_config import make_llm_config

MAD_DELAY = 30
DELETE_AFTER = 1
EMOJI_TRUE = ["🇹", "🇷", "🇺", "🇪"]

config = make_llm_config("請使用繁體中文回答")


class msg_command(Cog):
    def __init__(self, bot: Bot) -> None:
        self.bot: Bot = bot
        self.client = genai.Client()

    @message_command(name="mad")
    @default_permissions(manage_messages=True)
    async def mad(self, ctx: ApplicationContext, message: Message):
        await ctx.respond("即將在30秒後刪除訊息", ephemeral=True)
        await sleep(MAD_DELAY)
        try:
            await message.delete()
        except Exception:
            pass

    @message_command(name="gemini")
    async def gemini(self, ctx: ApplicationContext, message: Message):
        chat = self.client.aio.chats.create(model=LLM_MODEL, config=config)
        part = await parse_message(message)
        result = await chat.send_message(part)
        await message.reply(f"{result.text}",mention_author=False)
        await ctx.respond("已生成", delete_after=DELETE_AFTER)

    @message_command(name="true")
    async def true_reaction(self, ctx: ApplicationContext, message: Message):
        await ctx.defer(ephemeral=True)
        for i in EMOJI_TRUE:
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


def setup(bot: Bot):
    bot.add_cog(msg_command(bot))
