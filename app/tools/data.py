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

        self.collections = (self.setlist, self.pool)

    def dump_workspace_to_db(self):
        """Dump the workspace to db at program exit."""

        logging.info('dump_workspace_to_db in AppData')

        # TODO:
        # get lowest available gig_id, assign to settings.workspace.workspace_gig_id
        # dump pool songs to db, tracking their song_ids
        # dump pool song_ids list to pool meta with associated workspace_gig_id
        # dump all songs in the setlists
        # dump all gig setlists, tracking their setlist_ids in the order they are in memory
            # before you dump each setlist, dump its songs, tracking their ids
            # dump the setlist with song_ids to setlist_songs
        # dump  the ordered setlist ids to gig_setlists table



    def get_last_workspace_from_db(self):
        """Restore workspace from last session on load."""
        logging.info('get_last_workspace_from_db in AppData')


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