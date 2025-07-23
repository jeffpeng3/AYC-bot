from asyncio import create_task
from os import getenv
from discord import (
    AllowedMentions,
    Bot,
    Member,
    VoiceState,
    Webhook,
)
from core.shared import get_client
from aiohttp import ClientSession
from discord.ext.commands import Cog


class voice_logger(Cog):
    def __init__(self, bot: Bot):
        self.bot: Bot = bot
        self.session: ClientSession
        self.webhook: Webhook
        create_task(self.initial_variable())

    async def initial_variable(self):
        self.session = await get_client()
        self.webhook = Webhook.from_url(
            getenv("VOICE_WEBHOOK", ""), session=self.session
        )

    @Cog.listener("on_voice_state_update")
    async def on_voice_state_update(
        self, member: Member, before: VoiceState, after: VoiceState
    ):
        message = member.mention
        if not after.channel:
            if before.channel:
                message += f'離開了 {before.channel.name}'
            else:
                print('為啥這個不成立阿',before,after)
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
        avatar = (
            member.avatar.url
            if member.avatar
            else "https://www.siasat.com/wp-content/uploads/2021/05/Discord.jpg"
        )
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