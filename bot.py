import logging
from os import getenv, listdir

logger = logging.getLogger(__name__)
logging.getLogger("discord").setLevel(logging.WARNING)
logging.basicConfig(
    level=getenv("LOG_LEVEL", "INFO").upper(),
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
from discord.ext.commands import is_owner
from discord.commands import option
from discord import (
    ApplicationContext,
    Intents,
    Message,
    AutoShardedBot,
    AutocompleteContext,
    User,
    default_permissions,
)
from asyncio import Event, new_event_loop
from discord import Bot

from core.shared import close_client

OWNER_ID = 551024169442344970
GUILD_ID = 879748390290853918


def command_prefix(_bot: Bot | AutoShardedBot, _msg: Message) -> list[str]:
    return ["-"]


bot = Bot(
    command_prefix=command_prefix,
    help_command=None,
    case_insensitive=True,
    intents=Intents.all(),
    owner_id=OWNER_ID,
    auto_sync_commands=False,
)

init_once = Event()

@bot.event
async def on_ready():
    if init_once.is_set():
        return
    logger.info("-------------")
    if bot.user:
        logger.info("Logged in as : %s (%s)", bot.user.name, bot.user.id)
        logger.info("-------------")
    for filename in listdir("cogs"):
        if filename.endswith(".py"):
            logger.info("loading %s ...", filename)
            try:
                bot.load_extension(f"cogs.{filename[:-3]}")
                logger.info("load %s done", filename)
            except Exception as e:
                logger.error("Failed to load %s: %s", filename, e)
    await bot.sync_commands()
    logger.info("-------------")
    init_once.set()


async def list_not_loaded_cog(ctx: AutocompleteContext) -> list[str]:
    if not ctx.interaction.user:
        return []
    user = (
        ctx.interaction.user
        if isinstance(ctx.interaction.user, User)
        else ctx.interaction.user._user
    )
    if not await bot.is_owner(user):
        return []
    all_cog_list_with_extension = filter(
        lambda name: name.endswith(".py"), listdir("cogs")
    )
    all_cog_list = map(lambda name: name[:-3], all_cog_list_with_extension)
    loaded_cog_list = bot.cogs.keys()
    not_loaded_cog_list = list(set(all_cog_list) - set(loaded_cog_list))

    what_we_may_want = filter(
        lambda name: name.startswith(ctx.value), not_loaded_cog_list
    )
    return list(what_we_may_want)


async def list_loaded_cog(ctx: AutocompleteContext) -> list[str]:
    if not ctx.interaction.user:
        return []
    user = (
        ctx.interaction.user
        if isinstance(ctx.interaction.user, User)
        else ctx.interaction.user._user
    )
    if not await bot.is_owner(user):
        return []
    cog_list = bot.cogs.keys()
    what_we_may_want = filter(lambda name: name.startswith(ctx.value), cog_list)
    return list(what_we_may_want)


@bot.slash_command(
    name="load",
    guild_ids=[GUILD_ID],
    description="載入模組",
)
@option(
    name="extension",
    type=str,
    description="選擇想要載入的模組",
    autocomplete=list_not_loaded_cog,
)
@default_permissions(administrator=True)
@is_owner()
async def load(ctx: ApplicationContext, extension: str):
    bot.load_extension(f"cogs.{extension}")
    await ctx.defer(ephemeral=True)
    await ctx.respond(f"load {extension} done.", ephemeral=True)


@bot.slash_command(
    name="sync",
    guild_ids=[GUILD_ID],
    description="同步指令",
)
@default_permissions(administrator=True)
@is_owner()
async def sync(ctx: ApplicationContext):
    await ctx.defer(ephemeral=True)
    await bot.sync_commands()
    await ctx.respond("command sync done.", ephemeral=True)


@bot.slash_command(
    name="unload",
    guild_ids=[GUILD_ID],
    description="卸載模組",
)
@option(
    name="extension",
    type=str,
    description="選擇想要卸載的模組",
    autocomplete=list_loaded_cog,
)
@default_permissions(administrator=True)
@is_owner()
async def unload(ctx: ApplicationContext, extension: str):
    bot.unload_extension(f"cogs.{extension}")
    await ctx.defer(ephemeral=True)
    await ctx.respond(f"unload {extension} done.", ephemeral=True)


@bot.slash_command(
    name="reload",
    guild_ids=[GUILD_ID],
    description="重新載入模組",
)
@option(
    name="extension",
    type=str,
    description="選擇想要重新載入的模組",
    autocomplete=list_loaded_cog,
)
@default_permissions(administrator=True)
@is_owner()
async def reload(ctx: ApplicationContext, extension: str):
    bot.reload_extension(f"cogs.{extension}")
    await ctx.defer(ephemeral=True)
    await ctx.respond(f"reload {extension} done.", ephemeral=True)

if __name__ == "__main__":

    init_once.clear()
    token = getenv("DISCORD_TOKEN")
    try:
        if token:
            bot.run(token)
        else:
            raise ValueError("token not found.")
    finally:
        new_event_loop().run_until_complete(close_client())