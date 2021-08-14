import datetime
import os
import unittest
from unittest import mock
import json

from src.db_connection import SqlLiteConnection

class TestSqliteConnection(unittest.TestCase):
    def setUp(self) -> None:
        self.conn = SqlLiteConnection(
            'song_history',
            'testing',
            '/home/robert/projects/spotify_user_history/data'
        )

    def tearDown(self) -> None:
        try:
            os.remove('/home/robert/projects/spotify_user_history/data/testing.db')
        except:
            print('File not found, this can happen if no changes to the DB are made')

    def test_find_newest(self):
        self.assertIsNone(self.conn.find_newest())

if __name__ == '__main__':
    unittest.main()