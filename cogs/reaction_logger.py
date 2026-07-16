import logging
from asyncio import create_task
from discord import (
    AllowedMentions,
    Bot,
    RawReactionActionEvent,
)
from discord.ext.commands import Cog
from core.webhook_logger import WebhookLogger

logger = logging.getLogger(__name__)


class reaction_logger(WebhookLogger):
    def __init__(self, bot: Bot):
        super().__init__(bot, "REACTION_WEBHOOK")

    @Cog.listener("on_raw_reaction_add")
    async def on_raw_reaction_add(self, payload: RawReactionActionEvent):
        user = await self.bot.get_or_fetch_user(payload.user_id)
        if not user:
            logger.warning("無法獲取user: %s", payload.user_id)
            return
        if user.bot:
            return
        if payload.guild_id:
            location = f"{self.bot.get_guild(payload.guild_id)}的<#{payload.channel_id}>"
        else:
            location = f"<#{payload.channel_id}>"

        avatar = (
            payload.member.display_avatar.url
            if payload.member
            else user.display_avatar.url
        )
        name = payload.member.display_name if payload.member else user.display_name
        message_url = "https://discord.com/channels/"
        message_url += f"{payload.guild_id if payload.guild_id else '@me'}"
        message_url += f"/{payload.channel_id}/{payload.message_id}"
        message = message_url
        message += f"\n<@{payload.user_id}>在{location}點了\n"
        message += (
            f"{payload.emoji.url if payload.emoji.is_custom_emoji() else payload.emoji}"
        )

        await self.webhook.send(
            message,
            username=name,
            avatar_url=avatar,
            allowed_mentions=AllowedMentions.none(),
        )

    @Cog.listener("on_raw_reaction_remove")
    async def on_raw_reaction_remove(self, payload: RawReactionActionEvent):
        user = await self.bot.get_or_fetch_user(payload.user_id)
        if not user:
            logger.warning("無法獲取user: %s", payload.user_id)
            return
        if user.bot:
            return
        if payload.guild_id:
            location = f"{self.bot.get_guild(payload.guild_id)}的<#{payload.channel_id}>"
        else:
            location = f"<@{payload.channel_id}>"

        avatar = (
            payload.member.display_avatar.url
            if payload.member
            else user.display_avatar.url
        )
        name = payload.member.display_name if payload.member else user.display_name
        message_url = "https://discord.com/channels/"
        message_url += f"{payload.guild_id if payload.guild_id else '@me'}"
        message_url += f"/{payload.channel_id}/{payload.message_id}"
        message = message_url
        message += f"\n<@{payload.user_id}>在{location}收回了\n"
        message += (
            f"{payload.emoji.url if payload.emoji.is_custom_emoji() else payload.emoji}"
        )

        await self.webhook.send(
            message,
            username=name,
            avatar_url=avatar,
            allowed_mentions=AllowedMentions.none(),
        )


def setup(bot: Bot):
    bot.add_cog(reaction_logger(bot))


def teardown(bot: Bot):
    instance: reaction_logger = bot.get_cog("reaction_logger")  # type: ignore
    create_task(instance.session.close())
