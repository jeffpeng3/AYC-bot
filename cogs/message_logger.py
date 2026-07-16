from asyncio import create_task, gather
from discord import (
    AllowedMentions,
    Bot,
    Guild,
    Message,
    RawMessageDeleteEvent,
    RawMessageUpdateEvent,
)
from discord.ext.commands import Cog
from core.webhook_logger import WebhookLogger

IGNORED_CHANNEL_IDS = [1099435386113105992]
DEFAULT_NAME = "某人"
DEFAULT_AVATAR_URL = "https://www.siasat.com/wp-content/uploads/2021/05/Discord.jpg"


class message_logger(WebhookLogger):
    def __init__(self, bot: Bot):
        super().__init__(bot, "TEXT_WEBHOOK")

    @staticmethod
    def _message_url(guild_id: int | None, channel_id: int, message_id: int) -> str:
        gid = guild_id if guild_id else "@me"
        return f"https://discord.com/channels/{gid}/{channel_id}/{message_id}"

    def _format_location(self, guild_id: int | None, channel_id: int) -> str:
        if guild_id:
            guild = self.bot.get_guild(guild_id)
            name = guild.name if guild else str(guild_id)
            return f"{name}的<#{channel_id}>"
        return "DM"

    @Cog.listener("on_message")
    async def on_message(self, message: Message):
        if message.author.bot:
            return
        if message.channel.id in IGNORED_CHANNEL_IDS:
            return
        location = self._format_location(
            message.guild.id if message.guild else None, message.channel.id
        )

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
            location = self._format_location(payload.guild_id, payload.channel_id)
            msg = f"{self._message_url(payload.guild_id, payload.channel_id, payload.message_id)}\n"
            msg += f"{DEFAULT_NAME}刪除了在{location}的訊息"
            embeds = []
            name = DEFAULT_NAME
            avatar = DEFAULT_AVATAR_URL
        else:
            if message.author.bot:
                return
            location = self._format_location(
                message.guild.id if message.guild else None, message.channel.id
            )

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
            location = self._format_location(payload.guild_id, payload.channel_id)
            msg = f"{self._message_url(payload.guild_id, payload.channel_id, payload.message_id)}\n"
            msg += f"{DEFAULT_NAME}編輯了在{location}的訊息"
            embeds = []
            attachment = []
            name = DEFAULT_NAME
            avatar = DEFAULT_AVATAR_URL
        else:
            if message.author.bot:
                return
            location = self._format_location(
                message.guild.id if message.guild else None, message.channel.id
            )

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
