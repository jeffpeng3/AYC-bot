from discord import (
    ApplicationContext,
    Embed,
    Member,
    Bot,
    User,
    VoiceChannel,
    option,
    slash_command,
    InteractionContextType
)
from discord.ext.commands import Cog


class slh_command(Cog):
    def __init__(self, bot: Bot) -> None:
        self.bot: Bot = bot

    @slash_command(
        name="snowball",
        description="立訓又吃到雪球了😭",
        guild_ids=[624590181298601985],
        # contexts=InteractionContextType.guild,
    )
    async def snowBall(self, ctx: ApplicationContext, cnt: int = 1):
        channel: VoiceChannel = self.bot.get_channel(883718467562401812)  # type: ignore
        rename = f"立訓吃了{int(channel.name[4:-3])+cnt}顆雪球"
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

        


def setup(bot: Bot):
    bot.add_cog(slh_command(bot))
