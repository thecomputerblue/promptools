# shows gig details. TODO: rename this file and update references.
# more importantly, implement!

import tkinter as tk
from tkinter import ttk 
import logging

from tools.apppointers import AppPointers

class GigDetailView(tk.Frame, AppPointers):
    """Class for the setlist info box used in library
    and the right pane of the main window."""

    def __init__(self, parent):
        tk.Frame.__init__(self,
            parent,
            # relief="sunken",
            # borderwidth=2,
            )
        AppPointers.__init__(self, parent)

        self.song = parent.song

        # TODO: change to title

        # self.rowconfigure(7, weight=10)
        # self.columnconfigure(0, weight=1)
        # self.columnconfigure(1, weight=0)
        # self.columnconfigure(2, weight=5)
        # self.columnconfigure(3, weight=5)

        self.header = tk.Label(self, text="GIG DETAILS")
        self.header.grid(row=0, column=0, columnspan=3, sticky="w")

        # TODO: grab lock functions etc from setlist.
        self.lock = tk.Label(self, text=u"\U0001F512",)
        # self.lock.bind("<Button-1>", lambda e: self.suite.toggle_lock())
        self.lock.grid(row=0, column=3, sticky="e")

        self.show_label = tk.Label(self, text="show:")
        self.show_label.grid(row=1, column=0, sticky="e")
        self.show_var = tk.StringVar()
        self.show_entry = tk.Entry(self)
        self.show_entry.grid(row=1, column=1, columnspan=3, sticky="ew")

        self.city_label = tk.Label(self, text="city:")
        self.city_label.grid(row=2, column=0, sticky="e")
        self.city_var = tk.StringVar()
        self.city_entry = tk.Entry(self)
        self.city_entry.grid(row=2, column=1, columnspan=3, sticky="ew")

        self.venue_label = tk.Label(self, text="venue:")
        self.venue_label.grid(row=3, column=0, sticky="e")
        self.venue_var = tk.StringVar()
        self.venue_entry = tk.Entry(self)
        self.venue_entry.grid(row=3, column=1, columnspan=3, sticky="ew")

        self.date_label = tk.Label(self, text="date:")
        self.date_label.grid(row=4, column=0, sticky="e")
        self.date_var = tk.StringVar()
        self.date_entry = tk.Entry(self, width=10)
        self.date_entry.grid(row=4, column=1, sticky="ew")

        self.schedule_button = tk.Button(self, text="Schedule")
        self.schedule_button.grid(row=4, column=2, sticky="ew")
        self.guests_button = tk.Button(self, text="Guests")
        self.guests_button.grid(row=4, column=3, sticky="ew")

        # TODO: add scrollbar to comments_text
        self.comments_label = tk.Label(self, text="comments:")
        self.comments_label.grid(row=5, column=0, columnspan=4, sticky="w")
        self.comments_var = tk.StringVar()
        self.comments_text = tk.Text(self, width=30)
        self.comments_text.grid(row=6, column=0, columnspan=4, sticky="nesw")
        self.rowconfigure(6, weight=10)


        # self.created_label = tk.Label(self, text="created:")
        # self.created_label.grid(row=8, column=0, columnspan=2, sticky="e")
        # self.created_var = tk.StringVar()
        # self.created_time = tk.Label(self)
        # self.created_time.grid(row=8, column=2, columnspan=4, sticky="w")

        # self.modified_label = tk.Label(self, text="modified:")
        # self.modified_label.grid(row=9, column=0, columnspan=2, sticky="e")
        # self.modified_var = tk.StringVar()
        # self.modified_time = tk.Label(self)
        # self.modified_time.grid(row=9, column=2, columnspan=4, sticky="w")

        # self.opened_label = tk.Label(self, text="opened:")
        # self.opened_label.grid(row=10, column=0, columnspan=2, sticky="e")
        # self.opened_var = tk.StringVar()
        # self.opened_time = tk.Label(self)
        # self.opened_time.grid(row=10, column=2, columnspan=4, sticky="w")



    def push(self, song):
        """dump old info back to song, push new song, refresh fields."""

        self.dump_meta_back_to_song()
        self.song = song
        self.refresh_song_meta_fields()

    def refresh_song_meta_fields(self):

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
            widget.insert(i, data)
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