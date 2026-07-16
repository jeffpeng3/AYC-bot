from discord import (
    ApplicationContext,
    Embed,
    Bot,
    option,
    OptionChoice,
    slash_command,
)
from discord.ext.commands import Cog
from cloudflare import AsyncCloudflare
from cloudflare.types.dns.record_create_params import SRVRecordData
from os import getenv

GUILD_ID = 624590181298601985
PORT_MIN = 20000
PORT_MAX = 30000
TTL = 1
COLOR_PENDING = 0xFFFF00
COLOR_SUCCESS = 0x00FF00
COLOR_ERROR = 0xFF0000

class cf_command(Cog):
    def __init__(self, bot: Bot) -> None:
        self.bot: Bot = bot
        self.cf = AsyncCloudflare()
        self.domain = getenv("DOMAIN", "")

    @slash_command(name="add_record", description="新增DNS紀錄", guild_ids=[GUILD_ID])
    @option(name="service_type", type=str, choices=[OptionChoice("minecraft", "_minecraft")])
    @option(name="name", type=str, description="名稱, <name>.<domain>")
    @option(name="port", type=int, description="port", min_value=PORT_MIN, max_value=PORT_MAX)
    async def addRecord(self, ctx: ApplicationContext, service_type: str, name: str, port: int):
        srv_name = f"{service_type}._tcp.{name}.sub"
        embed = Embed(title="正在新增DNS紀錄...", description=f"網域: {name}.sub.{self.domain}\n指向: sub.{self.domain}:{port}", color=COLOR_PENDING)
        await ctx.respond(embed=embed)

        try:
            zones = await self.cf.zones.list(name=self.domain)
            if len(zones.result) == 0:
                raise Exception(f"找不到網域 {self.domain}")
            zone_id = zones.result[0].id
            dest_ip = f"sub.{self.domain}"
            data = SRVRecordData(
                priority=0,
                weight=0,
                port=int(port),
                target=dest_ip,
            )
            await self.cf.dns.records.create(
                zone_id=zone_id, type="SRV", name=srv_name, data=data, ttl=TTL
            )
            embed = Embed(title="新增DNS紀錄成功", description=f"網域: {name}.sub.{self.domain}\n指向: sub.{self.domain}:{port}", color=COLOR_SUCCESS)

        except Exception as e:
            embed = Embed(title="新增DNS紀錄失敗", description=f"網域: {name}.sub.{self.domain}\n指向: sub.{self.domain}:{port}\n錯誤訊息: {e}", color=COLOR_ERROR)
        await ctx.edit(embed=embed)


def setup(bot: Bot):
    bot.add_cog(cf_command(bot))
