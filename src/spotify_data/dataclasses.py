import pydantic
from datetime import datetime, date
from typing import List

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
        debug_logger.debug(f'Instantiate Spotify History Object for track {data["track"]["id"]}')
        super().__init__(**data)

    class Config:
        allow_mutation = False

class SpotifyCursor(pydantic.BaseModel):
    before: int
    after: int

    @property
    def before_datetime(self):
        return datetime.utcfromtimestamp(
            self.before / 1000).strftime("%Y-%m-%d %H:%M:%S")

    @property
    def after_datetime(self):
        return datetime.utcfromtimestamp(
            self.after / 1000).strftime("%Y-%m-%d %H:%M:%S")

    class Config:
        allow_mutation = False

class SpotifyHistory(pydantic.BaseModel):
    items: List[SpotifyHistoryObject]
    next: str
    cursors: SpotifyCursor
    limit: int
    href: str
    is_last: bool = False

    def __init__(self, **data):
        info_logger.info(f'Instantiating Spotify History for {data["href"]}')
        super().__init__(**data)
        info_logger.info(f'Done instantiating Spotify History from ' + 
            f'{self.cursors.before_datetime} to {self.cursors.after_datetime}')

    @pydantic.validator('is_last')
    @classmethod
    def populate_is_last(cls, v, values):
        return bool(values.get['next'])

    def __str__(self) -> str:
        return f'History contains {len(self.items)} tracks'