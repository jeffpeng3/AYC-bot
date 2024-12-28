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

class cf_command(Cog):
    def __init__(self, bot: Bot) -> None:
        self.bot: Bot = bot
        self.cf = AsyncCloudflare()
        self.domain = getenv("DOMAIN")

    @slash_command(name="add_record", description="新增DNS紀錄",guild_ids=[624590181298601985])
    @option(name="service_type", type=str, choices=[OptionChoice("minecraft", "_minecraft")])
    @option(name="name", type=str, description="名稱, <name>.<domain>")
    @option(name="port", type=int, description="port", min_value=20000, max_value=30000)
    async def addRecord(self, ctx: ApplicationContext, service_type: str, name: str, port: int):
        srv_name = f"{service_type}._tcp.{name}.sub"
        embed = Embed(title="正在新增DNS紀錄...", description=f"網域: {name}.sub.{self.domain}\n指向: sub.{self.domain}:{port}", color=0xFFFF00)
        await ctx.respond(embed=embed)

        try:
            zones = await self.cf.zones.list(name=self.domain)
            print(zones.result[0].id)
            if len(zones.result) == 0:
                print(f"找不到網域 {self.domain}")
                return False
            zone_id = zones.result[0].id
            dest_ip = f"sub.{self.domain}"
            data = SRVRecordData(
                name=name,
                service=service_type,
                protocol="_tcp",
                priority=0,
                weight=0,
                port=int(port),
                target=dest_ip,
            )
            await self.cf.dns.records.create(
                zone_id=zone_id, type="SRV", name=srv_name, data=data, ttl=1
            )
            embed = Embed(title="新增DNS紀錄成功", description=f"網域: {name}.sub.{self.domain}\n指向: sub.{self.domain}:{port}", color=0x00FF00)

        except Exception as e:
            embed = Embed(title="新增DNS紀錄失敗", description=f"網域: {name}.sub.{self.domain}\n指向: sub.{self.domain}:{port}\n錯誤訊息: {e}",color=0xFF0000)
        await ctx.edit(embed=embed)


def setup(bot: Bot):
    bot.add_cog(cf_command(bot))
