from os import getenv, listdir
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
    InteractionContextType
)
from asyncio import Event
from discord import Bot as _Bot
# import mafic


def command_prefix(bot: _Bot | AutoShardedBot, msg: Message) -> list[str]:
    return ["-"]


class Bot(_Bot):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # self.pool = mafic.NodePool(self)


bot = Bot(
    command_prefix=command_prefix,
    help_command=None,
    case_insensitive=True,
    intents=Intents.all(),
    owner_id=551024169442344970,
    auto_sync_commands=False,
)

init_once = Event()

@bot.event
async def on_ready():
    if init_once.is_set():
        return
    print("-------------")
    if bot.user:
        print("Logged in as :")
        print(bot.user.name)
        print(bot.user.id)
        print("-------------")
    # await bot.pool.create_node(
    #     host="127.0.0.1",
    #     port=2333,
    #     label="MAIN",
    #     password="yao_dcbot",
    # )
    # print(f"connect to node {bot.pool.nodes}")
    # print("-------------")
    for filename in listdir("cogs"):
        if filename.endswith(".py"):
            print(f"loading {filename} ...")
            bot.load_extension(f"cogs.{filename[:-3]}")
            print(f"load {filename} done")
    await bot.sync_commands()
    print("-------------")
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
    guild_ids=[879748390290853918],
    # contexts=InteractionContextType.guild,
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
    guild_ids=[879748390290853918],
    # contexts=InteractionContextType.guild,
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
    guild_ids=[879748390290853918],
    # contexts=InteractionContextType.guild,
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
    guild_ids=[879748390290853918],
    # contexts=InteractionContextType.guild,
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
    if token:
        bot.run(token)
    else:
        raise ValueError("token not found.")
