import tkinter as tk
from tkinter import ttk
import sqlite3
import logging

from gui.songdetail import SongDetailView
from tools.apppointers import AppPointers

class LibraryWindow(tk.Toplevel, AppPointers):
    """Class for the window for configuring program preferences."""

    def __init__(self, parent, *args, **kwargs):
        tk.Toplevel.__init__(self, parent.frame)
        AppPointers.__init__(self, parent)

        self.title("Library Manager")

        # raise flag that window is open
        self.settings.windows.library.set(True)

        # default window size
        win_w = 1200
        win_h = 500
        self.geometry(f'{str(win_w)}x{str(win_h)}')

        # TODO: stop window resizing
        # self.resizable(width=False, height=False)

        # always popup in center of operator window
        x = int(self.app.winfo_screenwidth()/2 - win_w/2)
        y = int(self.app.winfo_screenheight()/2 - win_h/2)
        self.geometry(f'+{x}+{y}')

        # destroy method 
        self.protocol("WM_DELETE_WINDOW",self.quit_window)

        self.notebook = LibraryNotebook(self)

    def quit_window(self):
        """When you close window, update the flag."""

        self.settings.windows.library.set(False)
        self.destroy()

class LibraryNotebook(ttk.Notebook, AppPointers):
    """ttk notebook for managing several preference tabs."""

    def __init__(self, parent):
        ttk.Notebook.__init__(self, parent)
        AppPointers.__init__(self, parent)

        self.app = parent.app
        
        # tabs
        song_browser = SongBrowser(self)
        song_browser.pack(fill="both", expand=True)
        self.add(song_browser, text='Songs')

        setlist_browser = SetlistBrowser(self)
        setlist_browser.pack(fill="both", expand=True)
        self.add(setlist_browser, text='Setlists')

        pool_browser = PoolBrowser(self)
        pool_browser.pack(fill="both", expand=True)
        self.add(pool_browser, text='Pools')

        gig_browser = GigBrowser(self)
        gig_browser.pack(fill="both", expand=True)
        self.add(gig_browser, text='Gigs')

        lib_settings = LibrarySettings(self)
        lib_settings.pack(fill="both", expand=True)
        self.add(lib_settings, text='Settings')

        # pack frame 
        self.pack(fill="both", expand=True)

class SongBrowser(tk.PanedWindow, AppPointers):
    """Class for the Song Browser tab."""

    def __init__(self, parent):
        tk.PanedWindow.__init__(self, parent, orient="horizontal", sashwidth=10)
        AppPointers.__init__(self, parent)

        self.song = None

        self._data = None
        self.data = self.tools.dbmanager.get_all_song_meta_from_db()

        # widgets
        self.top = SongViewTop(self)
        self.top.pack(side="top", fill="both", expand=True)

        self.bottom = SongViewBottom(self)
        self.bottom.pack(side="top", fill="both")

        # expose tree to rest of browser
        self.tree = self.top.tree


    def handle_click(self, event):
        if self.tree.identify_region(event.x, event.y) == "separator":
            return "break"
   

class SongViewTop(tk.Frame, AppPointers):
    """Top half of the song browser, which contains the treview and info."""

    def __init__(self, parent):
        tk.Frame.__init__(self, parent,
            # old PanedWindow params
            # orient="horizontal", sashwidth=10
            )
        AppPointers.__init__(self, parent)

        self.data = parent.data
        self.song = parent.song

        # make sure to assign to self!!!
        self.treeview = SongTreeFrame(self)
        self.tree = self.treeview.tree

        # dump library into tree
        for i, meta in enumerate(self.data):
            song_id, lib_id, name, created, modified, comments, confidence, def_key = meta
            ordered = [song_id, lib_id, name, created, modified, confidence, def_key, comments]
            self.tree.insert(parent='', index="end", iid=i, values=ordered)

        # infobox (right side)
        self.songdetail = SongDetailView(self)

        self.treeview.pack(side="left", expand=True, fill="both")
        self.songdetail.pack(side="right", fill="y")


