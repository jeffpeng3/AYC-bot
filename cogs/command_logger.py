from asyncio import create_task
from os import getenv
from discord import (
    AllowedMentions,
    ApplicationContext,
    Bot,
    DMChannel,
    MessageCommand,
    SlashCommand,
    UserCommand,
    Webhook,
)
from discord.abc import GuildChannel
from aiohttp import ClientSession
from discord.ext.commands import Cog


class command_logger(Cog):
    def __init__(self, bot: Bot):
        self.bot: Bot = bot
        self.session: ClientSession
        self.webhook: Webhook
        create_task(self.initial_variable())

    async def initial_variable(self):
        self.session = ClientSession()
        self.webhook = Webhook.from_url(
            getenv("COMMAND_WEBHOOK", ""), session=self.session
        )

    @Cog.listener("on_application_command")
    async def on_application_command(self, ctx: ApplicationContext):
        author = ctx.author
        if not ctx.channel:
            return
        if isinstance(ctx.channel,DMChannel):
            location = 'DM'
        elif ctx.guild and isinstance(ctx.channel,GuildChannel):
            location = f"{ctx.guild.name}的{ctx.channel.mention}"
        else:
            location = ctx.channel
        avatar = author.display_avatar.url
        name = author.display_name
        mention = author.mention
        message = f"{mention}在{location}\n"
        message += f"/{ctx.command.qualified_name}"
        # print(ctx.interaction.data)
        if isinstance(ctx.command,SlashCommand):
            if ctx.selected_options:
                for options in ctx.selected_options:
                    message += f" {options['name']}:{options['value']}"
        elif isinstance(ctx.command,MessageCommand):
            data:dict = ctx.interaction.data # type: ignore
            url = f"https://discord.com/channels/{ctx.guild.id if ctx.guild else '@me'}"
            url += f"/{ctx.channel_id}/{data['target_id']}"
            message += f" message:{data['target_id']}({url})"
        if isinstance(ctx.command,UserCommand):
            data:dict = ctx.interaction.data # type: ignore
            message += f" user:{data['target_id']}(<@{data['target_id']}>)"
        await self.webhook.send(
            message,
            username=name,
            avatar_url=avatar,
            allowed_mentions=AllowedMentions.none(),
        )

def setup(bot: Bot):
    bot.add_cog(command_logger(bot))

def teardown(bot: Bot):
    instance: command_logger = bot.get_cog("command_logger")  # type: ignore
    create_task(instance.session.close())