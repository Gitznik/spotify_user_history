import pydantic
from pymongo import MongoClient
from abc import ABC, abstractmethod
import pymongo
import sqlite3
import pytz
from typing import List, Optional
from datetime import datetime
import pandas as pd
from pathlib import Path
import os
from dateutil.parser import parse

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

class SqlLiteConnection(DatabaseConnection):
    def __init__(
            self, 
            tbl: str, 
            db: str = 'spotify_data.db', 
            path: str = '../data/') -> None:

        self.db = db
        self.tbl = tbl
        self.file_path = os.path.join(
            os.path.dirname(__file__), (path + db))
        super().__init__()

    def _create_connection(self) -> sqlite3.Connection:
        try:
            debug_logger.debug(
                f'Connecting to SqlLite Database {self.file_path}')
            return sqlite3.connect(self.file_path)
        except:
            raise

    def close_connection(self):
        debug_logger.debug(
            f'Closing SqlLite Database {self.file_path}')
        self.conn.close()

    def find_newest(self):
        sql = f'SELECT MAX(played_at) FROM {self.tbl}'
        return parse(self.conn.execute(sql).fetchall()[0][0])

    def save_one(self, data: pydantic.BaseModel) -> None:
        df = self._prepare_song_history(data)
        df.to_sql(self.tbl, self.conn, if_exists='append', index=False)

    def save_many(self, data: List[pydantic.BaseModel]) -> None:
        data_parsed = [item.dict() for item in data]
        df = self._prepare_song_history(data_parsed)
        df.to_sql(self.tbl, self.conn, if_exists='append', index=False)

    def _prepare_song_history(self, data: pydantic.BaseModel) -> pd.DataFrame:
        columns = [
            'played_at', 
            'track.artists', 
            'track.album.album_type', 
            'track.album.artists', 
            'track.album.id', 
            'track.album.name', 
            'track.album.release_date', 
            'track.duration_ms', 
            'track.explicit', 
            'track.href', 
            'track.id', 
            'track.name', 
            'track.popularity']
        column_types = {
            'track.artists': 'str',
            'track.album.artists': 'str'
        }
        df = pd.json_normalize(data)
        return df.astype(column_types)[columns]

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
        debug_logger.debug(f'Inserted {inserted.inserted_id}')


    def save_many(
            self, 
            data: List[pydantic.BaseModel], 
            save_csv: bool = True,
            csv_path: Path = Path('data/songs.csv')) -> None:
        data_parsed = [item.dict() for item in data]
        if save_csv:
            self._save_csv_copy(data_parsed, csv_path)
        inserted = self.collection.insert_many(data_parsed)
        debug_logger.debug(f'Inserted {inserted.inserted_ids}')
        
    @staticmethod
    def _save_csv_copy(
            parsed_data: List[dict], 
            path: Path = Path('data/songs.csv')) -> None:
        mode = 'a' if bool(path.exists()) else 'w'
        use_headers = not bool(path.exists())
        
        info_logger.info('Saving csv copy of the data')
        df = pd.json_normalize(parsed_data)
        df.to_csv(
            'data/songs.csv', mode = mode, header=use_headers, index=False)

    def reset_collection(self) -> None:
        self.collection.delete_many({})
        info_logger.warning(f'Deleted all documents from {self.db}:{self.tbl}')