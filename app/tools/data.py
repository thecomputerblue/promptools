import sqlite3
import logging

class AppData():
    """Class for app data used in saving and recalling workspace, settings."""

    def __init__(self, app):
        self.app = app
        self.dbmanager = app.tools.dbmanager
        self.deck = app.deck
        self.gig = GigData(self)

    @property
    def setlists(self):
        return self.gig.setlists

    @property
    def pool(self):
        return self.gig.pool

    @property
    def db(self):
        return self.app.settings.paths.db.get()


class SongCollection:
    """Generic class for containing a list of songs."""

    def __init__(self, app, name=None):
        # TODO: on init, attempt to load previous.

        # name collection
        self.app = app
        self.name = name
        self.pool = []
        self.markers = self.default_markers()

        self.callbacks = {}

    def clear_collection_songs(self):
        """Delete all songs in the collection."""

        self.pool.clear()
        self.do_callbacks()

    def default_markers(self):
        """Return default markers"""
        return {}

    @property
    def names(self):
        """Return names of all songs in the collection."""

        return [song.name for song in self.pool] if self.pool else None

    def add_callback(self, fn, *args, **kwargs):
        self.callbacks[fn] = (args, kwargs)

    def do_callbacks(self):
        """Do any callbacks assigned to the Song Collection."""
        for fn, v in self.callbacks.items():
            fn(*v[0], **v[1]) if v else fn()

    def clear_all(self):
        """Clear everything, then refresh via callbacks."""
        self.clear_data()
        self.do_callbacks()

    def clear_data(self):
        """Clear song list. In child classes you'll want to redefine this."""
        self.pool.clear()
        self.markers = self.default_markers()


class SetlistCollection(SongCollection):
    """Holds a song pool, and a list of Setlist versions that reference the song pool."""

    def __init__(self, app):
        SongCollection.__init__(self, app)
        # TODO: on init, attempt to load previous from db.

        self.setlists = [Setlist(self)]
        self.deck = self.app.deck

        self.deck.add_callback('live', self.update_marks)

    def refresh(method):
        """Decorator that updates markers and does all callbacks."""
        def inner(self, *args, **kwargs):
            method(self, *args, **kwargs)
            self.update_marks()
            self.do_callbacks()
        return inner

    def clear_markers(self):
        self.markers = self.default_markers()

    def default_markers(self):
        """Return default marker dict."""
        return {
        'played': [],
        'skipped': [],
        'live': None,
        'previous': None,
        'nextup': None
        }

    def update_marks(self):
        """Update song markers based on deck."""
        logging.info('update_marks in SetlistCollection')
        self.try_mark('previous', self.deck.previous)
        self.try_mark('live', self.deck.live)
        self.mark_nextup()

    def try_mark(self, local, deck):
        """Try to update mark from deck"""

        if deck in self.live.songs:
            self.markers[local] = deck

    def mark_nextup(self):
        logging.info('mark_nextup in SetlistCollection')
        count = len(self.live.songs)
        for i, song in enumerate(self.live.songs):
            if song is self.markers.get('live'):
                self.markers['nextup'] = self.live.songs[i+1] if i < count-1 else None
                break

    @refresh
    def add_song(self, song):
        """Add a song to the live setlist."""

        if not song or self.song_already_in_setlist(song):
            return
        self.pool.append(song)
        self.live.songs.append(song) # TODO: live add method that auto-appends to pool?

    def song_already_in_setlist(self, song):
        """Check if a song is already in the setlist."""

        # TODO: currently comparing names, reconsider in future.
        names = self.live.names
        if names is not None and song.name in names:
            logging.info('same named song already in setlist!')
            return True

    def add_live(self):
        """Add the live song to the setlist."""

        self.add_song(self.deck.live)

    def toggle_mark(self, param, song):
        """Toggle a song within a marker list."""
        l = self.markers[param]
        l.remove(song) if song in l else l.append(song)

    @refresh
    def move_song(self, setlist, song_i, dest):
        """Move song within a setlist."""
        i = min(dest, len(setlist.songs)-1)
        setlist.songs.insert(i, setlist.songs.pop(song_i))

    def remove_song_if_orphaned(self, song):
        """If a song no longer exists in any of the setlists,
        remove it from the pool."""
        for setlist in self.setlists:
            if song in setlist.songs:
                return
        self.pool.remove(song)

    def clear_data(self):
        """Clear all songs in all setlists, markers, etc."""
        logging.info('clear_data in SetlistCollection')
        self.clear_markers()
        self.clear_setlists()
        self.clear_songs()

    def clear_setlists(self):
        """Clears setlists."""
        # TODO: for whatever reason, .clear is not eliminating the original
        # setlist obj. figure this out....
        # self.setlists.clear()
        self.setlists = []

    def clear_songs(self):
        self.pool.clear()

    def add_setlist(self, setlist):
        """Add setlist, trigger callbacks."""
        self.setlists.append(setlist)
        # self.do_callbacks()

    @property
    def live(self):
        """Return the live setlist, or generate an empty one if none exist."""
        self.setlists.append(Setlist(self)) if not self.setlists else None
        # logging.info(f'fetched live setlist {[song.name for song in self.setlists[0].songs]}')
        logging.info(f'ALL SETLISTS: {[s for s in self.setlists]}')
        return self.setlists[0]

