import pydantic
from pymongo import MongoClient
from abc import ABC, abstractmethod
import pytz
from typing import List
from datetime import datetime

from .logging.logger import info_logger, debug_logger

class DatabaseConnection(ABC):

    def __init__(self) -> None:
        self.conn = self.create_connection()

    def __enter__(self):
        return self

    def __exit__(self, *args):
        self.close_connection()

    @abstractmethod
    def close_connection(self):
        pass

    @abstractmethod
    def create_connection(self):
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

    def __init__(
            self, 
            db: str, 
            tbl: str, 
            host: str = 'localhost', 
            port: int = 27017):

        self.db = db
        self.tbl = tbl
        self.host = host
        self.port = port
        super().__init__()
        self.collection = self.conn[self.db][self.tbl]

    def create_connection(self) -> MongoClient:
        return MongoClient(self.host, self.port)

    def close_connection(self) -> None:
        self.conn.close()

    def find_newest(self) -> datetime:
        newest_unaware = self.collection.find_one(
            sort=[('played_at', -1)])['played_at']
        return pytz.utc.localize(newest_unaware)

    def save_one(self, data: pydantic.BaseModel) -> None:
        inserted = self.collection.insert_one(data.dict())
        debug_logger.debug(f'Inserted {inserted.inserted_id}')


    def save_many(self, data: List[pydantic.BaseModel]) -> None:
        data_parsed = [item.dict() for item in data]
        inserted = self.collection.insert_many(data_parsed)
        debug_logger.debug(f'Inserted {inserted.inserted_ids}')
        

    def reset_collection(self) -> None:
        self.collection.delete_many({})