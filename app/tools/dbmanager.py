import sqlite3
import logging
from contextlib import contextmanager

# helpers
@contextmanager
def open_db(file_name: str):
    """Conext manager for sqlite3 connections."""
    connection = sqlite3.connect(file_name)
    try:
        yield connection.cursor()
    finally:
        connection.commit()
        connection.close()
    # TODO: if an exception occurs, maybe rollback instead of committing...

def lowest_unused(l: list) -> int:
    """Return lowest int that doesn't appear in a list."""

    l.sort()
    last = len(l) - 1
    logging.info(f"lowest unused recieved: {l}")

    for i, curr in enumerate(l):
        if i == last:
            return l[-1] + 1
        elif new := curr + 1 != l[i + 1]:
            return new

def sql_q_marks(n):
    """Return '(?, ?, ... ?)' with n '?' marks. Used for SQLite VALUES."""
    return "(" + ", ".join(["?"] * n) + ")"


class DatabaseManager:
    """Handles all database interactions."""

    def __init__(self, app):
        self.app = app
        self.settings = self.app.settings.library
        self.init_db(self.db)
        self.gen_db_defaults(self.db)

    @property
    def db(self):
        return self.app.settings.paths.db.get()
    
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

    def gen_db_defaults(self, db):
        """Create any default entries needed for the app to work expectedly.
        For example, gig_id 0 should always exist as a placeholder for workspace,
        so if it doesn't generate it. Without doing so, A gig save operation
        could lead to a gig in slot 0, which would be overwritten by
        a workspace save."""

        logging.info(f"generating db defaults: {db}")
        with open_db(self.db) as cur:

            # generate gig_id 0 for workspace in gigs
            # TODO: can probably reduce this to a readable one-liner
            cur.execute("SELECT * FROM gigs WHERE gig_id==0")
            workspace = cur.fetchone()
            if workspace is None:
                cur.execute(
                    "INSERT INTO gigs (gig_id, name) VALUES (?, ?)", (0, "workspace")
                )
                logging.info("gen_db_defaults generated workspace gig_id placeholder")

    def choose_id(self, cur, key, table):
        """Choose the an unused id for a given db key.
        Currently finds lowest available. If table is empty, starts at 0."""

        logging.info(f"choose_id in DatabaseManager")
        query = f"SELECT {key} FROM {table}"
        fetched = cur.execute(query).fetchall()
        return lowest_unused([tup[0] for tup in fetched]) if fetched else 0

    def dump_gig(self, gig, workspace=False):
        """Dump the workspace back to db,
        either as a gig or to workspace slot."""

        self.assign_gig_id(gig)
        store_id = 0 if workspace else gig.gig_id

        self.dump_pool(store_id)
        self.dump_gig_setlists(store_id)
        self.dump_gig_meta(store_id)

    def dump_gig_meta(self, store_id):
        """Dump the gig metadata."""

        # TODO: replace with dict dump
        logging.info(f"dumping gig metadata")
        name = self.app.data.gig.name
        with open_db(self.db) as cur:
            cur.execute("DELETE FROM gigs WHERE gig_id=?", (store_id,))
            cur.execute(
                "INSERT INTO gigs (gig_id, name) VALUES (?, ?)", (store_id, name)
            )

    def dump_dict_to_row(self, cur, table, d):
        """Dump a dict back into a table row."""

        # TODO: could potentially end up with mismatched k,v order with this method
        # TODO: too clever, there is defintely a better way to do this
        k, v = ", ".join(d.keys()), tuple(d.values())
        q = f"INSERT OR REPLACE INTO {table} ({k}) VALUES {sql_q_marks(len(d))}"
        cur.execute(q, v)

    def dump_pool(self, gig_id):
        """Dump pool songs, then their ids into pool_data."""

        self.dump_songs(self.app.data.pool.songs)
        pool_ids = [song.song_id for song in self.app.data.pool.songs]
        self.dump_pool_ids(gig_id=gig_id, pool_ids=pool_ids)

    def dump_pool_ids(self, gig_id, pool_ids):
        """Dump pool_ids to the db."""

        with open_db(self.db) as cur:
            for i, p in enumerate(pool_ids):
                query = "INSERT INTO pool_data (gig_id, pos, song_id) VALUES (?, ?, ?)"
                cur.execute(query, (gig_id, i, p))

    def load_gig(self, gig_id):
        """Construct gig dictionary from db,
        pass to data module for unpacking."""

        self.app.data.gig.load_gig(self.make_gig_dict(gig_id))

    def make_gig_dict(self, gig_id):
        """Make a dict with gig_id."""

        return {
            "gig_metadata": self.load_gig_metadata(gig_id),
            "setlists": self.load_gig_setlists(gig_id),
            "pool": self.load_gig_pool(gig_id)
        }

    def load_gig_pool(self, gig_id):
        pool_song_ids = self.get_pool_song_ids(gig_id)
        return self.load_many_songs(pool_song_ids)

    def get_pool_song_ids(self, gig_id):
        # TODO: nearly identical function to get_gig_setlist_ids
        with open_db(self.db) as cur:
            cur.execute("SELECT song_id FROM pool_data WHERE gig_id=?", (gig_id,))
            sel = cur.fetchall()
            return sel[0] if sel else None

    def load_gig_metadata(self, gig_id: int) -> dict:
        """Return dict of gig metadata from db."""
        return self.row_to_dict("gigs", "gig_id", gig_id)

    def row_to_dict(self, table: str, row: str, value: str or int) -> dict:
        """Return dict of a single row of a table
        where key is the column header."""
        with open_db(self.db) as cur:
            query = f"SELECT * from {table} WHERE {row}=?"
            cur.execute(query, (value,))
            k = [c[0] for c in cur.description] if cur.description else []
            d = cur.fetchall()
            v = d[0] if d else []
            return dict(zip(k, v))

    def get_gig_setlist_ids(self, gig_id):
        with open_db(self.db) as cur:
            cur.execute("SELECT setlist_id FROM gig_setlists WHERE gig_id=?", (gig_id,))
            sel = cur.fetchall()
            return sel[0] if sel is not None else None

    def load_gig_setlists(self, gig_id) -> list:
        """Return list of setlists for a gig_id."""

        sids = self.get_gig_setlist_ids(gig_id)
        if sids is None:
            return []

        setlists = []
        for sid in sids:
            setlists.append(self.load_setlist(sid))
        return setlists

    def load_setlist(self, setlist_id):
        setlist = {}
        # TODO: retrieve + apply metadata
        setlist["songs"] = self.load_many_songs(self.get_sl_song_ids(setlist_id))

        return setlist

    def get_sl_song_ids(self, setlist_id):
        """Return list of song_ids for a setlist_id."""
        logging.info(f'get_sl_song_ids recieved setlist_id: {setlist_id}')
        with open_db(self.db) as cur:
            cur.execute(
                "SELECT song_id FROM setlist_songs WHERE setlist_id=? ORDER BY pos",
                (setlist_id,),
            )
            return list(zip(*cur.fetchall()))[0]

    def load_many_songs(self, song_ids):
        """Return an ordered list of song dicts from provided song_ids."""
        if not song_ids:
            return []
        songs = []
        logging.info(f'load_many_songs recieved song_ids: {song_ids}')
        for song_id in song_ids:
            songs.append(self.load_song(song_id))
        return songs

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

    def temp_song_dict(self, song):
        """TEMP FUNCTION TO MAKE A SONG METADATA DICT"""
        return {
            "song_id": song.song_id,
            "library_id": song.library_id,
            "title": song.name,
            "created": song.created,
            "modified": song.modified,
            "comments": song.info,
            "confidence": song.confidence,
            "default_key": None,
        }

    def dump_song_meta(self, d, cur):
        """Replaces dump_song_meta"""

        # TODO: once song is updated to store metadata in a dict,
        # you can pass that in and delete this line, which generates
        # a dict from the song obj.
        song_meta = self.temp_song_dict(d)
        self.dump_dict_to_row(cur, "song_meta", song_meta)

    def dump_gig_setlists(self, gig_id):
        """Dump ALL the open setlists."""
        setlists = self.app.data.setlists
        self.dump_setlists(setlists)
        self.dump_gig_setlist_ids([s.setlist_id for s in setlists], gig_id)

    def dump_setlists(self, setlists):
        for setlist in setlists:
            self.dump_setlist(setlist)

    def dump_gig_setlist_ids(self, setlist_ids, gig_id):
        """Track which setlists are associated with the gig."""
        logging.info("dump_gig_setlist_ids")
        with open_db(self.db) as cur:
            for i, s in enumerate(setlist_ids):
                query = "INSERT INTO gig_setlists (gig_id, pos, setlist_id) VALUES (?, ?, ?)"
                logging.info(
                    f"inserted into gig_setlists gig_id:{gig_id}, pos:{i}, setlist_id: {s}"
                )
                cur.execute(query, (gig_id, i, s))

    def dump_setlist(self, setlist, dump_songs=False):
        """Dump a single setlist. Pass dump_songs=True if you want
        to dump setlists songs. This is False by default because
        dump_gig_setlists dumps the entire setlist pool at once, and
        re-dumping would be redundant."""

        self.dump_songs(setlist.songs) if dump_songs else None

        with open_db(self.db) as cur:
            self.assign_setlist_id(setlist, cur)
            self.dump_song_ids_to_setlist_songs(
                self.get_song_ids(setlist), setlist.setlist_id, cur
            )
            self.dump_setlist_metadata(setlist, cur)

    def get_song_ids(self, setlist):
        """Get all song ids from setlist."""

        # TODO: generate song id if it doesn't exist?
        song_ids = []
        for song in setlist.songs:
            song_ids.append(song.song_id)
        return song_ids

    def dump_songs(self, songs: list):
        """Dump all songs from setlist."""
        print(f'SONGS---->{songs}')
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

    def assign_setlist_id(self, setlist, cur):
        """Assign an appropriate setlist_id for storing to database
        based on overwrite settings, whether setlist exists in db already,
        etc."""

        if self.settings.overwrite_setlists.get():
            if setlist.setlist_id is not None:
                return
        setlist.setlist_id = self.choose_id(cur, "setlist_id", "setlist_meta")

    def assign_gig_id(self, gig):
        """Return an appropriate gig_id for storing to database."""

        with open_db(self.db) as cur:
            if gig.gig_id is None:
                gig.gig_id = self.choose_id(cur, "gig_id", "gigs")
        # TODO: overwrite setting (see assign_setlist_id)

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

        logging.info(f"library_id_stategies \n song_id: {song.song_id}")

        if song.library_id is not None:
            logging.info("song already had a library_id, so it was returned")
            return song.library_id
        elif song.song_id is not None:
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
            return cur.fetchall()

    def make_song_dict_from_db(self, song_id):
        """Construct and return a dictionary for the song from db"""
        song_data = self.get_song_metadata(song_id)
        song_data["tk_tuples"] = self.get_song_script(song_id)
        return song_data

    def load_song(self, song_id):
        return self.make_song_dict_from_db(song_id)

    def get_song_metadata(self, song_id):
        """Pull everything from the metadata table for the given song_id
        and return a dictionary."""
        return self.row_to_dict("song_meta", "song_id", song_id)

    def get_song_script(self, song_id):
        """Return song script as list of tuples."""
        with open_db(self.db) as cur:
            # TODO: sort!!!
            cur.execute(
                "SELECT pos, flag, content FROM song_data WHERE song_id=?", (song_id,)
            )
            script = cur.fetchall()
        return script
