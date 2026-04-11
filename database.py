import atexit
import logging
import sqlite3
import sys

from pathlib import Path

from util import CharacterBannerType, error_and_exit


class Database:
    def __init__(self):
        self._try_create_db()
        logging.info('Connecting to database')
        self._con = sqlite3.connect(self._get_db_path())
        atexit.register(self._cleanup)

    def _cleanup(self):
        if self._con:
            logging.info('Closing database')
            self._con.close()

    def _get_db_path(self):
        if sys.platform != 'linux':
            error_and_exit('This software is meant to be run on Linux')

        return Path('~/.local/share/endfield-pull-tracker').expanduser() / 'db.sqlite3'

    def _try_create_db(self):
        database_path = self._get_db_path()
        if database_path.exists():
            logging.info('Database at path "%s" exists', database_path)
            return

        logging.info('Creating new database at path "%s"', database_path)
        database_path.parent.mkdir(parents=True, exist_ok=True)

        con = sqlite3.connect(database_path)
        try:
            with con:
                cur = con.cursor()

                # character table
                cur.execute('''
                    CREATE TABLE character (
                        id INTEGER PRIMARY KEY,
                        bannerID TEXT,
                        bannerName TEXT,
                        characterID TEXT,
                        characterName TEXT,
                        rarity INTEGER,
                        timestamp INTEGER,
                        new INTEGER,
                        free INTEGER
                    )
                ''')

                # weapon table
                cur.execute('''
                    CREATE TABLE weapon (
                        id INTEGER PRIMARY KEY,
                        bannerID TEXT,
                        bannerName TEXT,
                        weaponID TEXT,
                        weaponName TEXT,
                        weaponType TEXT,
                        rarity INTEGER,
                        timestamp INTEGER,
                        new INTEGER
                    )
                ''')

                cur.close()
        except Exception as e:
            logging.error('Database error: %s', e)
        finally:
            con.close()

    def get_latest_character_pull_id(self, banner_id):
        banner_type_map = {
            CharacterBannerType.BEGINNER: 'beginner',
            CharacterBannerType.STANDARD: 'standard'
        }

        if banner_id in banner_type_map:
            banner_filter = f'WHERE bannerID = "{banner_type_map[banner_id]}"'
        else:
            banner_filter = 'WHERE bannerID LIKE "special_%"'

        try:
            cur = self._con.cursor()
            cur.execute(f'SELECT id FROM character {banner_filter} ORDER BY id DESC LIMIT 1')
            row = cur.fetchone()
            cur.close()

            if row is None:
                return None
            return row[0]
        except Exception as e:
            logging.error('Database error: %s', e)
            return None

    def get_latest_weapon_pull_id(self):
        try:
            cur = self._con.cursor()
            cur.execute('SELECT id FROM weapon ORDER BY id DESC LIMIT 1')
            row = cur.fetchone()
            cur.close()

            if row is None:
                return None
            return row[0]
        except Exception as e:
            logging.error('Database error: %s', e)
            return None

    def get_character_pulls(self):
        try:
            with self._con as con:
                cur = con.cursor()
                cur.execute('SELECT id, rarity, characterName, bannerID, bannerName, timestamp, new, free FROM character')
                pulls = []
                for row in cur:
                    pulls.append({
                        'id': row[0],
                        'rarity': row[1],
                        'name': row[2],
                        'bannerID': row[3],
                        'bannerName': row[4],
                        'timestamp': row[5],
                        'new': row[6],
                        'free': row[7]
                    })
                cur.close()
                return pulls
        except Exception as e:
            logging.error('Database error: %s', e)
            return []

    def get_weapon_pulls(self):
        try:
            with self._con as con:
                cur = con.cursor()
                cur.execute('SELECT id, rarity, weaponName, bannerID, bannerName, timestamp, new FROM weapon')
                pulls = []
                for row in cur:
                    pulls.append({
                        'id': row[0],
                        'rarity': row[1],
                        'name': row[2],
                        'bannerID': row[3],
                        'bannerName': row[4],
                        'timestamp': row[5],
                        'new': row[6]
                    })
                cur.close()
                return pulls
        except Exception as e:
            logging.error('Database error: %s', e)
            return []

    def insert_character_pulls(self, pulls):
        try:
            with self._con as con:
                cur = con.cursor()
                cur.executemany('INSERT OR IGNORE INTO character VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)', pulls)
                cur.close()
        except Exception as e:
            logging.error('Database error: %s', e)

    def insert_weapon_pulls(self, pulls):
        try:
            with self._con as con:
                cur = con.cursor()
                cur.executemany('INSERT OR IGNORE INTO weapon VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)', pulls)
                cur.close()
        except Exception as e:
            logging.error('Database error: %s', e)
