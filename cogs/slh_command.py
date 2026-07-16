from discord import (
    ApplicationContext,
    AutocompleteContext,
    Embed,
    Member,
    VoiceRegion,
    Bot,
    User,
    VoiceChannel,
    option,
    slash_command,
)
from discord.ext.commands import Cog
from core.config import runtime

SNOWBALL_GUILD_ID = 624590181298601985
SNOWBALL_CHANNEL_ID = 883718467562401812


class slh_command(Cog):
    def __init__(self, bot: Bot) -> None:
        self.bot: Bot = bot

    @slash_command(
        name="snowball",
        description="立訓又吃到雪球了😭",
        guild_ids=[SNOWBALL_GUILD_ID],
    )
    async def snowBall(self, ctx: ApplicationContext, cnt: int = 1):
        channel: VoiceChannel = self.bot.get_channel(SNOWBALL_CHANNEL_ID)  # type: ignore
        rename = f"立訓吃了{int(channel.name[4:-3]) + cnt}顆雪球"
        await channel.edit(name=rename)
        await ctx.respond(f"立訓這次吃了{cnt}顆雪球", ephemeral=True)

    @slash_command(name="head", description="頭像")
    @option(name="user", type=User | Member, description="要取頭像的人")
    async def avatar(self, ctx: ApplicationContext, user: User | Member):
        embed = Embed()
        embed.set_image(url=user.avatar)
        embed.add_field(
            name=user.name,
            value=user.nick if isinstance(user, Member) and user.nick else "沒有暱稱",
        )
        await ctx.respond(embed=embed, ephemeral=True)

    async def list_other_region(self, ctx: AutocompleteContext) -> list[str]:
        if not ctx.interaction.user:
            return []
        if not isinstance(ctx.interaction.user, Member):
            return []
        user = ctx.interaction.user
        if not user.voice:
            return []
        if not user.voice.channel:
            return []
        targetChannel = user.voice.channel
        current_region = targetChannel.rtc_region
        other_regions = [
            region.value for region in VoiceRegion if region != current_region
        ]
        if ctx.value == "":
            return other_regions
        filtered_regions = filter(
            lambda name: name.startswith(ctx.value), other_regions
        )
        return list(filtered_regions)

    @slash_command(name="region", description="更換語音地區")
    @option(name="region", type=str, description="地區", autocomplete=list_other_region)
    async def region(self, ctx: ApplicationContext, region: str):
        if not ctx.interaction.user:
            return
        if not isinstance(ctx.interaction.user, Member):
            return
        user = ctx.interaction.user
        if not user.voice:
            return
        if not user.voice.channel:
            return
        targetChannel = user.voice.channel
        await targetChannel.edit(
            rtc_region=VoiceRegion(region),
            reason=f"由 {ctx.interaction.user.display_name} 指定",
        )
        runtime.last_region = region
        await ctx.respond(f"已將語音頻道地區更改為 {region}", ephemeral=True)


def setup(bot: Bot):
    bot.add_cog(slh_command(bot))
