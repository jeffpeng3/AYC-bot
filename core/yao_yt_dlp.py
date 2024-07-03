from itertools import islice
from typing import AsyncIterator
from discord import Member
import yt_dlp
import asyncio

from model.music_model import Song_Info


class Music_Info_Extrector:
    ytdl_song_opt = {
        "format": "ba/b",
        "restrictfilenames": True,
        "default_search": "auto",
        "noplaylist": True,
        "skip_download": True,
        "flat-playlist": True,
        "nocheckcertificate": True,
        "ignoreerrors": True,
        "logtostderr": False,
        "quiet": True,
        "no_warnings": True,
        "source_address": "0.0.0.0",
    }

    ytdl_playlist_opt = {
        "format": "ba/b",
        "restrictfilenames": True,
        "default_search": "auto",
        "skip_download": True,
        "flat-playlist": True,
        "extract_flat": True,
        "nocheckcertificate": True,
        "ignoreerrors": True,
        "logtostderr": False,
        "quiet": True,
        "no_warnings": True,
        "source_address": "0.0.0.0",
    }

    @staticmethod
    def get_music_info_sync(url, member) -> Song_Info:
        data: dict | None = yt_dlp.YoutubeDL(
            Music_Info_Extrector.ytdl_song_opt
        ).extract_info(url)
        if data is None:
            raise KeyError("search failure : data not found")
        if data.get("_type") == "playlist":
            data = data["entries"][0]
        if data is None:
            raise KeyError("search failure : data not found")
        return Song_Info(
            url=data["webpage_url"],
            title=data["title"],
            channel=data["uploader"],
            channel_url=data["uploader_url"],
            thumbnail=data["thumbnail"],
            requester=member,
        )

    @staticmethod
    async def get_music_info(url: str, member: Member | None) -> Song_Info:
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            None, Music_Info_Extrector.get_music_info_sync, url, member
        )

    @staticmethod
    async def get_playlist(url, member) -> AsyncIterator[Song_Info]:
        data: dict | None = yt_dlp.YoutubeDL(
            Music_Info_Extrector.ytdl_playlist_opt
        ).extract_info(url)
        if data is None:
            raise KeyError("search failure : data not found")
        if not data.get("_type") == "playlist":
            data: dict | None = yt_dlp.YoutubeDL(
                Music_Info_Extrector.ytdl_playlist_opt
            ).extract_info(data['url'])
        if data is None:
            raise KeyError("search failure : data not found")
        if not data.get("_type") == "playlist":
            raise TypeError("this is not a playlist")
        coros = map(
            lambda x: Music_Info_Extrector.get_music_info(x['url'], member),
            data["entries"],
        )
        batch_size = 13
        while batch := tuple(islice(coros, batch_size)):
            tasks = map(asyncio.create_task,batch)
            for task in asyncio.as_completed(tasks):
                try:
                    yield await task
                except Exception as e:
                    print('skip',e)




async def test():
    music_ext = Music_Info_Extrector()
    # tasks: list[asyncio.Task] = []
    # tasks.append(
    #     asyncio.create_task(
    #         music_ext.get_music_info(
    #             "https://www.youtube.com/watch?v=m2IXWFYfTew", None
    #         )
    #     )
    # )
    # tasks.append(
    #     asyncio.create_task(
    #         music_ext.get_music_info(
    #             "https://www.youtube.com/live/m2IXWFYfTew?feature=share", None
    #         )
    #     )
    # )
    # tasks.append(
    #     asyncio.create_task(
    #         music_ext.get_music_info(
    #             "https://www.youtube.com/watch?v=0ScSkht_qLY&list=PLwW-jiBMC59iewtUTK-P8utZSnGbMBT_r&index=2",
    #             None,
    #         )
    #     )
    # )
    # tasks.append(
    #     asyncio.create_task(
    #         music_ext.get_music_info("https://youtu.be/2epJQyYSF2Q", None)
    #     )
    # )
    # tasks.append(
    #     asyncio.create_task(
    #         music_ext.get_music_info(
    #             "https://www.youtube.com/watch?v=bE6NjdIA-aE", None
    #         )
    #     )
    # )
    async for i in music_ext.get_playlist("https://www.youtube.com/watch?v=EoPFGj3uuYo&list=PL0bHKk6wuUGL_Qd34mf0XsQnyiDk2OeGR",None):
        print(i)
    # await asyncio.wait(tasks)
    # print(*[i.result() for i in tasks],sep='\n')

if __name__ == '__main__':
    asyncio.run(test())
