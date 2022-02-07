import tkinter as tk 
import time
import copy
import logging


class EditPoolFrame(tk.Frame):
    """Class for the Edit Pool frame in the left pane of the main window."""

    def __init__(self, parent, *args, **kwargs):
        tk.Frame.__init__(
            self, parent, highlightthickness=2, borderwidth=2, relief="sunken"
        )

        # context
        self.parent = parent
        self.app = parent.app
        self.suite = self

        # pool data & its manager
        self.data = self.app.data.pool
        self.manager = PoolManager(self)

        # expose songs more shallowly
        self.songs = self.data.pool

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

    def clicked_trash(self):
        """Trash any selected songs."""

        logging.info('clicked_trash in EditPoolFrame')

        d = self.data
        m = self.manager

        for sel in self.listbox.curselection():

            # Get the target song object for comparison.
            ind = int(sel)
            target = m.filtered[ind] # !!!This is returning a name, not the song object.

            # find and delete target song
            for i in range(len(d.songs)):
                song = d.songs[i]
                if song is target:
                    logging.info(f'deleting {song.name} from pool')
                    del d.songs[i]
                    break

            # # replaces previous block
            # for song in d.songs:
            #     if song is target:
            #         logging.info(f'deleting {song.name} from pool')
            #         del song
            #         break                    

        self.listbox_update()

    def listbox_update(self):
        
        l = self.listbox
        m = self.manager
        d = self.data

        sel = l.curselection() if l.curselection() else None

        # apply search filter
        self.filter_songs()        

        # Delete previous data.
        l.delete(0, "end")

        # sort filtered in place, create list representation
        m.filtered = sorted(m.filtered, key=lambda song: song.name)
        list_repr = [song.name for song in m.filtered] # key=str.lower
        # logging.info(f'pool list:\n{list_repr})

        # Insert sorted data
        for song in list_repr:
            l.insert("end", song)

        if sel != None:
            l.selection_set(sel)
            l.activate(sel)
            l.selection_anchor(sel)

    def filter_songs(self):
        """Filter song list based on search."""

        d = self.data
        m = self.manager
        search = self.suite.header.search 

        value = search.get().strip().lower()

        # get data from file_list
        if value == "":
            m.filtered = d.songs
        else:
            m.filtered = [] # clear the filtered list

            # TODO: needs to ignore punctuation when filtering
            for song in d.songs:
                m.filtered.append(song) if value in song.name.lower() else None

    def on_listbox_select(self, event):
        """Preview pool song on selection."""

        current = event.widget.curselection()
        self.push_selection_to_preview(current) if current else None

    def push_selection_to_preview(self, current):
        """Push info to infobox, and song obj to preview frame."""
        
        app = self.app
        m = self.manager
        i = current[0]

        song = m.filtered[i] if m.filtered else None
        app.deck.cued = song
        # make the pools update method the refresh callback in song detail,
        # so when you change the song name it is immediately reflected
        # in the playlist
        # TODO: feels hacky
        app.meta.song_detail.refresh_callback = self.listbox_update

class PoolManager:
    """Class for managing the edit pool."""

    def __init__(self, parent):

        # context
        self.parent = parent
        self.app = parent.app
        self.suite = parent.suite
        self.data = parent.data

        # Filtered list of songs so filtered listbox can call the right object.
        self.filtered = []

    def add_song(self, song):
        """Add entry to the pool."""

        logging.info(f'added song to pool {song.name}')
        self.data.songs.append(copy.deepcopy(song))
        self.suite.listbox_update()

    def delete_song(self, target):
        """Delete song from pool."""

        logging.info('delete_song in PoolManager')

        d = self.data

        # Untested!
        for i in range(d.songs):
            if target.name == d.songs[i].name \
            and target.created == d.songs[i].created:
                del d.songs[i]
                break

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

        self.trash = tk.Button(self, text="\u2715", command=self.suite.clicked_trash)
        self.trash.pack(side="left")

        self.undo = tk.Button(self, text="Undo", command=None)
        self.undo.pack(side="left")

        # lock
        self.lock = tk.Label(self, text=u"\U0001F512",)
        self.lock.bind("<Button-1>", lambda e: self.suite.toggle_lock())
        self.lock.pack(side="right")

        # keep all buttons in a list for lock toggle fn
        self.allbuttons = [self.scratch, self.rename, self.trash]


