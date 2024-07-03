from discord import (
    ApplicationContext,
    Bot,
    slash_command,
    File,
    Webhook,
    AllowedMentions,
    VoiceChannel,
    ButtonStyle,
    Interaction,
    Message,
    TextChannel,
)
from discord.ui import View, button, Button
from discord.ext.commands import Cog
from aiohttp import ClientSession
from asyncio import create_task, Event, sleep
from os import listdir, getenv, path
from random import choice
from json import load, dump
from typing import Awaitable, Callable


def get_random_lewd() -> tuple[str, str]:
    dirs = listdir("/mnt/lewd/cache")
    subdir = choice(dirs)
    subdirs = listdir(f"/mnt/lewd/cache/{subdir}")
    subsubdir = choice(subdirs)
    subsubdirs = listdir(f"/mnt/lewd/cache/{subdir}/{subsubdir}")
    image = choice(subsubdirs)
    ext = image.split("-")[-1]
    return f"/mnt/lewd/cache/{subdir}/{subsubdir}/{image}", ext


class Lewd_Buttons(View):
    def __init__(
        self,
        ctx: ApplicationContext,
        lewd_logger: Callable[[ApplicationContext, str, str], Awaitable],
        counter: Callable[[str],None],
        update_event: Event,
    ) -> None:
        super().__init__(timeout=60)
        self.ctx = ctx
        self.lewd_logger = lewd_logger
        self.counter = counter
        self.update_event = update_event

    @button(style=ButtonStyle.gray, emoji="🔄", label="下面一位")
    async def retry(self, btn: Button, interaction: Interaction):
        await interaction.response.defer()
        if not isinstance(interaction.message, Message):
            return
        lewd_path, ext = get_random_lewd()
        with open(lewd_path, "rb") as f:
            lewd_image = File(f, f"lewds.{ext}")

        await interaction.edit_original_response(
            content="Hachi又四處翻找，找到了這張圖",
            file=lewd_image,
            attachments=[],
        )
        await self.lewd_logger(self.ctx, lewd_path, ext)
        self.counter(str(self.ctx.author.id))
        self.update_event.set()

    @button(style=ButtonStyle.red, emoji="🥵", label="不能只有我看到")
    async def share(self, btn: Button, interaction: Interaction):
        await interaction.response.defer()
        if not isinstance(interaction.message, Message):
            return
        message = interaction.message
        f = await message.attachments[0].to_file()
        if isinstance(btn.view, View):
            btn.view.disable_all_items()
            btn.view.stop()
        if not (channel := interaction.channel):
            return
        if not isinstance(channel, TextChannel):
            return
        if user := interaction.user:
            await channel.send(
                content=f"{user.mention}覺得不能只有他看到這個",
                file=f,
                allowed_mentions=AllowedMentions.none(),
            )
            await interaction.delete_original_response()
            return
        await channel.send("好像哪裡出錯了...")

    @button(style=ButtonStyle.red, emoji="🫣", label="偷偷分享一下")
    async def spoiler_share(self, btn: Button, interaction: Interaction):
        await interaction.response.defer()
        if not isinstance(interaction.message, Message):
            return
        message = interaction.message
        f = await message.attachments[0].to_file()
        f.filename = f"SPOILER_{f.filename}"
        if isinstance(btn.view, View):
            btn.view.disable_all_items()
            btn.view.stop()
        if not (channel := interaction.channel):
            return
        if not isinstance(channel, TextChannel):
            return
        if user := interaction.user:
            await channel.send(
                content=f"{user.mention}偷偷傳了這個出來",
                file=f,
                allowed_mentions=AllowedMentions.none(),

            )
            await interaction.delete_original_response()
            return
        await channel.send("好像哪裡出錯了...")

    # @button(style=ButtonStyle.red, emoji="🫣", label="偷偷分享一下")
    # async def spoiler_share(self, btn: Button, interaction: Interaction):
    #     await interaction.response.defer()
    #     if not isinstance(interaction.message, Message):
    #         return
    #     message = interaction.message
    #     f = await message.attachments[0].to_file()
    #     f.filename = f"SPOILER_{f.filename}"
    #     if isinstance(btn.view, View):
    #         btn.view.disable_all_items()
    #         btn.view.stop()
    #     if not (channel := interaction.channel):
    #         return
    #     if not isinstance(channel, TextChannel):
    #         return
    #     if user := interaction.user:
    #         await channel.send(
    #             content=f"{user.mention}偷偷傳了這個出來",
    #             file=f,
    #             allowed_mentions=AllowedMentions.none(),

    #         )
    #         await interaction.delete_original_response()
    #         return
    #     await channel.send("好像哪裡出錯了...")

class lewd(Cog):
    def __init__(self, bot: Bot) -> None:
        self.bot: Bot = bot
        self.session: ClientSession
        self.webhook: Webhook
        self.update_event = Event()
        with open("./data/lewd.json", "r", encoding="utf-8") as f:
            self.count: dict[str, int] = load(f)
        create_task(self.initial_variable())
        create_task(self.update_timer())

    async def update_timer(self):
        await self.bot.wait_until_ready()
        channel: VoiceChannel = self.bot.get_channel(1158445670911459449)  # type:ignore
        while 1:
            await self.update_event.wait()
            await sleep(300)
            rename = f"已經抽了{self.count['total']}張色圖"
            await channel.edit(name=rename)

    async def initial_variable(self):
        self.session = ClientSession()
        self.webhook = Webhook.from_url(
            getenv("LEWD_WEBHOOK", ""), session=self.session
        )

    async def lewd_logger(self, ctx: ApplicationContext, image_path: str, ext: str):
        with open(image_path, "rb") as f:
            lewd_log = File(f, f"lewds.{ext}")
        await self.webhook.send(
            content="我找到了這張圖",
            file=lewd_log,
            username=ctx.author.display_name,
            avatar_url=ctx.author.display_avatar.url,
            allowed_mentions=AllowedMentions.none(),
        )

    def counter(self, user_id: str):
        if not self.count.get(str(user_id)):
            self.count[str(user_id)] = 1
        else:
            self.count[str(user_id)] += 1
        self.count["total"] += 1
        with open("./data/lewd.json", "w", encoding="utf-8") as f:
            dump(self.count, f, ensure_ascii=False, indent=4)

    @slash_command(
        name="lewd",
        description="取得一張色圖",
        guild_ids=[879748390290853918, 624590181298601985],
    )
    async def lewd_pic(self, ctx: ApplicationContext):
        if ctx.channel_id != 1107999740408385646 and ctx.user.id != 551024169442344970:
            await ctx.respond("大庭廣眾之下還想偷色色阿", delete_after=30)
            return
        if  not path.exists('/mnt/lewd/cache'):
            await ctx.respond("找不到色圖資料夾", delete_after=30)
            return
        lewd_path, ext = get_random_lewd()
        with open(lewd_path, "rb") as f:
            lewd_image = File(f, f"lewds.{ext}")

        await ctx.respond(
            "在Hachi的努力之下，找到這張圖了",
            file=lewd_image,
            ephemeral=True,
            view=Lewd_Buttons(ctx, self.lewd_logger, self.counter, self.update_event),
        )
        await self.lewd_logger(ctx, lewd_path, ext)
        self.counter(str(ctx.author.id))
        self.update_event.set()


def setup(bot: Bot):
    bot.add_cog(lewd(bot))


def teardown(bot: Bot):
    instance: lewd = bot.get_cog("lewd")  # type: ignore
    create_task(instance.session.close())
