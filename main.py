import os

from src.logging.logger import info_logger, debug_logger

from src._auth.auth_flows import AuthorizationCodeFlow
from src.spotify_interaction import SpotifyInteraction
from src.db_connection import MongoConnection

def main():
    flow = AuthorizationCodeFlow(scope = 'user-read-recently-played')
    interaction = SpotifyInteraction(connection=flow)

    
    with MongoConnection(
            db='spotify_user_history', 
            tbl='song_history', 
            host=os.environ['WSL_HOST']) as database_conn:

        play_history = interaction.get_new_play_history(database_conn=database_conn)
        if play_history:
            database_conn.save_many(play_history)
        else:
            info_logger.info('Nothing to do, no new tracks added')


if __name__ == '__main__':
    info_logger.info('--------------------')
    info_logger.info('Starting application')
    info_logger.info('--------------------')

    main()

    info_logger.info('--------------------')
    info_logger.info('Closing application')
    info_logger.info('--------------------')


