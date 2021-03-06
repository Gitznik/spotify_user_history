import pydantic
from pymongo import MongoClient
from abc import ABC, abstractmethod
import pymongo
import pytz
from typing import List
from datetime import datetime

from .logging.logger import info_logger, debug_logger
from .errors.database_errors import DbConnectionTimeout, DbInvalidName

class DatabaseConnection(ABC):

    def __init__(self) -> None:
        self.conn = self._create_connection()

    def __enter__(self):
        return self

    def __exit__(self, *args) -> None:
        self.close_connection()

    @abstractmethod
    def close_connection(self):
        pass

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

    def __init__(
            self, 
            db: str, 
            tbl: str, 
            host: str = 'localhost', 
            port: int = 27017) -> None:

        self.db = db
        self.tbl = tbl
        self.host = host
        self.port = port
        super().__init__()
        self.collection = self._define_collection(db, tbl)


    def _create_connection(self) -> MongoClient:
        try:
            client = MongoClient(self.host, self.port)
            debug_logger.debug(
                f'Connecting to MongoDb Version: ' + 
                f'{client.server_info()["version"]}')
            return client
        except pymongo.errors.ServerSelectionTimeoutError as e:
            info = f'Timeout for {self.host}:{self.port}, server not reachable'
            raise DbConnectionTimeout(info)
        except:
            raise

    def _define_collection(self, db: str, tbl: str) -> MongoClient:
        if db not in {database['name'] for database in self.conn.list_databases()}:
            info_logger.warn(
                f'Database {db} does not exist and will be created')
        if tbl not in {coll for coll in self.conn[db].list_collection_names()}:
            info_logger.warn(
                f'Collection {tbl} does not exist and will be created')
        try:
            return self.conn[db][tbl]
        except pymongo.errors.InvalidName as e:
            raise DbInvalidName(str(e))

    def close_connection(self) -> None:
        debug_logger.debug(
                f'Disconnecting MongoDb Version: ' + 
                f'{self.conn.server_info()["version"]}')
        self.conn.close()

    def find_newest(self) -> datetime:
        newest_unaware = self.collection.find_one(
            sort=[('played_at', -1)])['played_at']
        return pytz.utc.localize(newest_unaware)

    def save_one(self, data: pydantic.BaseModel) -> None:
        inserted = self.collection.insert_one(data.dict())
        info_logger.info(f'Inserted {inserted.inserted_id}')


    def save_many(self, data: List[pydantic.BaseModel]) -> None:
        data_parsed = [item.dict() for item in data]
        inserted = self.collection.insert_many(data_parsed)
        info_logger.info(f'Inserted {inserted.inserted_ids}')
        

    def reset_collection(self) -> None:
        self.collection.delete_many({})
        info_logger.warning(f'Deleted all documents from {self.db}:{self.tbl}')