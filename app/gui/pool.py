import tkinter as tk 
from tkinter import ttk
import time
import copy
import logging
import string

from tools.apppointers import AppPointers

# helpers
def scrub_text(text):
    """Remove text formatting for search comparison."""
    text = text.strip().lower()
    text = text.translate(str.maketrans('', '', string.punctuation))
    return text

def alphabetize_songs(songs):
    return sorted(songs, key=lambda song: song.name)

class PoolAndSetlistsNotebook(ttk.Notebook, AppPointers):
    """Two pages for song pool and setlists respectively."""

    def __init__(self, parent, *args, **kwargs):
        ttk.Notebook.__init__(self, parent,
            padding=0
            )
        AppPointers.__init__(self, parent)

        self.pool_and_setlists = PoolAndSetlistsFrame(self)
        self.pool_and_setlists.pack(fill="both", expand=True)
        self.add(self.pool_and_setlists, text="Song Pool")

        self.setlist_page = SetlistPage(self)
        self.setlist_page.pack(fill="both", expand=True)
        self.add(self.setlist_page, text="Setlists")

    def sync(self):
        self.pool_and_setlists.sync()
        self.setlist_page.sync()

class SetlistPage(tk.Frame, AppPointers):
    """Page for gig setlists."""

    def __init__(self, parent, *args, **kwargs):
        tk.Frame.__init__(
            self, parent, highlightthickness=2, borderwidth=2, relief="sunken"
        )        
        AppPointers.__init__(self, parent)

        self.dummy = tk.Label(self, text='implement setlists')
        self.dummy.pack()

    def sync(self):
        pass


class PoolAndSetlistsFrame(tk.Frame, AppPointers):
    """Pane for showing the gig song pool and setlists."""

    def __init__(self, parent, *args, **kwargs):
        tk.Frame.__init__(
            self, parent, highlightthickness=2, borderwidth=2, relief="sunken"
        )
        AppPointers.__init__(self, parent)
        self.suite = self

        # subframes
        self.header = PoolHeader(self)
        self.header.pack(side="top", anchor="w", expand=False)

        self.controls = PoolControlRow(self)
        self.controls.pack(side="top", fill="both", expand=False)

        # shows contents of pool
        self.listbox = tk.Listbox(
            self,
            width=40,
            bg="lightgrey",
            fg="black",
            exportselection=False
            )
        # self.listbox.grid(row=2, columnspan=4, sticky="nesw")
        self.listbox.pack(side="top", fill="both", expand=True)
        self.listbox.bind("<<ListboxSelect>>", self.on_listbox_select)
            #listvariable=self.contents

        # expose some things for ease
        self.search = self.header.search
        self.query = self.header.query

        # deck callback
        self.deck.add_callback("live", self.listbox_update)
        self.gig.add_callback(self.listbox_update)

        # refresh once to show anything that was loaded at init.
        # self.listbox_update()

        # make strategies for updating listbox
        # TODO: implement colors
        # self.make_listbox_strategies()

    # TODO: better approach than a bunch of properties?

    def sync(self): 
        self.listbox_update()

    @property
    def pool(self):
        return self.gig.pool
    
    @property
    def markers(self):
        return self.gig.markers

    @property
    def live(self):
        return self.gig.live_setlist

    @property
    def songs(self):
        """Filter gig songs by pool search and return as an alphabetized list."""
        songs = alphabetize_songs(self.filter_songs_by_query(self.pool.songs))
        return songs

    @property
    def names(self):
        return [song.name for song in self.songs]
    
    def filter_songs_by_query(self, songs):
        """Filter song list by search contents."""
        query = scrub_text(self.query.get())
        if not songs or not query:
            return songs
        out = []
        for song in songs:
            if query in scrub_text(song.name):
                out.append(song)
        return out
    
    def do_sel(self, sel):
        """Clear and apply new target listbox selection."""
        l = self.listbox
        l.selection_clear(0, "end")
        l.selection_set(sel) if sel < l.size() else l.selection_set("end")
        l.activate(sel)

    def preserve_sel(method):
        """Capture then restore listbox selection after executing inner method"""

        def inner(self, *args, **kwargs):

            sel = self.get_sel()
            method(self, sel, *args, **kwargs)
            self.do_sel(sel) if sel is not None else None

        return inner

    def pass_sel(method):
        """Capture listbox selection and do decorated function only
        if there is a selection."""

        def inner(self, *args, **kwargs):
            sel = self.get_sel()
            if sel is None:
                return
            method(self, sel, *args, **kwargs)

        return inner

    def get_sel(self):
        """Get selection index."""

        sel = self.listbox.curselection()
        return sel[0] if sel else None

    def right_click(self, event):
        """When right clicking in listbox, update selection and bring up context options."""

        l = self.listbox
        sel = l.nearest(event.y)
        self.do_sel(sel)
        self.menu.do_popup(event, sel)

    @preserve_sel
    def mark_nextup(self, sel, *args, **kwargs):
        """Mark the selected song as next up."""
        self.markers['nextup'] = self.live.songs[sel]
        self.listbox_update()

    @preserve_sel
    def on_remove(self, sel, *args, **kwargs):
        """Remove selected song."""
        if sel is None:
            return
        self.try_delete(i=sel)
        self.listbox_update()

    @preserve_sel
    def try_undo(self, sel, *args, **kwargs):
        logging.info('try_undo in PoolAndSetlistsFrame')

    @preserve_sel
    def try_add(self, sel, *args, **kwargs):
        logging.info('try_add in PoolAndSetlistsFrame')

    @preserve_sel
    def on_duplicate(self, sel, *args, **kwargs):
        logging.info('on_duplicate in PoolAndSetlistsFrame')

    @pass_sel
    def move(self, sel, target: str or int):
        """Move song within list."""

        dest = self.target_to_i(start_i=sel, target=target)
        self.data.move_song(self.live, sel, dest)
        self.listbox_update()
        self.do_sel(dest)

    def target_to_i(self, start_i, target):
        """Convert a listbox target to an index."""

        if target == "top":
            return 0
        elif target == "end":
            return -1
        new = start_i + target
        return new if new >=0 else 0

    @pass_sel
    def on_toggle(self, sel, mark):
        """Toggle a songs presence within a marker list."""
        self.data.toggle_mark(mark, self.songs[sel])
        self.listbox_update()

    @pass_sel
    def on_listbox_select(self, sel, event):
        self.push_song_to_preview(self.songs, sel) if sel is not None else None

    def try_delete(self, i):
        """Delete song at index if its not in a setlist."""
        # TODO: if it is in a setlist, raise a dialog box.
        song = self.songs[i]
        if self.check_orphan(song, self.gig.setlists):
            self.pool.remove(song)

    def check_orphan(self, song, setlists) -> bool:
        """Return True if song is orphaned (not in the list of setlists)."""
        for setlist in setlists:
            if song in setlist.songs:
                self.helper.popup("Can't delete a song from the pool that is in a setlist!")
                return False
        return True 

    def push_song_to_preview(self, songs, i):
        """Push info to infobox, and song obj to preview frame."""

        # TODO: this method will not work if you implement search
        # TODO: think of a way to automate this refresh callback
        self.deck.cued = songs[i] if songs else None
        self.gui.meta.song_detail.refresh_callback = self.listbox_update

    def make_listbox_strategies(self):
        """Define strategies for formatting listbox items."""

        # TODO: clunky...
        # TODO: update with pool parameters...
        colors = self.settings.colors
        l = self.listbox

        self.listbox_strategies = {
            lambda song: self.song_is_skipped(song): lambda i: l.itemconfig(i, bg=colors.skipped),
            lambda song: self.song_is_nextup(song): lambda i: l.itemconfig(i, bg=colors.nextup),
            lambda song: self.song_is_previous(song): lambda i: l.itemconfig(i, bg=colors.previous),
            lambda song: self.song_is_live(song): lambda i: l.itemconfig(i, bg=colors.live),
        }

    # TODO: hmmm
    def song_is_skipped(self, song):
        return song in self.markers.get('skipped') if self.markers.get('skipped') else False

    def song_is_nextup(self, song):
        return song is self.markers.get('nextup')

    def song_is_live(self, song):
        return song is self.markers.get('live')

    def song_is_previous(self, song):
        return song is self.markers.get('previous')

    @preserve_sel
    def listbox_update(self, sel=None):

        self.listbox.delete(0, "end")

        songs = self.songs
        if not songs:
            return

        logging.info(f'listbox_update names: {self.names}')
        for i, name in enumerate(self.names):
            name = strike(name) if songs[i] in self.markers.get('played') else name
            self.listbox.insert("end", name)
            # TODO: implement color_item for pool
            # self.color_item(i)

    def color_item(self, i:int) -> None:
        """Apply appropriate color to a listbox item."""

        logging.info('color_item in SetlistFrame')
        for k, v in self.listbox_strategies.items():
            if k(self.songs[i]):
                v(i)
                logging.info('color applied!')
                break

    def add_to_listbox(self, item: str):
        self.listbox.insert("end", item)