class SongLibraryFilters(tk.Frame, AppPointers):
    """Class for song library filters"""

    def __init__(self, parent):
        tk.Frame.__init__(self, parent)
        AppPointers.__init__(self, parent)

        self.include_header = tk.Label(self, text="Include:")
        self.include_header.pack(side="left", anchor="w")
        self.show_library = tk.Checkbutton(self, text="Library")
        self.show_library.pack(side="left", anchor="w")
        self.show_setlist_songs = tk.Checkbutton(self, text="Setlists")
        self.show_setlist_songs.pack(side="left", anchor="w")
        self.show_pool_songs = tk.Checkbutton(self, text="Pools")
        self.show_pool_songs.pack(side="left", anchor="w")             
        self.show_orphans = tk.Checkbutton(self, text="Orphans")
        self.show_orphans.pack(side="left", anchor="w")

        # TODO: show frozen? want a way to set aside orphaned songs
        # so they're not deleted when you clean up


class SongTreeFrame(tk.Frame, AppPointers):
    """Class for the treeview and its scrollbar."""

    def __init__(self, parent):
        tk.Frame.__init__(self, parent)
        AppPointers.__init__(self, parent)

        self.library_filters = SongLibraryFilters(self)
        self.library_filters.pack(side="top", fill="both")

        self.scrolled_tree = ScrolledSongTree(self)
        self.scrolled_tree.pack(side="top", fill="both", expand=True)
        self.tree = self.scrolled_tree.tree

        self.search = SearchBar(self)
        self.search.pack(side="top", fill="both")

        self.search_filters = SearchFilters(self)
        self.search_filters.pack(side="top", fill="both")


class SearchBar(tk.Frame, AppPointers):
    """Class for the Pool header & searchbar."""

    def __init__(self, parent):
        tk.Frame.__init__(self, parent)
        AppPointers.__init__(self, parent)

        # label
        self.label = tk.Label(self, text="Search:")
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

class SearchFilters(tk.Frame, AppPointers):
    """Row of search filters."""

    def __init__(self, parent):
        tk.Frame.__init__(self, parent)
        AppPointers.__init__(self, parent)

        self.target_label = tk.Label(self, text="Targets:")
        self.target_label.pack(side="left", anchor="w")

        self.song_title = tk.Checkbutton(self, text="Title")
        self.song_title.pack(side="left", anchor="w")

        self.song_artist = tk.Checkbutton(self, text="Artist")
        self.song_artist.pack(side="left", anchor="w")

        self.song_key = tk.Checkbutton(self, text="Key")
        self.song_key.pack(side="left", anchor="w")

        self.song_genre = tk.Checkbutton(self, text="Genre")
        self.song_genre.pack(side="left", anchor="w")

        self.comments = tk.Checkbutton(self, text="Comments")
        self.comments.pack(side="left", anchor="w")

        self.confidence = tk.Checkbutton(self, text="Confidence")
        self.confidence.pack(side="left", anchor="w")

        self.gig = tk.Checkbutton(self, text="Gig")
        self.gig.pack(side="left", anchor="w")

        self.toggle_all = tk.Button(self, text="Toggle All")
        self.toggle_all.pack(side="left", anchor="w")


class ScrolledSongTree(tk.Frame, AppPointers):
    """Attach a scrollbar to treeview."""

    def __init__(self, parent):
        tk.Frame.__init__(self, parent)
        AppPointers.__init__(self, parent)

        self._song_dict = None

        # library data tree (left side of frame)
        tree = ttk.Treeview(self, selectmode="browse")
        tree['columns']=("song_id", "lib_id", "name", "created", "modified", "confidence", "default key", "comments")
        
        tree.column("#0", width=0, stretch=False)
        tree.column("song_id", anchor="center", width=5)
        tree.column("lib_id", anchor="center", width=5)
        tree.column("name", anchor="w", width=200)
        tree.column("created", anchor="w", width=60)
        tree.column("modified", anchor="w", width=60)
        tree.column("confidence", anchor="center", width=5)
        tree.column("default key", anchor="center", width=5)
        tree.column("comments", anchor="w", width=100)

        tree.heading("#0", text='', anchor="center")
        tree.heading("song_id", text="song_id", anchor="center")
        tree.heading("lib_id", text="lib_id", anchor="center")
        tree.heading("name", text="name", anchor="w")
        tree.heading("created", text="created", anchor="center")
        tree.heading("modified", text="modified", anchor="center")
        tree.heading("confidence", text="confidence", anchor="center")
        tree.heading("default key", text="default key", anchor="center")
        tree.heading("comments", text="comments", anchor="center")

        tree.pack(side="left", fill="both", expand=True)
        self.tree = tree

        self.scrollbar = ttk.Scrollbar(self, orient="vertical")
        self.scrollbar.config(command=self.tree.yview)
        self.tree.configure(yscrollcommand=self.scrollbar.set)
        self.scrollbar.pack(side="left", fill="y")

        self.tree.bind("<<TreeviewSelect>>", self.on_tree_select)

    def on_tree_select(self, event):
        """Retrieve the selected song data to a dict."""

        # get the selected row id
        sel = self.tree.focus()
        # get the song id of the selected row
        song_id = self.tree.set(sel, column="song_id")

        # retrieve and assign dict of the song, triggering callbacks
        song_dict = self.app.tools.dbmanager.make_song_dict_from_db(song_id=song_id)

        song = self.app.tools.factory.new_song(dictionary=song_dict)
        print(f'SONG CREATED IN ON_TREE_SELECT: {song.name}')

        self.suite.top.songdetail.push(song)

        # if cue_selection in library settings, push to cue.
        if self.app.settings.library.cue_selection.get():
            self.app.deck.cued = song

