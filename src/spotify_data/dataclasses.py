import pydantic
from datetime import datetime, date
from typing import List, Optional

from ..logging.logger import info_logger, debug_logger

class Config:
    allow_mutation = False

class SpotifyArtist(pydantic.BaseModel):
    id: str
    name: str

    class Config:
        allow_mutation = False
    
class SpotifyAlbum(pydantic.BaseModel):
    album_type: str
    artists: List[SpotifyArtist]
    id: str
    name: str
    release_date: date

    class Config:
        allow_mutation = False

class SpotifySong(pydantic.BaseModel):
    artists: List[SpotifyArtist]
    album: SpotifyAlbum
    duration_ms: int
    explicit: bool
    href: str
    id: str
    name: str
    popularity: int

    @pydantic.validator('popularity')
    @classmethod
    def popularity_valid(cls, value) -> None:
        if value < 0 or value > 100:
            raise ValueError(f'Popularity {value} outside the valid range' + 
                                f'Should be between 0 and 100')
        return value

    class Config:
        allow_mutation = False

class SpotifyHistoryObjectContext(pydantic.BaseModel):
    type: str
    uri: str

    class Config:
        allow_mutation = False

class SpotifyHistoryObject(pydantic.BaseModel):
    played_at: datetime
    track: SpotifySong
    context: SpotifyHistoryObjectContext

    def __init__(self, **data):
        debug_logger.debug(f'Instantiate Spotify History Object for track' + 
                            f'{data["track"]["id"]}')
        super().__init__(**data)

    class Config:
        allow_mutation = False

class SpotifyCursor(pydantic.BaseModel):
    before: Optional[int]
    after: Optional[int]

    @property
    def before_datetime(self):
        if self.before:
            return datetime.utcfromtimestamp(
                self.before / 1000).strftime("%Y-%m-%d %H:%M:%S")
        return None

    @property
    def after_datetime(self):
        if self.after:
            return datetime.utcfromtimestamp(
                self.after / 1000).strftime("%Y-%m-%d %H:%M:%S")
        return None

    class Config:
        allow_mutation = False

class SpotifyHistory(pydantic.BaseModel):
    items: List[SpotifyHistoryObject]
    next: Optional[str] = None
    cursors: Optional[SpotifyCursor] = None
    limit: int
    href: str

    def __init__(self, **data) -> None:
        info_logger.info(f'Instantiating Spotify History for {data["href"]}')
        super().__init__(**data)
        if self.is_last:
            info_logger.info(f'Done instantiating final Spotify History')
        else:
            info_logger.info(f'Done instantiating Spotify History from ' + 
                f'{self.cursors.before_datetime} to ' + 
                f'{self.cursors.after_datetime}')

    @property
    def is_last(self) -> bool:
        return bool(self.next)

    def __str__(self) -> str:
        return f'History contains {len(self.items)} tracks'