class Setlist:
    """Class for a setlist."""

    def __init__(self, parent, d={}, *args, **kwargs):
        self.app = parent.app
        self.parent = parent
        self.title = d.get('title')

        # songs contains songs as they are ordered in this setlist
        self.songs = []
        self.get_songs(d.get('songs'))

        # db pointers
        self.setlist_id = d.get('setlist_id') 
        self.library_id = d.get('library_id')

    def get_songs(self, songs: list) -> list:
        """Turns a list of song dicts into a list of song objs."""
        songs = self.app.tools.factory.make_many_songs(songs) if songs else []
        for song in songs:
            self.add_song(song)

    def add_song(self, song) -> None:
        self.songs.append(song)
        self.pool.append(song)

    @property
    def pool(self):
        return self.parent.pool
    
    @property
    def names(self):
        """Return names of all songs in the collection."""
        return [song.name for song in self.songs] if self.songs else []

    def remove_song_at_index(self, i:int) -> None:
        """Remove song from the setlist by setlist index, 
        and also pool if it has no other references."""
        # TODO: if deleted song is currently in song info, clear the song info
        # achieve with listeners within song? more comprehensive callback manager?
        song = self.songs[i]
        self.songs.remove(song)
        self.parent.remove_song_if_orphaned(song)


class GigData:
    """Class for holding the workspace data. Pool, setlists, notepad, config."""

    def __init__(self, parent):
        self.app = parent.app
        self.suite = parent

        self.new_gig()

    def new_gig(self):
        """Initialize the gig with fresh collections."""
        self.name = None
        self.setlists = SetlistCollection(self.app)
        self.pool = SongCollection(self.app, name='pool')
        self._gig_id = None

    def clear_gig(self):
        """Clears gig data, but keeps the objects. This should trigger
        any callbacks."""
        self.setlists.clear_all()
        self.pool.clear_all()

    @property
    def gig_id(self):
        return self._gig_id

    @gig_id.setter
    def gig_id(self, new):
        self._gig_id = new
        if new != 0:
            self.app.settings.workspace.last_gig_id.set(new)

    def load_gig(self, gig_data):
        """Load gig into program from dictionary"""
        self.clear_gig()
        self.load_from_gig_data_dict(gig_data)

    def load_from_gig_data_dict(self, gig_data):
        """Dump gig_data into the gig object."""
        logging.info('load_from_gig_data_dict in GigData')
        self.load_setlists(gig_data.get('setlists'))

    def load_setlists(self, setlists):
        self.setlists.setlists = []
        for setlist in setlists:
            self.setlists.add_setlist(Setlist(parent=self.setlists, d=setlist))
        self.setlists.do_callbacks()


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