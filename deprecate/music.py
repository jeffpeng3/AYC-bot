from typing import Callable
from discord import (
    ApplicationContext,
    AutocompleteContext,
    ButtonStyle,
    Client,
    Embed,
    Interaction,
    Member,
    Message,
    Bot,
    SlashCommandGroup,
    option,
    Cog,
    InputTextStyle,
)
from discord.ext.pages import Paginator
from discord.ext import commands
from discord.channel import VocalGuildChannel
from discord.abc import Connectable, GuildChannel
from discord.ui import View, button, Button, Modal, InputText
from discord.colour import Colour
from model.music_model import LoopMode, Song
from mafic import Player as _Player
from mafic import TrackStartEvent, TrackEndEvent, TrackStuckEvent, TrackExceptionEvent
from core.yao_yt_dlp import Music_Info_Extrector
from random import randint
from json import load, dump

async def get_song(url:str,player:"Player",ctx:ApplicationContext|Interaction,position=0.0):
    if isinstance(ctx, ApplicationContext):
        author = ctx.author
    elif isinstance(ctx, Interaction):
        author = ctx.user
    if not isinstance(author, Member):
        raise TypeError("你不可能不是個member吧")
    song_info = await Music_Info_Extrector().get_music_info(url, author)
    tracks = await player.fetch_tracks(song_info.url)
    if not isinstance(tracks, list):
        raise TypeError("你必須是一個list的說")
    track = tracks[0]
    if track.seekable:
        track.position = int(position * 1000)
    song: Song = Song(song_info, track)
    return song


class Play_modal(Modal):
    def __init__(self, player: "Player") -> None:
        super().__init__(title="輸入網址或曲名", timeout=60)
        self.player = player
        self.add_item(InputText(label="請輸入網址，一行一個", required=False, style=InputTextStyle.long,placeholder='https://www.youtube.com/watch?v=xxxxxxx'))
        self.add_item(InputText(label="請輸入曲名，一行一個", required=False, style=InputTextStyle.long,placeholder='曲名'))

    async def callback(self, interaction: Interaction):
        await interaction.response.defer()
        song_list = []
        for i in self.children:
            if not i.value:
                continue
            for i in i.value.split("\n"):
                song = await get_song(i,self.player,interaction,0)
                song_list.append(song)
        if not song_list:
            return
        for i in song_list:
            await self.player.add_queue(i)
        await self.player.update_panel()


class Remove_View(View):
    def __init__(self, player: "Player"):
        super().__init__(timeout=60)
        self.player = player

    @button(style=ButtonStyle.blurple, emoji="⏏️")
    async def callback(self, btn: Button, interaction: Interaction):
        await interaction.response.defer()
        if not isinstance(interaction.message, Message):
            return
        message = interaction.message
        embed = message.embeds[0]
        if not isinstance(embed.title, str):
            return
        index = int(embed.title.split(".")[0])
        self.player.remove_queue(index)
        if isinstance(btn.view, View):
            btn.view.disable_all_items()
            btn.view.stop()
        await interaction.delete_original_response()
        await self.player.update_panel()


class History_Play_View(View):
    def __init__(self, player: "Player"):
        super().__init__(timeout=60)
        self.player = player

    @button(style=ButtonStyle.blurple, emoji="▶️")
    async def callback(self, btn: Button, interaction: Interaction):
        await interaction.response.defer()
        if not isinstance(interaction.message, Message):
            return
        if not isinstance(interaction.user, Member):
            return
        message = interaction.message
        embed = message.embeds[0]
        if not isinstance(embed.title, str):
            return
        index = int(embed.title.split(".")[0])
        await self.player.play_history(index, interaction.user)
        if isinstance(btn.view, View):
            btn.view.disable_all_items()
            btn.view.stop()
        await interaction.delete_original_response()
        await self.player.update_panel()


