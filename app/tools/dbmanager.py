# import tkinter as tk
import sqlite3
import logging

class DatabaseManager:
    """Handles all database interactions."""

    def __init__(self, app):
        self.app = app

        self.db = './data/appdata.db'
        self.init_db(self.db)

        self.data = None

    def init_db(self, db):
        """If the db path doesn't exist, create a db with the correct tables."""

        con = sqlite3.connect(db)
        cur = con.cursor()

        logging.info(f'initializing app database: {db}')

        with con:
            # TODO: use ISO8601 string format: "YYYY-MM-DD HH:MM:SS.SSS" on created/modified
            # I think my timestamp constructs already use this.
            cur.execute('''CREATE TABLE if not exists song_meta (
                song_id INTEGER PRIMARY KEY,
                library_id INTEGER,
                title TEXT,
                created TEXT, 
                modified TEXT,
                comments TEXT,
                confidence INTEGER,
                default_key TEXT
                )''')

            cur.execute('''CREATE TABLE if not exists song_data (
                song_id INTEGER,
                pos TEXT,
                flag TEXT,
                content TEXT,
                FOREIGN KEY (song_id) REFERENCES song_meta(song_id)
                )''')

            # TODO: gig metadata
            cur.execute('''CREATE TABLE if not exists gigs (
                gig_id INTEGER PRIMARY KEY,
                name TEXT
                venue TEXT,
                city TEXT,
                gig_date TEXT,
                comments TEXT
                )''')

            cur.execute('''CREATE TABLE if not exists gig_setlists (
                gig_id INTEGER,
                pos INTEGER,
                setlist_id INTEGER,
                FOREIGN KEY(gig_id) REFERENCES gigs(gig_id)
                )''')

            cur.execute('''CREATE TABLE if not exists setlist_songs (
                setlist_id INTEGER,
                pos INTEGER,
                song_id INTEGER,
                previous BOOLEAN,
                current BOOLEAN,
                next_up BOOLEAN,
                skip BOOLEAN,
                strike BOOLEAN
                )''')

            # pool data stores the list of pool songs in each gig_id along
            # with any tags
            cur.execute('''CREATE TABLE if not exists pool_data (
                gig_id INTEGER,
                pos INTEGER,
                song_id INTEGER,
                color TEXT,
                style TEXT
                )''')

            cur.execute('''CREATE TABLE if not exists guest_meta (
                guest_id INTEGER PRIMARY KEY,
                first_name TEXT,
                last_name TEXT,
                instruments TEXT,
                comments TEXT
                )''')

            cur.execute('''CREATE TABLE if not exists gig_guestlists (
                gig_id INTEGER,
                pos INTEGER,
                guest_id INTEGER
                )''')

            # TODO: give setlists their own metadata attributes unique from
            # the gig metadata, but later you can still set preferential
            # inheritance ie. setlist overrides gig or vice versa.
            cur.execute('''CREATE TABLE if not exists setlist_meta (
                setlist_id INTEGER PRIMARY KEY,
                name TEXT,
                venue TEXT,
                city TEXT,
                gig_date TEXT,
                comments TEXT                
                )''')

            cur.execute('''CREATE TABLE if not exists config (
                component TEXT,
                parameter TEXT,
                parameter_pos INTEGER,
                parameter_key TEXT,
                parameter_value TEXT
                )''')

        con.close()

    def get_next_available_id(self, cursor, key, table):
        """Return the next available id for a target parameter."""

        query = f"SELECT MAX({key}) FROM {table}"
        highest_id = cursor.execute(query).fetchall()[0][0]
        logging.info(f'highest_id is: {highest_id}')
        new_id = highest_id + 1 if highest_id != None else 0
        logging.info(f'new {key} generated: {new_id}')

        return new_id

    def get_lowest_available_id(self, cursor, key, table):
        """Find the first unused id in a key."""

        query = f"SELECT {key} FROM {table}"
        fetched =  cursor.execute(query).fetchall()

        if not fetched:
            return

        # extract keys
        keys = []
        for tup in fetched:
            keys.append(tup[0])

        # TODO: perhaps keys are inherently sorted and this is unnecessary?
        keys = keys.sort()
        count = len(keys)

        # initially assign to highest + 1, then try to find lower
        new_id = keys[-1] + 1
        for i in range(count-1):
            new_id = keys[i] + 1 if (keys[i] + 1) != keys[i+1] else new_id

        logging.info(f'returning new song_id {new_id}')

        return new_id

    def add_song_to_db(self, db, song):
        """Add a song to the db"""

        # TODO: keep the song_id with the song obj 
        # so you have the option to dump back into the same cells.

        # connect
        con = sqlite3.connect(db)
        cur = con.cursor()

        logging.info(f'began adding {song.name} to {db}')

        # generate song_id by increasing the largest song_id by 1
        with con:

            # song_id = self.get_next_available_id(cur, 'song_id', 'song_meta')
            song.song_id = self.song_id_strategies(song, cur)
            song.library_id = self.library_id_strategies(song, cur)

            # dump all song text data
            for tup in song.tk_tuples:
                self.dump_tk_tuple_to_db(cur, tup, song.song_id)

            # dump all song metadata
            self.dump_song_meta_to_db(cur, song)

        con.close()

        # return song_id so setlist / pool can track where the song went
        return song.song_id

    def dump_tk_tuple_to_db(self, cur, tup, song_id):
        """Add a tk_tuple to the db."""

        pos, tag, word = tup
        data = (song_id, pos, tag, word)
        query = "INSERT INTO song_data (song_id, pos, flag, content) VALUES (?, ?, ?, ?)"
        cur.execute(query, data)
        # logging.info(f'inserted {data} into song_data')

    def dump_song_meta_to_db(self, cur, song):
        """Dump the song metadata to the db."""

        query = """
                INSERT OR REPLACE INTO song_meta (
                song_id, 
                library_id,
                title,
                created, 
                modified,
                comments,
                confidence,
                default_key
                )

                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """
        cur.execute(
            query,
            (
            song.song_id,
            song.library_id,
            song.name,
            song.created,
            song.modified,
            song.info,
            song.confidence,
            None
            )
            )

    def dump_setlist_to_db(self, setlist):
        """Dump a setlist into the database."""

        db = self.db
        # track song_ids as you dump them
        # so when you dump the setlist it contains references
        song_ids = []

        # first dump all songs into the db, retrieve their ids
        for song in setlist.songs:
            song_ids.append(self.add_song_to_db(db, song))

        # now connect to the db
        con = sqlite3.connect(db)
        cur = con.cursor()

        with con:
            # choose appropriate setlist_id
            setlist_id = self.setlist_id_strategies(setlist, cur)

            # add setlist song pointers to setlist_songs
            # TODO: store previous, current, next_up, skip, strike, etc.

            for i, song_id in enumerate(song_ids):
                query = "INSERT INTO setlist_songs (setlist_id, pos, song_id) VALUES (?, ?, ?)"
                cur.execute(query, (setlist_id, i, song_id))

            # add setlist metadata to setlist_meta
            # TODO: generate gig_meta_id and save gig_metadata
            query = "INSERT INTO setlist_meta (setlist_id, name) VALUES (?, ?)"
            cur.execute(query, (setlist_id, setlist.name))

        con.close()

    # TODO: these follow the same pattern,can be combined probably...

    def dump_pool_to_db(self, pool):
        """Dump a song pool to db. While similar to setlists, pool stores
        different metadata. TODO: Might combine later."""

        db = self.db
        # track song_ids as you dump them
        # so when you dump the setlist it contains references
        song_ids = []

        # first dump all songs into the db, retrieve their ids
        for song in pool.songs:
            song_ids.append(self.add_song_to_db(db, song))

        # now connect to the db
        con = sqlite3.connect(db)
        cur = con.cursor()

        with con:
            # choose appropriate pool_id
            pool_id = self.pool_id_strategies(pool, cur)

            # add setlist song pointers to setlist_songs
            # TODO: store previous, current, next_up, skip, strike, etc.
            for i, song_id in enumerate(song_ids):
                query = "INSERT INTO pool_songs (pool_id, pos, song_id) VALUES (?, ?, ?)"
                cur.execute(query, (pool_id, i, song_id))

            # add setlist metadata to setlist_meta
            # TODO: generate gig_meta_id and save gig_metadata
            query = "INSERT INTO pool_data (pool_id, name) VALUES (?, ?)"
            cur.execute(query, (pool_id, pool.name))

        con.close()

    def pool_id_strategies(self, pool, cursor):
        # TODO: do this. might just be tied directly to gig id.
        return 0

    def setlist_id_strategies(self, setlist, cursor):
        """Return an appropriate setlist_id for storing to database
        based on overwrite settings, whether setlist exists in db already,
        etc."""

        if self.app.settings.library.overwrite_setlists.get():
            if setlist.setlist_id != None:
                return setlist.setlist_id

        return self.get_next_available_id(cursor, 'setlist_id', 'setlist_meta')

    def song_id_strategies(self, song, cursor):
        """Return an appropriate song_id for storing to database
        based on overwrite settings, whether song exists in db already, etc."""

        if self.app.settings.library.overwrite_songs.get():
            if song.song_id != None:
                return song.song_id

        return self.get_next_available_id(cursor, 'song_id', 'song_meta')

    def library_id_strategies(self, song, cursor):
        """Return an appropriate library_id for storing to database
        based on extant song_id."""

        if song.library_id != None:
            logging.info('song already had a library_id, so it was returned')
            return song.library_id

        if song.song_id != None:
            logging.info('song had no library_id, so song_id was assigned')
            return song.song_id

        logging.warning('failed to assign a library_id!')



    def get_all_song_meta_from_db(self):
        """Return all song metadata from db."""

        db = self.app.data.db
        con = sqlite3.connect(db)
        cur = con.cursor()

        with con:

            query = "SELECT * FROM song_meta"
            cur.execute(query)
            data = cur.fetchall()

        con.close()

        logging.info('got all song metadata from db')
        return data

    def get_song_dict_from_db(self, song_id):
        """Construct and return a dictionary for the song from db"""

        # TODO: metadata becomes a misnomer the way this is carried out.

        con = sqlite3.connect(self.db)
        cur = con.cursor()

        with con:

            # extract metadata to dict
            # TODO: create a generic song_dictionary template in tools/song
            # and import here
            song_data = {
                'library_id': None,
                'title': None,
                'created': None,
                'modified': None,
                'comments': None,
                'confidence': None,
                'default_key': None
                }

            for k, v in song_data.items():
                query = f'SELECT {k}  FROM song_meta WHERE song_id="{song_id}"'
                cur.execute(query)
                v = cur.fetchone()
                song_data[k] = v[0] if v != None else v
                # logging.info(f'retrieved {k}:{v} from {song_id}')

            # get the song script
            query = f'SELECT pos, flag, content FROM song_data WHERE song_id="{song_id}"'
            cur.execute(query)
            song_data['tk_tuples'] = cur.fetchall()
            song_data['song_id'] = song_id

        con.close()

        return song_data

