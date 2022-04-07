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

        
        self.app = self
        self.root = root
        self.suite = None

        # init program settings
        self.settings = Settings(self)

        # tools for creating and moving data within the app, and scrolling
        # TODO: kinda convoluted struct
        self.tools = AppTools(self)

        # track songs played / cued & manage callbacks
        # TODO: seperate parts
        self.deck = SongDeck(self)

        # song cache, use weak references so old songs get gc'd
        self.cache = Cache(self)

        # sqlite3 / data mgmt
        self.data = AppData(self)

        # all gui elements
        self.gui = TkGui(app=self, root=root)
        # push sync
        self.gui.sync()

        # keyboard / mouse / etc. mappings
        self.controls = AppControls(self)

        self._config_window_properties()

    def _config_window_properties(self):
        # Set window attributes & icon
        self.root.iconbitmap("./assets/generic.ico")
        self.root.tk.eval("tk::PlaceWindow . center")
        self.root.resizable(False, False)

        # assign quit method
        self.root.protocol("WM_DELETE_WINDOW", self.quit_app)

    def quit_app(self):
        """What to do when you quit."""

        # TODO: see if state has changed since last save, only show message if it has.
        choice = messagebox.askyesnocancel("Save State","Save state before quitting?")
        if choice is None:
            return
        elif choice == True:
            self.save_state()
        self.root.destroy()

    def save_state(self):
        """Save app state by dumping settings and gig data."""
        self.settings.dump_settings()
        self.tools.db_interface.dump_gig(self.data.gig, workspace=True)

def main():
    """Application main loop."""

    logger = logging.getLogger()
    logger.setLevel(logging.INFO)

    root = tk.Tk()  # change to tkd.Tk if you end up using dnd package!
    root.title("PrompTools alpha")

    # TODO: decouple tkinter components from main app
    app = MainApplication(root)
    app.gui.mainloop()


if __name__ == "__main__":
    main()
