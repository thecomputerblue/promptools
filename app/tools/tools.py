from tools.song import Song, SongFactory
from tools.transposer import Transposer
from tools.loader import LoadTool
from tools.scroll import ScrollTool
from tools.screens import Screens
from tools.db_interface import DatabaseManager
from tools.guitools import GuiTools
from tools.helper import Helper 
from tools.tk_text_interface import TkTextInterface
from tools.tempo import TapTempo

class AppTools():
    """Class for holding tools for the app.
    Each tool contains methods for accomplishing
    a certain category of task."""

    def __init__(self, app):
        self.app = app

        # responsible for generating song objects
        self.factory = SongFactory(app)

        # handle song transposition
        self.transposer = Transposer(app)

        # handle multiple screens
        self.screens = Screens(app)

        # handle scrolling & synch between talent/editor
        self.scroll = ScrollTool(app)

        # interface between songs and tkinter text boxes
        # TODO: this module has poor cohesion
        self.loader = LoadTool(app)

        # migrate the tk_text methods from loader to here
        self.tk_text_interface = TkTextInterface(app)

        # interface with sqlite3 database
        self.db_interface = DatabaseManager(app)

        # helpbox for tooltips & user-facing exceptions
        self.helper = Helper(app)

        self.tempo = TapTempo(app)
