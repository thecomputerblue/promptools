import tkinter as tk
import sqlite3
import logging


class AppData():
    """Class for app data used in saving and recalling workspace, settings."""

    def __init__(self, app):
        self.app = app

        # local ref to db manager
        self.dbmanager = app.tools.dbmanager
        # connect the dbmanager 
        self.dbmanager.data = self
        self.db = app.settings.paths.db.get()

        # init workspace collections
        self.workspace = WorkspaceData(self)
        self.setlist = self.workspace.get_active_setlist()
        self.pool = self.workspace.pool

        self.collections = [self.setlist, self.pool]

    def dump_all_collections_to_db(self):
        for collection in self.collections:
            self.dump_collection_to_db(collection)

    def reload_all_collections_from_db(self):
        for collection in self.collections:
            self.reload_collection_from_db(collection)

    def dump_collection_to_db(self, collection):
        """Dump a song collection into the database."""
        # identify if collection is pool or setlist and call the appropriate dbmanager method.
        c = collection
        m = self.dbmanager
        
        m.dump_pool_to_db(c) if c.name == "pool" else m.dump_setlist_to_db(c)

    def reload_collection_from_db(self, collection):
        """Reload a collection from the db, overwriting whatever collection is in memory."""

        # get the song factory
        factory = self.app.tools.factory

        # connect to db
        db = self.db
        con = sqlite3.connect(db)
        cur = con.cursor()

        # prove there is something in the db
        # TODO: maybe use this with con formulation for other methods.
        with con:
            cur.execute("SELECT * FROM songs")
            logging.info(f'all songs in db: {cur.fetchall()}')

            query = "SELECT name FROM sqlite_master WHERE type='table';"
            cur.execute(query)


        # retrieval method
        # - clear out active collections
        self.clear_collections()

        # - get all song_ids from songs table as a list.
        with con:

            # get song_ids
            cur.execute("SELECT song_id FROM songs")
            song_ids = cur.fetchall()

            # reconstruct each song from stored data
            for current in song_ids:
                logging.info(f'extracting data from {current}')
                # get collection data
                # TODO: mutiple select isn't working, not sure why.

                cur.execute("SELECT * FROM songs WHERE song_id = ?;", current)
                # print(cur.fetchall())[0]
                song_id, collection, collection_index = cur.fetchall()[0]

                # get metadata
                cur.execute("SELECT * FROM songs_meta WHERE song_id = ?;", current)
                # print(cur.fetchall())[0]
                song_id, song_name, created, modified, confidence, song_info = cur.fetchall()[0]

                # get song contents
                tk_tuples = []
                query = f"SELECT * FROM {current[0]}"
                cur.execute(query)
                for row in cur.fetchall():
                    tk_tuples.append(row)

                # reconstruct song object and put it in the correct collection.
                # first need to make a way to ingest meta info into a song object.
                meta = factory.new_meta(name=song_name, info=song_info, confidence=confidence)
                song = factory.new_song(formatted_tuples=tk_tuples, meta=meta)
                # TODO: REST OF METADATA. probably want to rework the entire song factory, tbh. it is a mess.
                # TODO: make sure order is preserved. only incidentally preserved now, maybe.
                logging.info(f'appending to collection: {collection}')
                exec(f'self.{collection}.songs.append(song)')

            # update all the list representations when finished 
            for collection in self.collections:
                collection.refresh_list()

    def clear_collections(self):
        """Clear current contents of setlist / pool / additional active collections."""

        # clear collections
        for collection in self.collections:
            # clears and refreshes associated listbox
            collection.clear_collection_songs()


class SongCollection:
    """Generic class for containing a list of songs."""

    def __init__(self, name=None):
        # TODO: on init, attempt to load previous.

        # name collection
        self.name = name
        self.songs = []
        self.callback = None

    def clear_collection_songs(self):
        """Delete all songs in the collection."""

        self.songs.clear()
        self.refresh_list()

    def refresh_list(self):
        """Refresh the list representation if it has been assigned via callback."""

        self.callback.listbox_update() if self.callback else None

    @property
    def names(self):
        """Return names of all songs in the collection."""

        return [song.name for song in self.songs] if self.songs else None

    @property
    def numbered(self, style=lambda i: " (" + str(i) + ") "):
        """Return songs with numbers."""
        
        # TODO: move the (#) formatting to settings so you can change it everywhere.
        return [style(i) + song.name for i, song in enumerate(self.songs)] if self.songs else None
        # TODO: old, delete
        # return [style(i) + self.songs[i].name for i in range(len(self.songs))] if self.songs else None