class PoolHeader(tk.Frame, AppPointers):
    """Class for the Pool header & searchbar."""

    def __init__(self, parent):
        tk.Frame.__init__(self, parent)
        AppPointers.__init__(self, parent)

        # label
        self.label = tk.Label(self, text="Search")
        self.label.pack(side="left", anchor="w", )

        # filter pool by search
        self.query = tk.StringVar()
        self.search = tk.Entry(self, textvariable=self.query)
        self.search.pack(side="left", anchor="w", expand=True, fill="both")
        # self.search.bind("<KeyRelease>", lambda _: self.suite.listbox_update())
        self.query.trace("w", lambda *args: self.suite.listbox_update())

        # clear search
        self.clear = tk.Button(self, text="Clear", command=lambda *args: self.search.delete(0, 'end'))
        self.clear.pack(side="right", anchor="e")


class PoolControlRow(tk.Frame, AppPointers):
    """Row for the setlist buttons for moving entries around."""

    def __init__(self, parent):
        tk.Frame.__init__(self, parent)
        AppPointers.__init__(self, parent)
  
        # cross out played song
        self.add = tk.Button(self, text="+", command=self.suite.try_add)
        self.add.pack(side="left")

        self.duplicate = tk.Button(self, text="\u2397", command=self.suite.on_duplicate)
        self.duplicate.pack(side="left")

        self.trash = tk.Button(self, text="\u2715", command=self.suite.on_remove)
        self.trash.pack(side="left")

        self.undo = tk.Button(self, text="Undo", command=self.suite.try_undo)
        self.undo.pack(side="left")

        # lock
        self.locked = tk.BooleanVar()
        self.lock = tk.Label(self)
        self.lock.bind("<Button-1>", lambda e: self.gui.toggle_lock(var=self.locked, label=self.lock))
        # toggle to init TODO: hacky?
        # self.gui.toggle_lock(var=self.locked, label=self.lock) 
        self.lock.pack(side="right")

        # keep all buttons in a list for lock toggle fn
        self.allbuttons = [self.add, self.duplicate, self.trash, self.undo]