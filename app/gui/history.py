# window to view and reload from song history.

import tkinter as tk
from tkinter import ttk
import logging 

from tools.apppointers import AppPointers

class SongHistoryWindow(tk.Toplevel, AppPointers):
    """Popup viewer for history. Should load to preview when you click an entry."""

    def __init__(self, parent, *args, **kwargs):
        tk.Toplevel.__init__(self, parent)
        AppPointers.__init__(self, parent)

        self._init_config()
        self._init_geometry()
        self._init_widgets()

    def _init_config(self):
        """Initialize window config"""
        self.title('Song History')
        self.settings.windows.song_history.set(True)
        self.protocol("WM_DELETE_WINDOW",self.quit_window)

    def _init_geometry(self):
                # default window size
        win_w = 400
        win_h = 500
        self.geometry(f'{str(win_w)}x{str(win_h)}')
        self.resizable(width=False, height=False)
        self.geometry(self.gui.screen_center(win_w, win_h))

    def _init_widgets(self):
        """Build window widgets."""
        self.treeview = HistoryTreeview(self)
        self.treeview.pack(expand=True, fill="both")

    def quit_window(self):
        self.settings.windows.song_history.set(False) 
        self.destroy()


class HistoryTreeview(tk.Frame, AppPointers): 

    def __init__(self, parent, *args, **kwargs):
        tk.Frame.__init__(self, parent)
        AppPointers.__init__(self, parent)

        # library data tree (left side of frame)
        tree = ttk.Treeview(self, selectmode="browse")
        tree['columns']=("name", "modified")
        
        tree.column("#0", width=0, stretch=False)
        tree.column("name", anchor="center", width=5)
        tree.column("modified", anchor="w", width=60)

        tree.heading("#0", text='', anchor="center")
        tree.heading("name", text="name", anchor="w")
        tree.heading("modified", text="modified", anchor="center")

        tree.pack(side="left", fill="both", expand=True)
        self.tree = tree

        self.scrollbar = ttk.Scrollbar(self, orient="vertical")
        self.scrollbar.config(command=self.tree.yview)
        self.tree.configure(yscrollcommand=self.scrollbar.set)
        self.scrollbar.pack(expand=True)

        self.tree.bind("<<TreeviewSelect>>", self.on_tree_select)

        self.dump_history_to_tree()

    def on_tree_select(self, event):
        """Retrieve the selected song data to a dict."""

        # get the selected row id
        sel = self.tree.focus()
        print(f'SELECTION IN HISTORY: {sel}')
        self.deck.cued = self.deck.history.fetch(sel)

    def dump_history_to_tree(self):
        history = self.deck.history.songs
        if not history:
            return 
        song_data = [(song.name, song.modified) for song in history]
        for i, song in enumerate(song_data):
            self.tree.insert(parent='', index="end", iid=i, values=song)
