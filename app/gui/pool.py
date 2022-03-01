import tkinter as tk 
from tkinter import ttk
import time
import copy
import logging

class PoolAndSetlistsNotebook(ttk.Notebook):
    """Two pages for song pool and setlists respectively."""

    def __init__(self, parent, *args, **kwargs):
        ttk.Notebook.__init__(self, parent,
            padding=0
            )

        # context
        self.parent = parent
        self.app = parent.app
        self.suite = self

        self.pool = PoolAndSetlistsFrame(self)
        self.pool.pack(fill="both", expand=True)
        self.add(self.pool, text="Song Pool")

        self.setlists = SetlistPage(self)
        self.setlists.pack(fill="both", expand=True)
        self.add(self.setlists, text="Setlists")

class SetlistPage(tk.Frame):
    """Page for gig setlists."""

    def __init__(self, parent, *args, **kwargs):
        tk.Frame.__init__(
            self, parent, highlightthickness=2, borderwidth=2, relief="sunken"
        )        

        # context
        self.parent = parent
        self.app = parent.app
        self.suite = self

        self.dummy = tk.Label(self, text='implement setlists')
        self.dummy.pack()


class PoolAndSetlistsFrame(tk.Frame):
    """Pane for showing the gig song pool and setlists."""

    def __init__(self, parent, *args, **kwargs):
        tk.Frame.__init__(
            self, parent, highlightthickness=2, borderwidth=2, relief="sunken"
        )

        # context
        self.parent = parent
        self.app = parent.app
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

        # callback for refreshing on db activity
        self.data.callback = self

        # deck callback
        self.deck.add_callback("live", self.listbox_update)
        self.data.add_callback(self.listbox_update)

        # make strategies for updating listbox
        # TODO: implement colors
        # self.make_listbox_strategies()

    # TODO: better method than a bunch of properties?
    @property
    def data(self):
        return self.app.data.pool

    @property
    def deck(self):
        return self.app.deck

    @property
    def pool(self):
        return self.data.pool
    
    @property
    def markers(self):
        return self.data.markers

    @property
    def live(self):
        return self.data.live

    @property
    def songs(self):
        return self.live.songs
    
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
        self.live.remove_song_at_index(i=sel)
        self.listbox_update()

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
        """What to do when clicking an item in the setlist."""
        self.push_song_to_preview(sel) if sel is not None else None

    def push_song_to_preview(self, i):
        """Push info to infobox, and song obj to preview frame."""

        # TODO: this method will not work if you implement search
        # TODO: think of a way to automate this refresh callback
        self.deck.cued = self.songs[i] if self.songs else None
        self.app.meta.song_detail.refresh_callback = self.listbox_update

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
        """Update listbox contents and formatting."""

        self.listbox.delete(0, "end")
        if not self.live.songs:
            return

        logging.info(f'listbox_update names: {self.live.names}')
        for i, name in enumerate(self.live.names):
            name = strike(name) if self.songs[i] in self.markers.get('played') else name
            # name = number(i+1, name)
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


# class PoolManager:
#     """Class for managing the edit pool."""

#     def __init__(self, parent):

#         # context
#         self.parent = parent
#         self.app = parent.app
#         self.suite = parent.suite
#         self.data = parent.data

#         # Filtered list of songs so filtered listbox can call the right object.
#         self.filtered = []

#     def add_song(self, song):
#         """Add entry to the pool."""

#         logging.info(f'added song to pool {song.name}')
#         self.data.pool.append(copy.deepcopy(song))
#         self.suite.listbox_update()

#     def delete_song(self, target):
#         """Delete song from pool."""

#         logging.info('delete_song in PoolManager')

#         pool = self.data.pool

#         for song in pool:
#             if target.name == song.name \
#             and target.created == song.created:
#                 del pool.song
#                 break

class PoolHeader(tk.Frame):
    """Class for the Pool header & searchbar."""

    def __init__(self, parent):
        tk.Frame.__init__(self, parent)

        self.suite = parent.suite

        # label
        self.label = tk.Label(self, text="Pool | Search:")
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


class PoolControlRow(tk.Frame):
    """Row for the setlist buttons for moving entries around."""

    def __init__(self, parent):
        tk.Frame.__init__(self, parent)

        # context
        self.parent = parent
        self.app = parent.app
        self.suite = parent
  
        # cross out played song
        self.scratch = tk.Button(self, text="Scratch", command=None)
        self.scratch.pack(side="left")

        # cross out played song
        self.rename = tk.Button(self, text="Rename", command=None)
        self.rename.pack(side="left")

        self.trash = tk.Button(self, text="\u2715", command=self.suite.on_remove)
        self.trash.pack(side="left")

        self.undo = tk.Button(self, text="Undo", command=None)
        self.undo.pack(side="left")

        # lock
        self.lock = tk.Label(self, text=u"\U0001F512",)
        self.lock.bind("<Button-1>", lambda e: self.suite.toggle_lock())
        self.lock.pack(side="right")

        # keep all buttons in a list for lock toggle fn
        self.allbuttons = [self.scratch, self.rename, self.trash]


