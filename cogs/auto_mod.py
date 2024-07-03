from discord import (
    Member,
    Bot,
    VoiceState,
    VoiceRegion
)
from discord.ext.commands import Cog
from time import time_ns
from os import getenv

class auto_mod(Cog):
    def __init__(self, bot: Bot):
        self.bot: Bot = bot
        self.entry_point = int(getenv("ENTRY_POINT",'0'))

    @Cog.listener("on_voice_state_update")
    async def on_voice(self, member: Member, before:VoiceState, after:VoiceState):
        s = "↑↓←→"
        entry_point = self.entry_point
        if entry_point == 0:
            return
        if after.channel and after.channel.id == entry_point:
            code = time_ns() + member.id
            code = bin(code)[2:][-16:]
            name = ''
            for i in range(4):
                name += s[int(code[i*2:2*(i+1)],2)]
            new_channel = await after.channel.clone(name=f"分流{name}",reason="分流")
            await new_channel.edit(rtc_region=VoiceRegion.japan)
            await member.move_to(new_channel)

        if before.channel:
            if before.channel.id == entry_point:
                return
            if member.guild.afk_channel and member.guild.afk_channel.id == before.channel.id:  # noqa: E501
                return
            if before.channel.members:
                return
            if not before.channel.name.startswith("分流"):
                return
            if [*filter(lambda x:x not in s,before.channel.name[2:])]:
                return
            await before.channel.delete(reason="分流")


def setup(bot: Bot):
    bot.add_cog(auto_mod(bot))
