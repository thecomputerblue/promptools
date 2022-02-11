import tkinter as tk
from tkinter import ttk 
import logging

class SongDetailView(tk.Frame):
    """Show and edit song metadata."""

    def __init__(self, parent):
        tk.Frame.__init__(self,
            parent,
            # relief="sunken",
            # borderwidth=2,
            )
        self.app = parent.app
        self.song = parent.song

        # TODO: change to title
        self.header = tk.Label(self, text="SONG DETAILS")
        self.header.grid(row=0, column=0, columnspan=2, sticky="w")

        # TODO: get lock methods etc from setlist.
        self.lock = tk.Label(self, text=u"\U0001F512",)
        # self.lock.bind("<Button-1>", lambda e: self.suite.toggle_lock())
        self.lock.grid(row=0, column=5, sticky="e")

        self.name_label = tk.Label(self, text="title:")
        self.name_label.grid(row=1, column=0, sticky="e")
        # self.name_var = tk.StringVar()
        self.name_entry = tk.Entry(self, width=30,
            # textvariable=self.name_var
            )
        self.name_entry.grid(row=1, column=1, columnspan=5, sticky="ew")

        self.name_entry.bind("<KeyRelease>", lambda *args: self.on_name_edit())

        self.artist_label = tk.Label(self, text="artist:")
        self.artist_label.grid(row=2, column=0, sticky="e")
        self.artist_var = tk.StringVar()
        self.artist_entry = tk.Entry(self)
        self.artist_entry.grid(row=2, column=1, columnspan=5, sticky="ew")

        self.key_label = tk.Label(self, text="key:")
        self.key_label.grid(row=3, column=0, sticky="e")
        self.key_var = tk.StringVar()
        self.key_entry = tk.Entry(self, width=4)
        self.key_entry.grid(row=3, column=1, sticky="w")

        self.duration_label = tk.Label(self, text="time:")
        self.duration_label.grid(row=3, column=2, sticky="e")
        self.duration_var = tk.StringVar()
        self.duration_entry = tk.Entry(self, width=6)
        self.duration_entry.grid(row=3, column=3, columnspan=1, sticky="ew")

        self.confidence_label = tk.Label(self, text="confidence:")
        self.confidence_label.grid(row=3, column=4, sticky="e")
        self.confidence_var = tk.IntVar()
        self.confidence_entry = tk.Entry(self, width=2)
        self.confidence_entry.grid(row=3, column=5, sticky="ew")

        self.genre_label = tk.Label(self, text="genre:")
        self.genre_label.grid(row=4, column=0, sticky="e")
        self.genre_var = tk.StringVar()
        self.genre_entry = tk.Entry(self)
        self.genre_entry.grid(row=4, column=1, columnspan=5, sticky="ew")

        self.link_label = tk.Label(self, text="link:")
        self.link_label.grid(row=5, column=0, sticky="e")
        self.link_var = tk.StringVar()
        self.link_entry = tk.Entry(self)
        self.link_entry.grid(row=5, column=1, columnspan=6, sticky="nesw")


        # TODO: add scrollbar to comments_text
        self.comments_label = tk.Label(self, text="comments:")
        self.comments_label.grid(row=6, column=0, columnspan=2, sticky="w")
        self.comments_var = tk.StringVar()
        self.comments_text = tk.Text(self, width=30, height=10)
        self.comments_text.grid(row=7, column=0, columnspan=6, sticky="nesw")

        self.rowconfigure(7, weight=10)

        # callbacks
        # assign this to a collection's listbox refresh method when you
        # push a song here. will make info instantly update in the list
        # when you make changes. TODO: better method?
        self.refresh_callback = None

        # when you pass in a song from a setlist / pool, pass in that frames
        # listbox refresh and run it whenever you edit title

    def on_name_edit(self):
        self.dump_meta_back_to_song()
        self.refresh_callback() if self.refresh_callback else None

    def push_deck(self):
        """Callback used in main window to get info from cued."""

        # TODO: feels like there's a redundancy here
        self.push(self.app.deck.cued)

    def push(self, song, callback=None):
        """dump old info back to song, push new song, refresh fields."""

        self.dump_meta_back_to_song()
        self.song = song
        self.refresh_callback = None
        self.refresh_song_meta_fields()

    def fill_from_song_dict(self, song_dict):
        """Populate the fields from a song dictionary."""
        # TODO 
        pass

    def refresh_song_meta_fields(self):

        if self.song is None:
            return 

        # (widget, 0 index format, data)
        fields = (
        (self.name_entry, 0, self.song.name),
        (self.key_entry, 0, self.song.key.default),
        (self.confidence_entry, 0, self.song.confidence),
        (self.comments_text, '1.0', self.song.info)
        )

        for f in fields:
            widget, i, data = f
            state = widget.cget("state")
            widget.config(state="normal")
            widget.delete(i, "end")
            widget.insert(i, data) if data != None else None
            widget.config(state=state)

        # update label fields
        # self.created_time.config(text=self.song.created if self.song.created else '')
        # self.modified_time.config(text=self.song.modified if self.song.modified else '')
        # self.opened_time.config(text=self.song.opened if self.song.opened else '')

    def empty(self):
        """When nothing valid is selected, empty the contents."""
        self.dump_meta_back_to_song()
        self.song = None

        # collect fields and labels
        fields = (
            self.name_entry,
            self.artist_entry,
            self.key_entry,
            self.confidence_entry,
            self.genre_entry,
            self.duration_entry,
            self.created_time,
            self.modified_time,
            self.opened_time,
            )

        # clear entry fields and labels
        for field in fields: 
            field.config(text='')

        # Refresh contents TODO: decorator function wrapper
        state = self.text.cget("state")
        self.text.config(state="normal")
        self.text.delete("1.0", "end")
        self.text.config(state=state)

    def dump_meta_back_to_song(self):
        """Dump info back to song obj."""

        if not self.song:
            return

        # put everything you want to dump back here
        # TODO: use the tk.StringVars instead of plain .get
        self.song.name = self.name_entry.get()
        self.song.meta.info = self.comments_text.get('1.0', 'end')
        # self.refresh_callback() if self.refresh_callback else None
