# module for the togglable (TODO) info pane on the right side of the program.

import tkinter as tk
from tkinter import scrolledtext
# from tkinter import ttk
import time
import copy
import logging

from gui.songdetail import SongDetailView
from gui.setlistdetail import GigDetailView

class MetaSuite(tk.PanedWindow):
    """Frame for metadata on the right pane"""
    # TODO: maybe rename info suite
    # TODO: think I prefer this as a popup instead of constantly visible

    def __init__(self, parent, *args, **kwargs):
        tk.PanedWindow.__init__(self,
            parent.frame,
            orient="vertical",
            sashwidth=5,
            borderwidth=5,
            relief="sunken",
            bg='pink',
            *args, **kwargs
            )

        # context
        self.parent = parent
        self.app = parent
        self.suite = self
        self.settings = self.app.settings

        # Current song, set, etc. whose info are being shown
        self.song = None
        self.set = None

        # frames
        # TODO: call font from settings
        self.notepad = scrolledtext.ScrolledText(self,
            width=10,
            height=5,
            fg="blue",
            # bg="#FFF9A3",
            bg="#DED77E",
            font="monaco 12" 
            )
        self.setlist_detail = GigDetailView(self)
        self.song_detail = SongDetailView(self)

        # callbacks for detail views so they get selection info instantly
        self.app.deck.add_callback('focused', self.song_detail.push_focused)

        # add panes
        self.add(self.notepad)
        self.add(self.setlist_detail)
        self.add(self.song_detail,
            # minsize=10
            )

        # bring out push fn for interfacing
        self.push = self.song_detail.push



