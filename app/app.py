import tkinter as tk
from tkinter import messagebox
import logging

# allows drag-n-drop, was a bit sketchy last time i used it. not using for now.
# import tkinterDnD as tkd

# app settings
from common.settings import Settings

# helper tools TODO: unroll tools.tools maybe?
from tools.tools import AppTools
from tools.data import AppData
from tools.cache import Cache
from tools.deck import SongDeck

# gui components
# TODO: package?
from gui.collections import CollectionsSuite
from gui.browser import BrowserSuite
from gui.talent import TalentWindow
from gui.monitor import TalentMonitor
from gui.preview import Preview
from gui.bigbutton import PromptButton
from gui.cued import CuedUp
from gui.menu import MenuBar
from gui.metapane import MetaSuite
from gui.helper import HelperBox


class MainApplication(tk.Frame):
    """Class for the main application."""

    def __init__(self, frame, *args, **kwargs) -> None:
        tk.Frame.__init__(self, frame)

        # context
        self.root = frame
        self.frame = frame
        self.app = self

        # init program settings
        # TODO: load previous settings from self.data
        self.settings = Settings(self)

        # tools for creating and moving data within the app, and scrolling
        self.tools = AppTools(self)

        # manages callbacks for updating cued / live / previous
        # TODO: expand to include history
        self.deck = SongDeck(self)

        # sqlite3 / data mgmt
        self.data = AppData(self)

        # song cache, use weak references so old songs get gc'd
        self.cache = Cache(self)

        # 2nd window for talent
        self.talent = TalentWindow(self)

        # main window widgets
        self.monitor = TalentMonitor(self)
        self.monitor.grid(row=0, column=1, columnspan=2, sticky="nesw")

        self.bigbutton = PromptButton(self)
        self.bigbutton.grid(
            row=3,
            column=1,
            rowspan=1,
            columnspan=2,
            ipadx=0,
            ipady=10,
            sticky="nesw",
            padx=5,
            pady=5,
        )

        self.browser = BrowserSuite(self)
        # self.browser = LibrarySuite(self) # this is the version that imports everything
        self.browser.grid(
            row=1,
            column=1,
            columnspan=1,
            rowspan=2,
            sticky="nesw",
            padx=8,
            pady=8,
        )

        # TODO: merge preview frame with cued since they will always live in that orientation
        self.cued = CuedUp(self)
        self.cued.grid(row=1, column=2, columnspan=1, sticky="nesw")

        self.preview = Preview(self)
        self.preview.grid(row=2, column=2, columnspan=1, sticky="nesw", padx=8, pady=8)

        self.meta = MetaSuite(self)
        self.meta.grid(row=0, column=3, sticky="nesw", rowspan=4)

        # setlist / song pool pane on the left
        self.collections = CollectionsSuite(self)
        self.collections.grid(row=0, column=0, rowspan=3, sticky="nesw")

        # this will be a tooltip box in the bottom left corner of the app
        self.helper = HelperBox(self)
        self.helper.grid(row=3, column=0, sticky="nesw")

        # configure rows / columns to get right weights
        self.columnconfigure(0, weight=1)
        self.columnconfigure(1, weight=0)
        self.columnconfigure(2, weight=1)
        self.columnconfigure(3, weight=5)

        # menus at the top of the app
        self.menu = MenuBar(self)

        # make some shorthand names.
        # TODO: best practice?
        self.setlist = self.collections.setlist
        self.pool = self.collections.pool

        # Set window attributes & icon
        self.tk.eval("tk::PlaceWindow . center")
        self.frame.resizable(False, False)
        self.frame.iconbitmap("./assets/generic.ico")

        # assign quit method
        self.root.protocol("WM_DELETE_WINDOW", self.quit_app)

    def quit_app(self):
        """What to do when you quit."""

        # TODO: see if state has changed since last save, only show message if it has.
        choice = messagebox.askyesnocancel(
            "Save Workspace",
            "Save workspace before quitting? Any unsaved changes to the workspace / settings will be lost.",
        )

        if choice == True:

            # logging.info('saved and quit')
            self.settings.dump_settings()
            # self.tools.dbmanager.dump_gig()
            self.root.destroy()

        elif choice == False:

            # logging.info('quit without saving')
            self.root.destroy()

        else:
            logging.info('canceled quit operation')


def main():
    """Application main loop."""
    root = tk.Tk()  # change to tkd.Tk if you end up using dnd package!
    root.title("PrompTools alpha")

    # TODO: decouple tkinter components from main app
    app = MainApplication(root)
    app.mainloop()


if __name__ == "__main__":
    main()
