from asyncio import create_task
from discord import (
    AllowedMentions,
    Bot,
    Member,
    VoiceState,
)
from discord.ext.commands import Cog
from core.webhook_logger import WebhookLogger

DEFAULT_AVATAR_URL = "https://www.siasat.com/wp-content/uploads/2021/05/Discord.jpg"


class voice_logger(WebhookLogger):
    def __init__(self, bot: Bot):
        super().__init__(bot, "VOICE_WEBHOOK")

    @Cog.listener("on_voice_state_update")
    async def on_voice_state_update(
        self, member: Member, before: VoiceState, after: VoiceState
    ):
        message = member.mention
        if not after.channel:
            if before.channel:
                message += f'離開了 {before.channel.name}'
            else:
                print('為啥這個不成立阿', before, after)
                return
        elif not before.channel:
            message += f'加入了 {after.channel.name}'
        elif after.afk:
            message += f'從 {before.channel.name} 跑去AFK了'
        elif before.channel.id != after.channel.id:
            message += f'從 {before.channel.name} 跑去 {after.channel.name} 了'
        elif before.mute != after.mute:
            if after.mute:
                message += '被伺服端靜音了'
            else:
                message += '解除伺服端靜音了'
        elif before.deaf != after.deaf:
            if after.deaf:
                message += '被伺服端拒聽了'
            else:
                message += '解除伺服端拒聽了'
        elif before.self_deaf != after.self_deaf:
            if after.self_deaf:
                message += '拒聽了'
            else:
                message += '解除拒聽了'
        elif before.self_mute != after.self_mute:
            if after.self_mute:
                message += '靜音了'
            else:
                message += '解除靜音了'
        elif before.self_stream != after.self_stream:
            if after.self_stream:
                message += '開始直播了'
            else:
                message += '停止直播了'
        else:
            message += "不知道怎麼了"

        name = member.display_name
        avatar = member.avatar.url if member.avatar else DEFAULT_AVATAR_URL
        await self.webhook.send(
            message,
            username=name,
            avatar_url=avatar,
            allowed_mentions=AllowedMentions.none(),
        )


def setup(bot: Bot):
    bot.add_cog(voice_logger(bot))

def teardown(bot: Bot):
    instance: voice_logger = bot.get_cog("voice_logger")  # type: ignore
    create_task(instance.session.close())