class Select_Page(Paginator):
    def __init__(self, bot: Client, song_list: list[Song], view: View):
        self.bot: Client = bot
        pages = [*map(self.song_to_embed, enumerate(song_list))]
        super().__init__(pages=pages, custom_view=view, timeout=60)  # type: ignore

    def song_to_embed(self, data: tuple[int, Song]) -> Embed:
        index, song = data
        embed = Embed()
        embed.set_author(
            name=song.info.channel,
            url=song.info.channel_url,
        )
        embed.set_image(url=song.info.thumbnail)
        embed.title = f"{index+1}.{song.info.title}"
        embed.url = song.info.url
        embed.set_footer(
            text=f"{song.info.requester}點的",
            icon_url=song.info.requester.display_avatar.url,
        )
        return embed

    async def respond(self, interaction: Interaction, ephemeral: bool = False):
        await super().respond(interaction, ephemeral)


class Panel_View(View):
    def __init__(self, player: "Player"):
        super().__init__(timeout=None)
        self.player: Player = player

    @staticmethod
    def check_permissions(func) -> Callable:
        def check(self: "Panel_View", interaction: Interaction):
            if not isinstance(interaction.user, Member):
                return False
            if not isinstance(interaction.client, Bot):
                return False
            if interaction.user.id == interaction.client.owner_id:
                return True
            if not interaction.user.voice:
                return False
            if not interaction.user.voice.channel:
                return False
            if not isinstance(self.player.channel, GuildChannel):
                return False
            if interaction.user.voice.channel.id != self.player.channel.id:
                return False
            return True

        async def warp(self: "Panel_View", btn: Button, interaction: Interaction):
            if check(self, interaction):
                await func(self, btn, interaction)
            else:
                await interaction.response.defer()

        return warp

    @button(style=ButtonStyle.danger, emoji="✖️")
    @check_permissions
    async def call_exit(self, btn: Button, interaction: Interaction) -> None:
        await interaction.response.defer()
        try:
            await self.player.msg.delete()
        except Exception:
            pass
        await self.player.destroy()

    @button(style=ButtonStyle.blurple, emoji="⏪")
    @check_permissions
    async def call_rewind(self, btn: Button, interaction: Interaction) -> None:
        await interaction.response.defer()
        if self.player.current and self.player.current.seekable:
            await self.player.seek(max(self.player.position - 5000, 0))

    @button(style=ButtonStyle.green, emoji="⏯️")
    @check_permissions
    async def call_pause(self, btn: Button, interaction: Interaction) -> None:
        await interaction.response.defer()
        if not self.player.current:
            return
        pause = not self.player.paused
        await self.player.pause(pause)
        self.player._paused = pause
        await self.player.update_panel()

    @button(style=ButtonStyle.blurple, emoji="⏩")
    @check_permissions
    async def call_forward(self, btn: Button, interaction: Interaction) -> None:
        await interaction.response.defer()
        if self.player.current and self.player.current.seekable:
            await self.player.seek(self.player.position + 5000)

    @button(style=ButtonStyle.blurple, emoji="⏭️")
    @check_permissions
    async def call_skip(self, btn: Button, interaction: Interaction) -> None:
        await interaction.response.defer()
        if self.player.current:
            await self.player.stop()

    # ==================================================================================
    @button(style=ButtonStyle.gray, emoji="🔉")
    @check_permissions
    async def call_volume_down(self, btn: Button, interaction: Interaction) -> None:
        await interaction.response.defer()
        self.player.volume = max(self.player.volume - 5, 0)
        await self.player.set_volume(self.player.volume)
        await self.player.update_panel()

    @button(style=ButtonStyle.gray, emoji="🔊")
    @check_permissions
    async def call_volume_up(self, btn: Button, interaction: Interaction) -> None:
        await interaction.response.defer()
        self.player.volume = min(self.player.volume + 5, 100)
        await self.player.set_volume(self.player.volume)
        await self.player.update_panel()

    @button(style=ButtonStyle.blurple, emoji="🔍")
    @check_permissions
    async def call_add_new_song(self, btn: Button, interaction: Interaction) -> None:
        modal = Play_modal(self.player)
        await interaction.response.send_modal(modal)

    @button(style=ButtonStyle.blurple, emoji="🔀")
    @check_permissions
    async def call_shuffle(self, btn: Button, interaction: Interaction) -> None:
        await interaction.response.defer()
        await self.player.shuffle()
        await self.player.update_panel()

    @button(style=ButtonStyle.blurple, emoji="🔁")
    @check_permissions
    async def call_loop(self, btn: Button, interaction: Interaction) -> None:
        await interaction.response.defer()
        match self.player.loop:
            case LoopMode.ALL:
                self.player.loop = LoopMode.SINGLE
            case LoopMode.SINGLE:
                self.player.loop = LoopMode.NONE
            case LoopMode.NONE:
                self.player.loop = LoopMode.ALL
        await self.player.update_panel()

    # ==================================================================================

    @button(style=ButtonStyle.blurple, emoji="⏏️")
    @check_permissions
    async def call_remove(self, btn: Button, interaction: Interaction) -> None:
        view = Remove_View(self.player)
        if not self.player.queue:
            await interaction.response.send_message("沒有待播放歌曲", ephemeral=True)
            return
        paginator = Select_Page(interaction.client, self.player.queue[1:], view)
        await paginator.respond(interaction, ephemeral=True)

    @button(style=ButtonStyle.blurple, emoji="📜")
    @check_permissions
    async def call_play_history(self, btn: Button, interaction: Interaction) -> None:
        view = History_Play_View(self.player)
        if not self.player.history:
            await interaction.response.send_message("沒有已播放歌曲", ephemeral=True)
            return
        paginator = Select_Page(interaction.client, self.player.history, view)
        await paginator.respond(interaction, ephemeral=True)

    @button(style=ButtonStyle.red, emoji="🎚️")
    @check_permissions
    async def call_EQ(self, btn: Button, interaction: Interaction) -> None:
        await interaction.response.defer()


