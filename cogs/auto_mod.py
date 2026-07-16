from discord import Member, Bot, VoiceState, VoiceRegion
from discord.ext.commands import Cog
from time import time_ns
from core.config import runtime

ENTRY_CHANNEL_ID = 1153635272840458270
VOICE_NAME_PREFIX = "分流"
VOICE_CHARS = "↑↓←→"


class auto_mod(Cog):
    def __init__(self, bot: Bot):
        self.bot: Bot = bot

    @Cog.listener("on_voice_state_update")
    async def on_voice(self, member: Member, before: VoiceState, after: VoiceState):
        if after.channel and after.channel.id == ENTRY_CHANNEL_ID:
            code = time_ns() + member.id
            code = bin(code)[2:][-16:]
            name = ""
            for i in range(4):
                name += VOICE_CHARS[int(code[i * 2 : 2 * (i + 1)], 2)]
            new_channel = await after.channel.clone(name=f"{VOICE_NAME_PREFIX}{name}", reason="分流")
            await new_channel.edit(rtc_region=VoiceRegion(runtime.last_region), nsfw=True)
            await member.move_to(new_channel)

        if before.channel:
            if before.channel.id == ENTRY_CHANNEL_ID:
                return
            if (
                member.guild.afk_channel
                and member.guild.afk_channel.id == before.channel.id
            ):
                return
            if before.channel.members:
                return
            if not before.channel.name.startswith(VOICE_NAME_PREFIX):
                return
            if [*filter(lambda x: x not in VOICE_CHARS, before.channel.name[len(VOICE_NAME_PREFIX):])]:
                return
            await before.channel.delete(reason="分流")


def setup(bot: Bot):
    bot.add_cog(auto_mod(bot))
