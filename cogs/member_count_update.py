from discord import (
    Member,
    Bot,
    TextChannel,
)
from discord.ext.commands import Cog

class member_count_update(Cog):
    def __init__(self, bot: Bot):
        self.bot: Bot = bot

    @Cog.listener("on_member_join")
    async def on_member_join(self, member : Member):
        if member.guild.id == 624590181298601985:
            channel = self.bot.get_channel(638016896272171008)
            if isinstance(channel,TextChannel):
                await channel.edit(name=f'一一一{member.guild.member_count}人一一一')

    @Cog.listener("on_member_remove")
    async def on_member_remove(self, member : Member):
        if member.guild.id == 624590181298601985:
            channel = self.bot.get_channel(638016896272171008)
            if isinstance(channel,TextChannel):
                await channel.edit(name=f'一一一{member.guild.member_count}人一一一')

def setup(bot: Bot):
    bot.add_cog(member_count_update(bot))
