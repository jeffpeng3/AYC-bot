from discord import (
    Thread,
    Bot,
)
from discord.ext.commands import Cog

class thread_about(Cog):
    def __init__(self, bot: Bot):
        self.bot: Bot = bot

    @Cog.listener("on_thread_create")
    async def on_thread_create(self, thread : Thread) -> None:
        await thread.join()

def setup(bot: Bot):
    bot.add_cog(thread_about(bot))
