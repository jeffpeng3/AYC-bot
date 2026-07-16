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

    async def _handle_chicken_reaction(self, reaction: Reaction, user: User) -> None:
        await reaction.remove(user)
        digit_emoji = [
            "0️⃣", "1️⃣", "2️⃣", "3️⃣", "4️⃣",
            "5️⃣", "6️⃣", "7️⃣", "8️⃣", "9️⃣",
        ]
        for i in reaction.message.reactions:
            if i.emoji in digit_emoji:
                return
        channel = self.bot.get_channel(JJ_CHANNEL_ID)
        if not isinstance(channel, GuildChannel):
            return
        count = int(channel.name[5:-3])
        digits = str(count)
        if len(set(digits)) != len(digits):
            return
        for d in digits:
            await reaction.message.add_reaction(digit_emoji[int(d)])

    @Cog.listener("on_reaction_add")
    async def reaction_add(self, reaction: Reaction, user: User):
        if user.bot:
            return
        try:
            match reaction.emoji:
                case "🐔" if reaction.message.author.id == JJ_USER_ID:
                    await self._handle_chicken_reaction(reaction, user)
        except Exception as e:
            logger.exception("special_reaction 錯誤: %s", e)


def setup(bot: Bot):
    bot.add_cog(special_reaction(bot))
