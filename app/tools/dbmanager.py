# import tkinter as tk
import sqlite3
import logging
from contextlib import contextmanager

# helpers
@contextmanager
def open_db(file_name: str):
    """Conext manager for sqlite3 connections."""
    connection = sqlite3.connect(file_name)
    try:
        cursor = connection.cursor()
        yield cursor
    finally:
        connection.commit()
        connection.close()

def lowest_unused(l: list) -> int:
    """Return lowest int that doesn't appear in a list."""

    l.sort()
    last = len(l) - 1
    logging.info(f'lowest unused recieved: {l}')

    for i, cur in enumerate(l):
        if i == last:
            return l[-1] + 1
        elif new := cur + 1 != l[i + 1]:
            return new


class DatabaseManager:
    """Handles all database interactions."""

    def __init__(self, app):
        self.app = app

        self.db = "./data/appdata.db"
        self.init_db(self.db)
        self.settings = self.app.settings.library

    def init_db(self, db):
        """If the db path doesn't exist, create a db with the correct tables."""

        logging.info(f"initializing app database: {db}")
        with open_db(self.db) as cur:
            # TODO: use ISO8601 string format: "YYYY-MM-DD HH:MM:SS.SSS" on created/modified
            # I think my timestamp constructs already use this.
            cur.execute(
                """CREATE TABLE if not exists song_meta (
                song_id INTEGER PRIMARY KEY,
                library_id INTEGER,
                title TEXT,
                created TEXT, 
                modified TEXT,
                comments TEXT,
                confidence INTEGER,
                default_key TEXT
                )"""
            )

            cur.execute(
                """CREATE TABLE if not exists song_data (
                song_id INTEGER,
                pos TEXT,
                flag TEXT,
                content TEXT,
                FOREIGN KEY (song_id) REFERENCES song_meta(song_id)
                )"""
            )

            # TODO: gig metadata
            cur.execute(
                """CREATE TABLE if not exists gigs (
                gig_id INTEGER PRIMARY KEY,
                name TEXT
                venue TEXT,
                city TEXT,
                gig_date TEXT,
                comments TEXT
                )"""
            )

            cur.execute(
                """CREATE TABLE if not exists gig_setlists (
                gig_id INTEGER,
                pos INTEGER,
                setlist_id INTEGER,
                FOREIGN KEY(gig_id) REFERENCES gigs(gig_id)
                )"""
            )

            cur.execute(
                """CREATE TABLE if not exists setlist_songs (
                setlist_id INTEGER,
                pos INTEGER,
                song_id INTEGER,
                previous BOOLEAN,
                current BOOLEAN,
                next_up BOOLEAN,
                skip BOOLEAN,
                strike BOOLEAN
                )"""
            )

            # pool data stores the list of pool songs in each gig_id along
            # with any tags
            cur.execute(
                """CREATE TABLE if not exists pool_data (
                gig_id INTEGER,
                pos INTEGER,
                song_id INTEGER,
                color TEXT,
                style TEXT
                )"""
            )

            cur.execute(
                """CREATE TABLE if not exists guest_meta (
                guest_id INTEGER PRIMARY KEY,
                first_name TEXT,
                last_name TEXT,
                instruments TEXT,
                comments TEXT
                )"""
            )

            cur.execute(
                """CREATE TABLE if not exists gig_guestlists (
                gig_id INTEGER,
                pos INTEGER,
                guest_id INTEGER
                )"""
            )

            # TODO: give setlists their own metadata attributes unique from
            # the gig metadata, but later you can still set preferential
            # inheritance ie. setlist overrides gig or vice versa.
            cur.execute(
                """CREATE TABLE if not exists setlist_meta (
                setlist_id INTEGER PRIMARY KEY,
                name TEXT,
                venue TEXT,
                city TEXT,
                gig_date TEXT,
                comments TEXT                
                )"""
            )

            cur.execute(
                """CREATE TABLE if not exists config (
                component TEXT,
                parameter TEXT,
                parameter_pos INTEGER,
                parameter_key TEXT,
                parameter_value TEXT
                )"""
            )

    def choose_id(self, cur, key, table):
        """Choose the an unused id for a given db key.
        Currently finds lowest available. If table is empty, starts at 0."""

        logging.info(f"choose_id in DatabaseManager")

        query = f"SELECT {key} FROM {table}"
        fetched = cur.execute(query).fetchall()

        return lowest_unused([tup[0] for tup in fetched]) if fetched else 0

    def dump_gig(self, gig):
        """Dump the workspace ('gig') to db."""

        logging.info('dump_gig in DatabaseManager')

        if not gig:
            return

        # TODO:
        # get lowest available gig_id, assign to settings.workspace.workspace_gig_id
        gig_id = self.choose_gig_id(gig)
        # remember gig_id TODO: this should only assign when saving workspace
        self.app.settings.workspace.workspace_gig_id.set(gig_id)

        # dump pool songs to db, tracking their song_ids
        self.dump_songs(self.app.data.pool.pool)
        # dump pool song_ids list to pool meta with associated workspace_gig_id
        pool_ids = [song.song_id for song in self.app.data.pool.pool]
        self.dump_pool_ids(gig_id=gig_id, pool_ids=pool_ids)
        # dump setlists
        self.dump_setlists(self.app.data.setlists, gig_id)

    def dump_pool_ids(self, gig_id, pool_ids):
        """Dump pool_ids to the db."""
        with open_db(self.db) as cur:
            for i, p in enumerate(pool_ids):
                query = "INSERT INTO pool_data (gig_id, pos, song_id) VALUES (?, ?, ?)"
                cur.execute(query, (gig_id, i, p))

    def get_gig(self, gig_id):
        """Retrieve workspace ('gig') from db."""
        pass

    def dump_song(self, song):
        """Dump a song to the db."""

        logging.info(f"began adding {song.name} to {self.db}")

        with open_db(self.db) as cur:
            self.assign_song_ids(song, cur)
            self.dump_song_script(song, cur)
            self.dump_song_meta(song, cur)

    def assign_song_ids(self, song, cur):
        """Assigns id tags to the song if they don't exist."""

        song.song_id = self.song_id_strategies(song, cur)
        song.library_id = self.library_id_strategies(song, cur)

    def dump_song_script(self, song, cur):
        """Dump song script to db."""

        for tup in song.tk_tuples:
            self.dump_script_tuple(cur, tup, song.song_id)

    def dump_script_tuple(self, cur, tup, song_id):
        """Dump the song script (a list of tuples) to the db."""

        pos, tag, word = tup
        data = (song_id, pos, tag, word)
        query = (
            "INSERT INTO song_data (song_id, pos, flag, content) VALUES (?, ?, ?, ?)"
        )
        cur.execute(query, data)

    def dump_song_meta(self, song, cur):
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
                None,
            ),
        )

    def dump_setlists(self, collection, gig_id):
        """Dump ALL the open setlists."""
        slists = collection.setlists
        pool = collection.pool

        self.dump_songs(pool)

        with open_db(self.db) as cur:
            # dump setlists and songs
            for i, s in enumerate(slists):
                s.setlist_id = self.choose_setlist_id(s, cur)
                song_ids = self.get_song_ids(s)
                self.dump_song_ids_to_setlist_songs(song_ids, s.setlist_id, cur)
                self.dump_setlist_metadata(s, cur)
            
            # dump gig references to setlists
            setlist_ids = [s.setlist_id for s in slists]
        
        self.dump_gig_setlist_ids(setlist_ids, gig_id)

    def dump_gig_setlist_ids(self, setlist_ids, gig_id):
        with open_db(self.db) as cur:
            for i, s in enumerate(setlist_ids):
                query = "INSERT INTO gig_setlists (gig_id, pos, setlist_id) VALUES (?, ?, ?)"
                cur.execute(query, (gig_id, i, s))

    def dump_setlist(self, setlist):
        """Dump a SINGLE setlist to the db."""

        self.dump_songs(setlist.songs)

        with open_db(self.db) as cur:
            # choose appropriate setlist_id
            setlist.setlist_id = self.choose_setlist_id(setlist, cur)
            song_ids = self.get_song_ids(setlist)
            self.dump_song_ids_to_setlist_songs(song_ids, setlist.setlist_id, cur)
            self.dump_setlist_metadata(setlist, cur)
            # TODO: store previous, current, next_up, skip, strike, etc.

    def get_song_ids(self, setlist):
        """Get all song ids from setlist."""

        song_ids = []

        for song in setlist.songs:
            song_ids.append(song.song_id)

        return song_ids

    def dump_songs(self, songs):
        """Dump all songs from setlist."""

        for song in songs:
            self.dump_song(song)

    def dump_song_ids_to_setlist_songs(self, song_ids, setlist_id, cur):
        """Dump song_ids and pos info to setlist_songs. This allows setlists
        to be restored with correct references in the correct order."""

        for i, song_id in enumerate(song_ids):
            query = (
                "INSERT INTO setlist_songs (setlist_id, pos, song_id) VALUES (?, ?, ?)"
            )
            cur.execute(query, (setlist_id, i, song_id))

    def dump_setlist_metadata(self, setlist, cur):
        """Dump setlist metadata to table."""

        # TODO: additional metadata
        query = "INSERT INTO setlist_meta (setlist_id, name) VALUES (?, ?)"
        cur.execute(query, (setlist.setlist_id, setlist.title))

    def choose_setlist_id(self, setlist, cur):
        """Return an appropriate setlist_id for storing to database
        based on overwrite settings, whether setlist exists in db already,
        etc."""

        if self.settings.overwrite_setlists.get():
            if setlist.setlist_id is not None:
                return setlist.setlist_id

        return self.choose_id(cur, "setlist_id", "setlist_meta")

    def choose_gig_id(self, gig):
        """Return an appropriate gig_id for storing to database."""      
        with open_db(self.db) as cur:
            if gig.gig_id is not None:
                new = gig.gig_id
            else:
                new = self.choose_id(cur, "gig_id", "gigs")

        return new
        # TODO: overwrite setting (see choose_setlist_id)  

    def song_id_strategies(self, song, cur):
        """Return an appropriate song_id for storing to database
        based on overwrite settings, whether song exists in db already, etc."""

        if self.settings.overwrite_songs.get():
            if song.song_id is not None:
                return song.song_id

        return self.choose_id(cur, "song_id", "song_meta")

    def library_id_strategies(self, song, cursor):
        """Return an appropriate library_id for storing to database
        based on extant song_id."""

        logging.info(f'library_id_stategies \n song_id: {song.song_id}')

        if song.library_id is not None:
            logging.info("song already had a library_id, so it was returned")
            return song.library_id

        if song.song_id is not None:
            logging.info("song had no library_id, so song_id was assigned")
            return song.song_id

        logging.warning("failed to assign a library_id!")

    def get_all_song_meta_from_db(self, option="all"):
        """Return ALL song metadata from db by default. Option to filter to
        library versions ('library'), or alternate versions ('alternates')."""

        options = {
            "library": "SELECT * FROM song_meta WHERE song_id == library_id",
            "alternates": "SELECT * FROM song_meta WHERE song_id != library_id",
            "all": "SELECT * FROM song_meta",
        }

        with open_db(self.db) as cur:
            cur.execute(options.get(option))
            data = cur.fetchall()

        return data

    def make_song_dict_from_db(self, song_id):
        """Construct and return a dictionary for the song from db"""

        with open_db(self.db) as cur:
            # extract metadata to dict
            # TODO: create a generic song_dictionary template in tools/song
            # and import here
            song_data = {
                "library_id": None,
                "title": None,
                "created": None,
                "modified": None,
                "comments": None,
                "confidence": None,
                "default_key": None,
            }

            # TODO: sloppy
            self.get_song_metadata(song_data, song_id, cur)
            song_data["tk_tuples"] = self.get_script(song_id, cur)
            song_data["song_id"] = song_id

        return song_data

    def get_song_metadata(self, song_data, song_id, cur):
        """Get song metadata from db and add to song_data dict."""

        for k, v in song_data.items():
            query = f'SELECT {k}  FROM song_meta WHERE song_id="{song_id}"'
            cur.execute(query)
            v = cur.fetchone()
            song_data[k] = v[0] if v is not None else v
            # logging.info(f'retrieved {k}:{v} from {song_id}')

    def get_script(self, song_id, cur):
        """Return song script as list of tuples."""

        query = (
            f'SELECT pos, flag, content FROM song_data WHERE song_id="{song_id}"'
        )
        cur.execute(query)

        return cur.fetchall()
