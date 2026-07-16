import logging
from discord import (
    ApplicationContext,
    DiscordException,
    Bot,
)
from discord.ext.commands import Cog

logger = logging.getLogger(__name__)


class error_handler(Cog):
    def __init__(self, bot: Bot):
        self.bot: Bot = bot

    @Cog.listener("on_application_command_error")
    async def on_application_command_error(
        self, context: ApplicationContext, exception: DiscordException
    ) -> None:
        logger.error("Command error from %s: %s", context.author, exception)
        try:
            await context.respond(content=f"error : {exception}", ephemeral=True)
        except Exception:
            logger.exception("Failed to respond with error message")

def setup(bot: Bot):
    bot.add_cog(error_handler(bot))
