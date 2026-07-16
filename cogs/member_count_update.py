from discord import (
    Member,
    Bot,
    TextChannel,
)
from discord.ext.commands import Cog

GUILD_ID = 624590181298601985
CHANNEL_ID = 638016896272171008
NAME_TEMPLATE = "一一一{}人一一一"


class member_count_update(Cog):
    def __init__(self, bot: Bot):
        self.bot: Bot = bot

    @Cog.listener("on_member_join")
    async def on_member_join(self, member: Member):
        if member.guild.id == GUILD_ID:
            channel = self.bot.get_channel(CHANNEL_ID)
            if isinstance(channel, TextChannel):
                await channel.edit(name=NAME_TEMPLATE.format(member.guild.member_count))

    @Cog.listener("on_member_remove")
    async def on_member_remove(self, member: Member):
        if member.guild.id == GUILD_ID:
            channel = self.bot.get_channel(CHANNEL_ID)
            if isinstance(channel, TextChannel):
                await channel.edit(name=NAME_TEMPLATE.format(member.guild.member_count))

def setup(bot: Bot):
    bot.add_cog(member_count_update(bot))
