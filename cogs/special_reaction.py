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
class special_reaction(Cog):
    def __init__(self, bot: Bot):
        self.bot: Bot = bot

    @Cog.listener("on_message")
    async def on_message(self, message: Message):
        if (
            message.author.id == 594546616107663530
            and "ㄐㄐ" in message.content
            and not self.bot.is_ws_ratelimited()
        ):
            ch = self.bot.get_channel(973137438459437056)
            if isinstance(ch, VoiceChannel):
                create_task(
                    ch.edit(
                        name=f'ㄐㄐ女王有{int(ch.name[5:-3])+message.content.count("ㄐㄐ")}根ㄐㄐ'
                    )
                )

        if "電" in message.content:
            try:
                await message.add_reaction("⚡")
            except Exception:
                pass

    @Cog.listener("on_reaction_add")
    async def reaction_add(self, reaction: Reaction, user: User):
        if user.bot:
            return
        try:
            match reaction.emoji:
                case "🐔" if reaction.message.author.id == 594546616107663530:
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
                    chicken_channel = self.bot.get_channel(973137438459437056)
                    if isinstance(chicken_channel, GuildChannel):
                        chicken_count = int(chicken_channel.name[5:-3])
                        chicken_str = str(chicken_count)
                        chicken_set = {*chicken_str}
                        if len(chicken_str) != len(chicken_set):
                            return
                        for i in chicken_str:
                            await reaction.message.add_reaction(emoji[int(i)])
        except Exception as e:
            print(e)


def setup(bot: Bot):
    bot.add_cog(special_reaction(bot))