class Player(_Player):
    def __init__(self, client: Client, channel: Connectable):
        super().__init__(client, channel)
        self.msg: Message
        self.queue: list[Song] = []
        self.history: list[Song] = []
        self.volume: int = 30
        self.loop: LoopMode = LoopMode.NONE

    async def init_panel(self, ctx: ApplicationContext):
        self.msg = await ctx.send(embed=self.panel(), view=self.view())

    def remove_queue(self, index: int):
        del self.queue[index]

    async def play_history(self, index: int, requester: Member):
        song = self.history[index - 1]
        song.info.requester = requester
        await self.add_queue(song)
        del self.history[index - 1]

    async def shuffle(self) -> None:
        length = len(self.queue)
        for i in range(1, length):
            j = randint(i, length - 1)
            self.queue[i], self.queue[j] = self.queue[j], self.queue[i]

    async def add_queue(self, song: Song):
        self.queue.append(song)
        await self.try_play()

    async def try_play(self) -> bool:
        if self.current:
            return False
        if not self.queue:
            return False
        track = self.queue[0].track
        await self.play(track, start_time=track.position, volume=self.volume)
        return True

    async def update_panel(self) -> None:
        await self.msg.edit(embed=self.panel())

    def view(self) -> View:
        return Panel_View(self)

    def panel(self) -> Embed:
        embed = Embed()
        embed.color = Colour.red()
        if not isinstance(self.channel, VocalGuildChannel):
            raise TypeError("這它媽都是啥頻道阿")
        embed.add_field(name="語音頻道", value=self.channel.name, inline=False)
        embed.add_field(name="循環模式", value=self.loop.value, inline=False)
        embed.add_field(
            name="播放狀態",
            value=("⏸️" if self.paused else "▶️") if self.current else "⏹️",
            inline=False,
        )
        embed.add_field(name="音量", value=f"{self.volume}%", inline=False)
        embed.add_field(
            name=f"播放清單-{len(self.queue[1:])}首待撥放",
            value="\n\n".join(map(Song.simple_str, self.queue[1:6]))
            if self.queue[1:]
            else "無待撥放的歌曲",
        )
        embed.add_field(
            name=f"歷史播放清單-{len(self.history)}首已撥放",
            value="\n\n".join(map(Song.simple_str, reversed(self.history[-5:])))
            if self.history
            else "無已撥放的歌曲",
        )
        if self.queue:
            song = self.queue[0]
            embed.set_author(
                name=song.info.channel,
                url=song.info.channel_url,
            )
            embed.set_footer(
                text=song.info.requester.display_name,
                icon_url=song.info.requester.display_avatar,
            )
            embed.set_thumbnail(url=song.info.thumbnail)
            embed.title = song.info.title
            embed.url = song.info.url
        else:
            embed.title = "沒有正在撥放的曲目"
        return embed


