import sqlite3
import logging


class AppData:
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

class Setlist:
    """Hold setlist song references & metadata."""

    # def refresh(method):
    #     return self.parent.refresh(method)

    def __init__(self, parent, d={}, *args, **kwargs):
        self.app = parent.app
        self.parent = parent
        self.title = d.get("title")

        # songs contains songs as they are ordered in this setlist
        self.songs = []
        self.import_songs(d.get("songs"))

        # db pointers
        self.setlist_id = d.get("setlist_id")
        self.library_id = d.get("library_id")

    def refresh(method):
        """Decorator that updates markers and does all callbacks."""

        def inner(self, *args, **kwargs):
            method(self, *args, **kwargs)
            self.parent.update_marks()
            self.parent.do_callbacks()

        return inner

    def import_songs(self, songs: list) -> list:
        """Turns a list of song dicts into a list of song objs."""
        songs = self.app.tools.factory.make_many_songs(songs) if songs else []
        for song in songs:
            self.add(song)

    @refresh
    def add(self, song) -> None:
        if song not in self.songs:
            self.songs.append(song)
        if song not in self.parent.pool.songs:
            self.parent.pool.add(song)

    @refresh
    def move(self, song_i, dest):
        i = min(dest, len(self.songs) - 1)
        self.songs.insert(i, self.songs.pop(song_i))

    @property
    def pool(self):
        return self.gig.pool

    @property
    def names(self):
        """Return names of all songs in the collection."""
        return [song.name for song in self.songs] if self.songs else []

    def remove_song_at_index(self, i: int) -> None:
        """Remove song from the setlist by setlist index."""
        # TODO: clear song metadata from right pane
        song = self.songs[i]
        self.songs.remove(song)


class PoolData: 
    """Simple container for pool."""

    def __init__(self, parent):
        self.app = parent.app
        self.parent = parent
        self.songs = []

    def refresh(method):
        """Decorator that updates markers and does all callbacks."""

        def inner(self, *args, **kwargs):
            method(self, *args, **kwargs)
            self.parent.update_marks()
            self.parent.do_callbacks()

        return inner
    @property
    def names(self):
        return [song.name for song in self.songs] if self.songs else None

    def add(self, song):
        self.songs.append(song)

    def clear(self):
        self.songs.clear()

    def load(self, songs):
        # TODO: optional merge-load
        self.clear()
        songs = self.app.tools.factory.make_many_songs(songs) if songs else []
        for song in songs:
            self.add(song)

    @refresh
    def remove(self,song):
        self.songs.remove(song)


class GigData:
    """Class for holding the workspace data. Pool, setlists, notepad, config."""

    def refresh(method):
        """Decorator that updates markers and does all callbacks."""
        def inner(self, *args, **kwargs):
            method(self, *args, **kwargs)
            self.update_marks()
            self.do_callbacks()
        return inner

    def __init__(self, parent):
        self.app = parent.app
        self.suite = parent
        self.deck.add_callback("live", self.update_marks)
        self.callbacks = {}
        self.helper = self.app.tools.helper

        # TODO: reload old gig
        self.new_gig()

    def new_gig(self):
        """Initialize the gig with fresh collections."""

        self.name = None
        self.setlists = [Setlist(self)]
        self.pool = PoolData(self)
        self.markers = self.default_markers()
        self._live_setlist = 0
        self._gig_id = None

    @refresh
    def clear_gig(self):
        """Clears gig data, but keeps the objects. This should trigger
        any callbacks."""

        # TODO: clear gig metadata
        self.pool.clear()
        self.markers = self.default_markers()
        self.setlists = [Setlist(self)]

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
        # TODO: optional merge-load
        self.clear_gig()
        self.load_from_gig_data_dict(gig_data)

    @refresh
    def load_from_gig_data_dict(self, gig_data):
        """Dump gig_data into the gig object."""
        logging.info("load_from_gig_data_dict in GigData")
        self.load_setlists(gig_data.get("setlists"))
        self.pool.load(gig_data.get("pool"))

    @refresh
    def load_setlists(self, setlists):
        # TODO: load-merge option
        self.setlists = []
        for setlist in setlists:
            self.setlists.append(Setlist(parent=self, d=setlist))

    @property
    def deck(self):
        return self.app.deck

    def add_callback(self, fn, *args, **kwargs):
        self.callbacks[fn] = (args, kwargs)

    def do_callbacks(self):
        """Do any callbacks assigned to the Song Collection."""
        for fn, v in self.callbacks.items():
            fn(*v[0], **v[1]) if v else fn()


    def default_markers(self):
        """Return default marker dict."""
        return {
            "played": [],
            "skipped": [],
            "live": None,
            "previous": None,
            "nextup": None,
        }

    def update_marks(self):
        """Update song markers based on deck."""
        logging.info("update_marks in SetlistCollection")
        self.try_mark("previous", self.deck.previous)
        self.try_mark("live", self.deck.live)
        self.mark_nextup(songs=self.live_setlist.songs)

    def try_mark(self, local, deck):
        """Try to update mark from deck"""

        if deck in self.live_setlist.songs:
            self.markers[local] = deck

    def mark_nextup(self, songs):
        logging.info("mark_nextup in SetlistCollection")
        count = len(songs)
        for i, song in enumerate(songs):
            if song is self.markers.get("live"):
                self.markers["nextup"] = (
                    songs[i + 1] if i < count - 1 else None
                )
                break

    @refresh
    def add_song_to_setlist(self, song):
        """Add a song to the live setlist."""

        if not song:
            return

        if song in self.live_setlist.songs:
            logging.info('song already in live setlist')
            self.helper.popup("song already in live setlist")
            return

        if song not in self.pool.songs:
            self.pool.append(song)

        self.live_setlist.songs.append(song) 

    @refresh
    def add_song_to_pool(self, song):
        """Add song to pool."""
        if not song or song in self.pool.songs:
            self.helper.popup("song already in pool!")
            return

        self.pool.add(song)

    def song_already_in_setlist(self, song):
        """Check if a song is already in the setlist."""

        # TODO: currently comparing names, reconsider in future.
        if self.live_setlist.names is not None and song.name in names:
            self.helper.popup("song already in setlist!")
            return True

    def toggle_mark(self, param, song):
        """Toggle a song within a marker list."""
        l = self.markers[param]
        l.remove(song) if song in l else l.append(song)

    @refresh
    def remove_orphans(self, pool, setlists):
        """Clear all songs from pool without setlist references."""
        for song in pool:
            pool.remove(song) if self.check_orphan(song, setlists) else None

    def check_orphan(self, song, setlists):
        """Return True if song is not in any setlist."""
        # TODO: utility function, maybe move to tools
        orphaned = True
        for setlist in setlists:
            if song in setlist.songs:
                orphaned = False
        return orphaned

    @property
    def live_setlist(self):
        """Return the live setlist, or generte an empty one if none exist."""
        self.setlists.append(Setlist(self)) if not self.setlists else None

        return self.setlists[self._live_setlist]

    @live_setlist.setter
    def live_setlist(self, new: int):
        self._live_setlist = new if new < len(self.setlists)-1 else 0