class SetlistCollection(SongCollection):
    """Generic class for holding collection of songs, as is setlist, pool."""

    def __init__(self, name=None):
        SongCollection.__init__(name)
        # TODO: on init, attempt to load previous.

        self.pointers = SetlistPointers(self)

        # library pointers. TODO: maybe rename to collection_id
        self.setlist_id = None
        self.library_id = None
   
class PoolCollection(SongCollection):
    """Song collection with properties specific to pool."""

    def __init__(self, name=None):
        SongCollection.__init__(name)

        self.pointers = PoolPointers(self)

        # library pointers. TODO: maybe rename to collection_id
        self.pool_id = None
        self.library_id = None


class SetlistPointers:
    """Class for pointers used to determine visualization
    in a song list and play behavior."""

    def __init__(self, setlist):
        self.setlist = setlist
        self.songs = setlist.songs

        self.skipped = []
        self.played = []

        self.nextup = None
        self.current = None 
        self.previous = None

class SetlistMetadata:
    """Class for storing setlist metadata."""

    def __init__(self, setlist):
        self.setlist = setlist
        self.songs = setlist.songs 

        self.title = tk.StringVar()
        self.city = tk.StringVar()
        self.venue = tk.StringVar()
        self.date = tk.StringVar()

        # put the  schedule in here, fetch from it as needed.
        self.schedule = {}

        # guest performers {name: {guest_metadata}}
        self.guests = {}

        # other acts (openers generally) {name: time}
        self.other_acts = {}

        # most important dict! {meal: time}
        # extract this from sechedule
        # self.meals = {}

class PoolPointers:
    """Class for pointers used to determine visualization
    in a song list and play behavior."""

    def __init__(self, pool):
        self.pool = pool
        self.songs = setlist.songs

        # TODO: define pointers.

class WorkspaceData:
    """Class for holding the workspace data. Pool, setlists, notepad, config."""

    def __init__(self, app):
        self.app = app

        # hold all workspace setlists
        self.setlists = []
        # index of live setlist
        self.live_setlist = 0

        self.pool = SongCollection(name='pool')

        # TODO: import last loaded setlists and pool from db.
        # for now just put a song collection in.
        self.setlists.append(SongCollection(name='setlist'))

    def get_active_setlist(self):
        """Return the active setlist."""

        return self.setlists[self.live_setlist]




"""
SQLITE RESOURCES:

SCRUB table name strings: https://stackoverflow.com/questions/3247183/variable-table-name-in-sqlite

LINK TABLES: https://www.sqlitetutorial.net/sqlite-python/create-tables/
INSERT PYTHON VARS INTO SQLITE: https://stackoverflow.com/questions/19759349/how-to-insert-variable-into-sqlite-database-in-python
LINKING TABLES: https://stackoverflow.com/questions/46754674/linking-tables-in-sqlite-3-in-python
check documentation to get this running:
https://docs.python.org/3/library/sqlite3.html
suggestion on storing tuples:
https://stackoverflow.com/questions/5260095/saving-tuples-as-blob-data-types-in-sqlite3-in-python
BLOB data:
https://pynative.com/python-sqlite-blob-insert-and-retrieve-digital-data/#h-what-is-blob
i think songs will be stored as 2 tables each,
one for the contents (columns for the parts of the tuple),
and one for the song metadata. the metadata table will have a column that indicates the name of the song table.

still need to learn how sqlite dbs are sturctured, but i think it will be like... each song COLLECTION is a table.
the table contains columns for all the song metadata, and a column that points to the name of the table with the song tktuple data.
above the level of the COLLECTION will be another table that defines the different collections in each part of the program (setlist, pool)
and pointers for those respective tables.
another level higher we can point to the tables for GIG metadata alongside the COLLECTIONS. hopefully this
makes sense with the way SQL works. will research tomorrow.
FOREIGN KEYS, PRIMARY KEYS? 
    https://www.sqlitetutorial.net/sqlite-foreign-key/
    https://sqlite.org/forum/info/7c4fe04f2546ed2a
link tables: https://dba.stackexchange.com/questions/21929/how-to-link-data-from-a-table-to-another-table-in-sqlite-database
"""