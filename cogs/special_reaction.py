import logging
from asyncio import create_task
from discord import (
    Message,
    Bot,
    Reaction,
    User,
    VoiceChannel,
)
from discord.ext.commands import Cog
from discord.abc import GuildChannel

logger = logging.getLogger(__name__)

JJ_USER_ID = 594546616107663530
JJ_CHANNEL_ID = 973137438459437056
JJ_TRIGGER = "ㄐㄐ"
ELECTRIC_TRIGGER = "電"
ELECTRIC_EMOJI = "⚡"


class special_reaction(Cog):
    def __init__(self, bot: Bot):
        self.bot: Bot = bot

    @Cog.listener("on_message")
    async def on_message(self, message: Message):
        if (
            message.author.id == JJ_USER_ID
            and JJ_TRIGGER in message.content
            and not self.bot.is_ws_ratelimited()
        ):
            ch = self.bot.get_channel(JJ_CHANNEL_ID)
            if isinstance(ch, VoiceChannel):
                create_task(
                    ch.edit(
                        name=f'ㄐㄐ女王有{int(ch.name[5:-3])+message.content.count(JJ_TRIGGER)}根ㄐㄐ'
                    )
                )

        if ELECTRIC_TRIGGER in message.content:
            try:
                await message.add_reaction(ELECTRIC_EMOJI)
            except Exception:
                pass

    @Cog.listener("on_reaction_add")
    async def reaction_add(self, reaction: Reaction, user: User):
        if user.bot:
            return
        try:
            match reaction.emoji:
                case "🐔" if reaction.message.author.id == JJ_USER_ID:
                    await reaction.remove(user)
                    emoji = [
                        "0️⃣",
                        "1️⃣",
                        "2️⃣",
                        "3️⃣",
                        "4️⃣",
                        "5️⃣",
                        "6️⃣",
                        "7️⃣",
                        "8️⃣",
                        "9️⃣",
                    ]
                    for i in reaction.message.reactions:
                        if i.emoji in emoji:
                            return
                    chicken_channel = self.bot.get_channel(JJ_CHANNEL_ID)
                    if isinstance(chicken_channel, GuildChannel):
                        chicken_count = int(chicken_channel.name[5:-3])
                        chicken_str = str(chicken_count)
                        chicken_set = {*chicken_str}
                        if len(chicken_str) != len(chicken_set):
                            return
                        for i in chicken_str:
                            await reaction.message.add_reaction(emoji[int(i)])
        except Exception as e:
            logger.exception("special_reaction 錯誤: %s", e)


def setup(bot: Bot):
    bot.add_cog(special_reaction(bot))
