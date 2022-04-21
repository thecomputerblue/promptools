import tkinter as tk
from tkinter import messagebox
import logging

# allows drag-n-drop, was a bit sketchy last time i used it. not using for now.
# import tkinterDnD as tkd


# app settings
from common.settings import Settings

# helper tools TODO: unroll tools.tools
from tools.tools import AppTools
from tools.data import AppData
from tools.cache import Cache
from tools.deck import SongDeck

from gui.gui import TkGui
from gui.controls import AppControls


class MainApplication:
    """Class for the main application."""

    def __init__(self, root, *args, **kwargs) -> None:

        # orientation pointers, used for tk & apppointer instances downstream
        self.app = self
        self.root = root
        self.suite = None

        # flag for state changes in workspace. not implemented yet. TODO
        # might be a better place to store these kinds of flags, maybe
        # in settings, maybe not.
        self._anything_changed = True

        # init program settings
        self.settings = Settings(self)

        # tools for creating and moving data within the app, and scrolling
        # TODO: kinda convoluted struct
        self.tools = AppTools(self)

        # manage playlisting, play history, cue, etc. any song obj movement / assignment
        # TODO: breakout these components as they become more comprehensive...
        self.deck = SongDeck(self)

        # not exactly a cache
        # tracks ALL song objects anywhere in the app. currently enforces stricter GC
        # than python default by running frequent checks. by tracking all songs in one
        # place i'll be able to update database references consistently when they change
        # (ie. if a library ID changes it needs to be updated in all loaded song objects
        # that use that ID.)
        self.cache = Cache(self)

        # sqlite3 / data mgmt
        self.data = AppData(self)

        # all tkinter elements
        self.gui = TkGui(app=self, root=root)
        # need to push sync after gui init so toggles, etc. match the program settings.
        self.gui.sync()

        # keyboard / mouse / etc. mappings
        self.controls = AppControls(self)

        self._config_window_properties()

    def _config_window_properties(self):
        """Grab bag of window config."""
        self.root.iconbitmap("./assets/generic.ico")
        self.root.tk.eval("tk::PlaceWindow . center")
        self.root.resizable(False, False)
        self.root.protocol("WM_DELETE_WINDOW", self.try_quit_app)

    def try_quit_app(self):
        """What to do when you quit."""
        self.ask_save() if self._anything_changed else self.root.destroy()

    def ask_save(self):
        choice = messagebox.askyesnocancel("Save State","Save state before quitting?")
        if choice is None:
            return
        elif choice == True:
            self.do_save()
        self.root.destroy()

    def do_save(self):
        """Save app state by dumping settings and gig data."""
        self.settings.dump_settings()
        self.tools.db_interface.dump_gig(self.data.gig, workspace=True)


def main():
    # config logger
    logger = logging.getLogger()
    logger.setLevel(logging.INFO)

    # tkinter gui root
    root = tk.Tk()
    root.title("PrompTools alpha")

    # app instance
    app = MainApplication(root)

    # tkinter mainloop
    app.gui.mainloop()


if __name__ == "__main__":
    main()
