from asyncio import sleep
from discord import (
    ApplicationContext,
    Member,
    Bot,
    default_permissions,
    user_command,
    VoiceChannel,
)
from discord.ext.commands import Cog, has_guild_permissions


class usr_command(Cog):
    def __init__(self, bot: Bot) -> None:
        self.bot: Bot = bot

    @user_command(name="mute")
    @default_permissions(mute_members=True)
    @has_guild_permissions(mute_members=True)
    async def mute(self, ctx: ApplicationContext, member: Member):
        await member.edit(mute=True)
        await ctx.author.send("你得到了暫時的清靜")
        await sleep(10)
        await member.edit(mute=False)

    @user_command(name="gotcha")
    async def gotcha(self, ctx: ApplicationContext, member: Member):
        channel: VoiceChannel = self.bot.get_channel(1101866682470907944)  # type:ignore
        rename = f"收到了{int(channel.name[3:-5])+1}個檢舉回報"
        await channel.edit(name=rename)
        await ctx.respond("恭喜你檢舉成功", ephemeral=True)

    @user_command(name="steal")
    async def steal(self, ctx: ApplicationContext, member: Member):
        channel: VoiceChannel = self.bot.get_channel(1113137310880510093)  # type:ignore
        rename = f"有人搶了{int(channel.name[4:-3])+1}個五殺"
        await channel.edit(name=rename)
        await ctx.respond("太難過ㄌ", ephemeral=True)

# Todo:
#   娛樂型檢舉系統

def setup(bot: Bot):
    bot.add_cog(usr_command(bot))