class music(Cog):
    music_command = SlashCommandGroup("music")

    def __init__(self, bot: Bot) -> None:
        self.bot: Bot = bot
        self.playlist: dict[str, dict[str, list[str]]]

        with open("data/playlist.json", "r", encoding="utf-8") as f:
            self.playlist = load(f)

    # region listener
    @Cog.listener("on_track_start")
    async def on_track_start(self, event: TrackStartEvent):
        player: Player = event.player
        await player.update_panel()

    @Cog.listener("on_track_end")
    async def on_track_end(self, event: TrackEndEvent):
        player: Player = event.player
        loop_mode_cache = player.loop
        if event.reason == "STOPPED":
            player.loop = LoopMode.NONE

        match player.loop:
            case LoopMode.NONE:
                song = player.queue[0]
                player.history.append(song)
                del player.queue[0]
            case LoopMode.ALL:
                song = player.queue[0]
                player.queue.append(song)
                del player.queue[0]
            case LoopMode.SINGLE:
                pass

        player.loop = loop_mode_cache
        await player.try_play()
        await player.update_panel()

    @Cog.listener("on_track_stuck")
    async def on_track_stuck(self, event: TrackStuckEvent):
        print(event)
        player: Player = event.player
        match player.loop:
            case LoopMode.NONE:
                song = player.queue[0]
                player.history.append(song)
                del player.queue[0]
            case LoopMode.ALL:
                song = player.queue[0]
                player.queue.append(song)
                del player.queue[0]
            case LoopMode.SINGLE:
                pass

        await player.try_play()
        await player.update_panel()

    @Cog.listener("on_track_exception")
    async def on_track_exception(self, event: TrackExceptionEvent):
        print(event)
        # player: Player = event.player
        # match player.loop:
        #     case LoopMode.NONE:
        #         song = player.queue[0]
        #         player.history.append(song)
        #         del player.queue[0]
        #     case LoopMode.ALL:
        #         song = player.queue[0]
        #         player.queue.append(song)
        #         del player.queue[0]
        #     case LoopMode.SINGLE:
        #         pass

        # await player.try_play()
        # await player.update_panel()

    # endregion listener

    @staticmethod
    async def is_vaild_to_join(ctx) -> bool:
        if not isinstance(ctx.user, Member):
            return False
        if not ctx.user.voice:
            return False
        if not ctx.user.voice.channel:
            return False
        return True

    async def auto_complete_playlist(self, ctx: AutocompleteContext) -> list[str]:
        if not ctx.interaction.user:
            return []
        user_id = str(ctx.interaction.user.id)
        suggest = self.playlist.get("playlist", {}).get(user_id, [])
        return [*filter(lambda x: ctx.value.lower() in x.lower(), suggest)]

    async def auto_complete_song(self, ctx: AutocompleteContext) -> list[str]:
        if not ctx.interaction.user:
            return []
        user_id = str(ctx.interaction.user.id)
        suggest = self.playlist.get("song", {}).get(user_id, [])
        return [*filter(lambda x: ctx.value.lower() in x.lower(), suggest)]

    def save_url(self, url: str, user_id: str, url_type: str) -> None:
        data = self.playlist[url_type]
        if url in data.get(user_id, []):
            return
        data[user_id] = data.get(user_id, [])
        data[user_id].append(url)
        data[user_id] = data[user_id][-5:]
        with open("data/playlist.json", "w", encoding="utf-8") as f:
            dump(self.playlist, f, ensure_ascii=False, indent=4)

    @commands.check(is_vaild_to_join)
    @music_command.command(name="join", description="呼叫機器人進語音", guild_only=True)
    async def join(self, ctx: ApplicationContext):
        await self.join_vc(ctx, True)

    @commands.check(is_vaild_to_join)
    @music_command.command(name="play", description="點首歌", guild_only=True)
    @option(type=str, name="url", description="歌名或網址", autocomplete=auto_complete_song)
    @option(
        type=float, name="position", description="開始位置(秒)", default=0.0, min_value=0.0
    )
    async def play(self, ctx: ApplicationContext, url: str, position: float):
        player = ctx.voice_client
        if not isinstance(player, Player):
            raise TypeError("這它媽怎麼會沒有player")
        if not isinstance(ctx.author, Member):
            raise TypeError("你不可能不是個member吧")
        await ctx.respond(f"你點的[音樂]({url})正在載入中", ephemeral=True)
        song = await get_song(url,player,ctx,position)
        await player.add_queue(song)
        await ctx.interaction.edit_original_response(
            content=f"你點了[{song.info.title}]({song.info.url})"
        )
        self.save_url(url, str(ctx.author.id), "song")
        await player.update_panel()

    @commands.check(is_vaild_to_join)
    @music_command.command(name="seek", description="快轉一下", guild_only=True)
    @option(type=float, name="position", description="開始位置(秒)", min_value=0.0)
    async def seek(self, ctx: ApplicationContext, position: float):
        player = ctx.voice_client
        if not isinstance(player, Player):
            raise TypeError("這它媽怎麼會沒有player")
        if not isinstance(ctx.author, Member):
            raise TypeError("你不可能不是個member吧")
        if track := player.current:
            if track.seekable:
                await player.seek(int(position * 1000))
                await ctx.respond(f"已快轉到{position}秒處", ephemeral=True)
            else:
                await ctx.respond("老鐵，這不能快轉啊", ephemeral=True)
        else:
            await ctx.respond("老鐵，先點個歌再說吧", ephemeral=True)

        await player.update_panel()

    @commands.check(is_vaild_to_join)
    @music_command.command(name="listplay", description="點個歌單", guild_only=True)
    @option(
        type=str, name="url", description="歌單的網址", autocomplete=auto_complete_playlist
    )
    async def listplay(self, ctx: ApplicationContext, url: str):
        if not (player := ctx.voice_client):
            player = ctx.voice_client
        if not isinstance(player, Player):
            raise TypeError("這它媽怎麼會沒有player")
        if not isinstance(ctx.author, Member):
            raise TypeError("你不可能不是個member吧")
        await ctx.respond(f"你點的[歌單]({url})正在載入中", ephemeral=True)
        self.save_url(url, str(ctx.author.id), "playlist")
        async for i in Music_Info_Extrector().get_playlist(url, ctx.author):
            tracks = await player.fetch_tracks(i.url)
            if not isinstance(tracks, list):
                raise TypeError("你必須是一個list的說")
            track = tracks[0]
            song: Song = Song(i, track)
            await player.add_queue(song)
        await player.update_panel()

    @play.before_invoke
    @listplay.before_invoke
    async def join_vc(self, ctx: ApplicationContext, reply: bool = False):
        async def nop(*arg, **kwarg):
            pass

        if reply:
            respond = ctx.respond
        else:
            respond = nop
        if not isinstance(ctx.user, Member):
            return False
        if not ctx.user.voice:
            return False
        if not ctx.user.voice.channel:
            return False
        if ctx.voice_client:
            await respond("機器人已經進入語音", ephemeral=True)
            return

        player = await ctx.user.voice.channel.connect(cls=Player)
        await ctx.respond(f"機器人已加入頻道:{ctx.user.voice.channel}", ephemeral=True)
        await player.init_panel(ctx)


def setup(bot: Bot):
    bot.add_cog(music(bot))
