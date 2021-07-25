from pymongo import MongoClient
from abc import ABC, abstractmethod
import pytz

class DatabaseConnection(ABC):

    def __init__(self, db: str, tbl: str) -> None:
        self.conn = self._create_connection(db, tbl)

    @abstractmethod
    def _create_connection(self):
        pass
    
    @abstractmethod
    def save_data(self):
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

    def save_data(self, data: dict) -> None:
        self.conn.insert_one(data)

    def reset_collection(self) -> None:
        self.conn.delete_many({})