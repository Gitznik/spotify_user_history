import requests
from datetime import datetime, timezone
from typing import List, Optional, Literal
from pydantic.error_wrappers import ValidationError

from .errors.token_errors import MissingScopeError
from ._auth.auth_flows import AuthFlow
from .db_connection import DatabaseConnection
from .request_utils import ApiLogger
from .logging.logger import info_logger, debug_logger
from .spotify_data.dataclasses import SpotifyArtist, SpotifyHistory, SpotifySong
from .config.configure_requests import configure_request

conf_requests = configure_request()


class SpotifyInteraction:
    def __init__(
            self, 
            connection: AuthFlow) -> None:
        info_logger.info(f'Instantiate SpotifyInteraction')
        self.conn = connection

    @ApiLogger('Sending Playlist Request')
    def _get_playlist_req(self, playlist_id: str) -> requests.Response:
        return self.conn.get_request(
            endpoint= f'https://api.spotify.com/v1/playlists/{playlist_id}',
        )

    def get_playlist(self, playlist_id: str) -> dict:
        return self._get_playlist_req(playlist_id).json()

    @ApiLogger('Sending a Track request')
    def _get_track_req(
            self, 
            track_id: str, 
            market: Optional[str] = None) -> requests.Response:
        params = None
        if market:
            params = {'market': market}
        return self.conn.get_request(
            endpoint = f'https://api.spotify.com/v1/tracks/{track_id}',
            params = params
        )
    
    def get_track(
            self, 
            track_id: str, 
            market: Optional[str] = None) -> SpotifySong:
        track_resp = self._get_track_req(track_id=track_id, market=market)
        try:
            return SpotifySong(**track_resp.json())
        except ValidationError as e:
            info_logger.exception(f'SpotifyTrack parsing failed on ' + 
                                  f'\n{track_resp.json()}\n')
            raise e

    @ApiLogger('Sending Play History Request')
    def _get_play_history_req(
            self, start_point_unix_ms: int) -> requests.Response:

        required_scope = 'user-read-recently-played'
        self.conn.check_scope(required_scope)

        params = {
            'limit': 20,
            'after': start_point_unix_ms
        }
        return self.conn.get_request(
            endpoint = 'https://api.spotify.com/v1/me/player/recently-played/',
            params = params,
        )

    def _get_play_history(self, start_point_unix_ms: int) -> SpotifyHistory:
        try:
            history_resp = self._get_play_history_req(
                start_point_unix_ms=start_point_unix_ms)
        except MissingScopeError:
            info_logger.warning(
                f'Scope not authorized', exc_info=True)
            self.conn.reset_refreshing_token('user-top-read')
            try:
                history_resp = self._get_play_history_req(
                    start_point_unix_ms=start_point_unix_ms)
            except:
                raise
        history_resp = self._get_play_history_req(
            start_point_unix_ms=start_point_unix_ms)
        try:
            return SpotifyHistory(**history_resp.json())
        except ValidationError as e:
            info_logger.exception(f'SpotifyHistory parsing failed on ' + 
                                  f'\n{history_resp.json()}\n')
            raise e


    def get_full_play_history(
            self, start_point_unix_ms: int) -> List[SpotifySong]:

        history = self._get_play_history(
            start_point_unix_ms=start_point_unix_ms)
        history_list = [history]
        while not history_list[-1].is_last:
            history_list.append(self._get_play_history(
                start_point_unix_ms=history_list[-1].cursors.after))
        return [item for hist in history_list for item in hist.items]

    def get_new_play_history(
            self, 
            database_conn: DatabaseConnection,
            fallback_datetime: datetime = datetime(
                2021, 7, 24, 10, 0, tzinfo=timezone.utc)
                ) -> List[SpotifySong]:
        try:
            start_point = database_conn.find_newest()
            start_point_ts = round(start_point.timestamp() * 1000)
            info_logger.info(f'Load play history after {start_point}')
        except:
            info_logger.warning('No existing start point found in MongoDB, ' + 
                                f'use fallback timestamp {fallback_datetime}')
            start_point_ts = round(fallback_datetime.timestamp() * 1000)

        return self.get_full_play_history(start_point_ts)

    @ApiLogger('Sending Top Artist or Track request')
    def _get_top_artists_or_tracks_req(
            self,
            type: Literal['artists', 'tracks'],
            time_range: Literal[
                'short_term', 'medium_term', 'long_term'] = 'medium_term',
            limit: int = 20,
            offset: int = 0) -> requests.Response:

        required_scope = 'user-top-read'
        self.conn.check_scope(required_scope)

        endpoint = f'https://api.spotify.com/v1/me/top/{type}'
        params = {
            'time_range': time_range,
            'limit': limit,
            'offset': offset
        }
        return self.conn.get_request(
            endpoint = endpoint,
            params = params,
        )

    def get_top_artists_or_tracks(
            self,
            type: Literal['artists', 'tracks'],
            time_range: Literal[
                'short_term', 'medium_term', 'long_term'] = 'medium_term',
            limit: int = 20,
            offset: int = 0) -> List[SpotifySong]:
        try:
            items = self._get_top_artists_or_tracks_req(
                type, time_range, limit, offset).json()
        except MissingScopeError:
            info_logger.warning(
                f'Scope not authorized', exc_info=True)
            self.conn.reset_refreshing_token('user-top-read')
            try:
                items = self._get_top_artists_or_tracks_req(
                    type, time_range, limit, offset).json()
            except:
                raise
        if type == 'tracks':
            return [SpotifySong(**track) for track in items['items']]
        return [SpotifyArtist(**artist) for artist in items['items']]
        