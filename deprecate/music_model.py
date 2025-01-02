from dataclasses import dataclass
from enum import Enum
from discord import Member
from mafic import Track

@dataclass
class Song_Info:
    url: str
    title: str
    channel: str
    channel_url: str
    thumbnail: str
    requester: Member

@dataclass
class Song:
    info: Song_Info
    track: Track

    def simple_str(self) -> str:
        temp = f'**[{self.info.title}]({self.info.url})**'
        return f'{temp}\n**{self.info.requester.display_name}**'

class LoopMode(Enum):
    NONE = "❌"
    ALL = "🔁"
    SINGLE = "🔂"
