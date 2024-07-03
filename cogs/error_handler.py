from discord import (
    ApplicationContext,
    DiscordException,
    Bot,
)
from discord.ext.commands import Cog
import traceback
class error_handler(Cog):
    def __init__(self, bot: Bot):
        self.bot: Bot = bot

    @Cog.listener("on_application_command_error")
    async def on_application_command_error(
        self, context: ApplicationContext, exception: DiscordException
    ) -> None:
        try:
            await context.respond(content=f"error : {exception}", ephemeral=True)
        except Exception as _:
            traceback.print_exc()

def setup(bot: Bot):
    bot.add_cog(error_handler(bot))
