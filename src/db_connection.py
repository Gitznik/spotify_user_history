import pydantic
from pymongo import MongoClient
from abc import ABC, abstractmethod
import pytz
from typing import List

from .logging.logger import info_logger, debug_logger

class DatabaseConnection(ABC):

    def __init__(self, db: str, tbl: str) -> None:
        self.conn = self._create_connection(db, tbl)

    @abstractmethod
    def _create_connection(self):
        pass
    
    @abstractmethod
    def save_one(self):
        pass

    @abstractmethod
    def save_many(self):
        pass

    @abstractmethod
    def find_newest(self):
        pass

class MongoConnection(DatabaseConnection):

    def _create_connection(self, db, tbl) -> MongoClient:
        return MongoClient('172.20.128.1', 27017)[db][tbl]

    def find_newest(self):
        newest_unaware = self.conn.find_one(
            sort=[('played_at', -1)])['played_at']
        return pytz.utc.localize(newest_unaware)

    def save_one(self, data: pydantic.BaseModel) -> None:
        inserted = self.conn.insert_one(data.dict())
        debug_logger.debug(f'Inserted {inserted.inserted_id}')


    def save_many(self, data: List[pydantic.BaseModel]) -> None:
        data_parsed = [item.dict() for item in data]
        inserted = self.conn.insert_many(data_parsed)
        debug_logger.debug(f'Inserted {inserted.inserted_ids}')
        

    def reset_collection(self) -> None:
        self.conn.delete_many({})