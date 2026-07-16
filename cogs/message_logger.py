from asyncio import create_task, gather
from os import getenv
from discord import (
    AllowedMentions,
    Bot,
    Message,
    RawMessageDeleteEvent,
    RawMessageUpdateEvent,
    Webhook,
)
from core.shared import get_client
from aiohttp import ClientSession
from discord.ext.commands import Cog

IGNORED_CHANNEL_IDS = [1099435386113105992]
DEFAULT_NAME = "某人"
DEFAULT_AVATAR_URL = "https://www.siasat.com/wp-content/uploads/2021/05/Discord.jpg"


class message_logger(Cog):
    def __init__(self, bot: Bot):
        self.bot: Bot = bot
        self.session: ClientSession
        self.webhook: Webhook
        create_task(self.initial_variable())

    async def initial_variable(self):
        self.session = await get_client()
        self.webhook = Webhook.from_url(
            getenv("TEXT_WEBHOOK", ""), session=self.session
        )

    @Cog.listener("on_message")
    async def on_message(self, message: Message):
        if message.author.bot:
            return
        if message.channel.id in IGNORED_CHANNEL_IDS:
            return
        if message.guild:
            location = f"{message.guild.name}的<#{message.channel.id}>"
        else:
            location = "DM"

        avatar = message.author.display_avatar.url
        name = message.author.display_name

        msg = f"{message.jump_url}\n{message.author.mention}在{location}說了\n"
        msg += message.content
        conv_to_file = [i.to_file(spoiler=i.is_spoiler()) for i in message.attachments]
        attachment = await gather(*conv_to_file)

        await self.webhook.send(
            msg,
            embeds=message.embeds,
            files=attachment,
            username=name,
            avatar_url=avatar,
            allowed_mentions=AllowedMentions.none(),
        )

    @Cog.listener("on_raw_message_delete")
    async def on_raw_message_delete(self, payload: RawMessageDeleteEvent):
        if payload.channel_id in IGNORED_CHANNEL_IDS:
            return
        message = payload.cached_message
        if not message:
            if payload.guild_id:
                location = f"{self.bot.get_guild(payload.guild_id)}的<#{payload.channel_id}>"
            else:
                location = "DM"
            msg = f"https://discord.com/channels/{payload.guild_id if payload.guild_id else '@me'}/{payload.channel_id}/{payload.message_id}\n"
            msg += f"{DEFAULT_NAME}刪除了在{location}的訊息"
            embeds = []
            name = DEFAULT_NAME
            avatar = DEFAULT_AVATAR_URL
        else:
            if message.author.bot:
                return
            if message.guild:
                location = f"{message.guild.name}的<#{message.channel.id}>"
            else:
                location = "DM"

            avatar = message.author.display_avatar.url
            name = message.author.display_name

            msg = message.jump_url
            msg += f"\n{message.author.mention}刪除在{location}的訊息\n"
            msg += message.content
            embeds = message.embeds

        await self.webhook.send(
            msg,
            embeds=embeds,
            username=name,
            avatar_url=avatar,
            allowed_mentions=AllowedMentions.none(),
        )

    @Cog.listener("on_raw_message_edit")
    async def on_raw_message_edit(self, payload: RawMessageUpdateEvent):
        if payload.channel_id in IGNORED_CHANNEL_IDS:
            return
        message = self.bot.get_message(payload.message_id)
        if not message:
            if payload.guild_id:
                location = f"{self.bot.get_guild(payload.guild_id)}的<#{payload.channel_id}>"
            else:
                location = "DM"
            msg = f"https://discord.com/channels/{payload.guild_id if payload.guild_id else '@me'}/{payload.channel_id}/{payload.message_id}\n"
            msg += f"{DEFAULT_NAME}編輯了在{location}的訊息"
            embeds = []
            attachment = []
            name = DEFAULT_NAME
            avatar = DEFAULT_AVATAR_URL
        else:
            if message.author.bot:
                return
            if message.guild:
                location = f"{message.guild.name}的<#{message.channel.id}>"
            else:
                location = "DM"

            avatar = message.author.display_avatar.url
            name = message.author.display_name

            msg = message.jump_url
            msg += f"\n{message.author.mention}編輯了在{location}的訊息\n"
            msg += message.content
            conv_to_file = [
                i.to_file(spoiler=i.is_spoiler()) for i in message.attachments
            ]
            attachment = await gather(*conv_to_file)
            embeds = message.embeds

        await self.webhook.send(
            msg,
            embeds=embeds,
            files=attachment,
            username=name,
            avatar_url=avatar,
            allowed_mentions=AllowedMentions.none(),
        )


def setup(bot: Bot):
    bot.add_cog(message_logger(bot))


def teardown(bot: Bot):
    instance: message_logger = bot.get_cog("message_logger")  # type: ignore
    create_task(instance.session.close())