class SongViewBottom(tk.Frame, AppPointers):
    """Bottom half of the song browser, which contains misc options."""

    def __init__(self, parent):
        tk.Frame.__init__(self,
            parent,
            relief="sunken",
            borderwidth=2,
            # highlightbackground="light grey",
            # highlightthickness=2
            )
        AppPointers.__init__(self, parent)

        self.data = parent.data
        self.song = parent.song

        self.cue_selection = tk.Checkbutton(
            self,
            text="Cue selected song for playback",
            variable=self.app.settings.library.cue_selection
            )

        self.cue_selection.pack(side="left", anchor="w")


class SetlistBrowser(tk.Frame, AppPointers):
    """Class for the Import/Export Settings tab."""

    def __init__(self, parent):
        tk.Frame.__init__(self, parent)
        AppPointers.__init__(self, parent)

        # widgets
        self.setlists = tk.Listbox(
            self,
            bg="lightgrey",
            fg="black",
            exportselection=False)
        self.setlists.pack(side='left', fill='both', expand=True)


class PoolBrowser(tk.Frame, AppPointers):
    """Class for the Import/Export Settings tab."""

    def __init__(self, parent):
        tk.Frame.__init__(self, parent)
        AppPointers.__init__(self, parent)

        # widgets 
        self.pools = tk.Listbox(
            self,
            bg="lightgrey",
            fg="black",
            exportselection=False)
        self.pools.pack(side='left', fill='both', expand=True)

        self.scrollbar = tk.Scrollbar(self, orient="vertical")
        self.scrollbar.pack(side="right", fill="y")

class GigBrowser(tk.Frame, AppPointers):
    """Class for the Import/Export Settings tab."""

    def __init__(self, parent):
        tk.Frame.__init__(self, parent)
        AppPointers.__init__(self, parent)

        self.app = parent.app
        self.settings = parent.app.settings

        # widgets 
        self.gigs = tk.Listbox(
            self,
            bg="lightgrey",
            fg="black",
            exportselection=False)
        self.gigs.pack(side='left', fill='both', expand=True)

        self.scrollbar = tk.Scrollbar(self, orient="vertical")
        self.scrollbar.pack(side="right", fill="y")

class LibrarySettings(tk.Frame, AppPointers):
    """Class for defining Library behaviors. Settings also reproduced in
    the preferences window."""

    def __init__(self, parent):
        tk.Frame.__init__(self, parent)
        AppPointers.__init__(self, parent)

        # options
        self.keep_local = tk.Checkbutton(
            self,
            text="Keep Local Song Versions In Setlists / Pools (Strongly Recommended)",
            # variable=self.settings. TODO
            )
        self.keep_local.pack(side="top", anchor="w")
        
        self.use_lib = tk.Checkbutton(
            self,
            text="Use Library Song Versions When Available")
        self.use_lib.pack(side="top", anchor="w")

        self.use_library_desc = tk.Label(
            self, 
            text="If a Library version of a song exists,\
            load that instead of the local version. ")
        self.use_library_desc.pack(side="top", anchor="w")


"""
resources...
stop resizing of columns:
https://stackoverflow.com/questions/45358408/how-to-disable-manual-resizing-of-tkinters-treeview-column
"""

