import tkinter as tk
import logging

from gui.setlist import SetlistFrame
from gui.pool import PoolAndSetlistsFrame, PoolAndSetlistsNotebook
from tools.apppointers import AppPointers

class CollectionsSuite(tk.PanedWindow, AppPointers):
    """Paned frame for the song collections on the left side of the app.
    It shows the live setlist, and the gig song pool."""

    def __init__(self, parent, *args, **kwargs):
        tk.PanedWindow.__init__(self,
            parent.frame,
            orient="vertical",
            sashwidth=5,
            bg="light blue",
            # showhandle=True
            )
        AppPointers.__init__(self, parent)

        # make frames
        self.pool = PoolAndSetlistsNotebook(self)
        self.add(self.pool)

        self.setlist = SetlistFrame(self)
        self.add(self.setlist)

        # reload collection data from db
        # self.app.data.reload_all_collections_from_db()