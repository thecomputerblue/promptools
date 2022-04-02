# manages app settings, including storing / recalling settings
# between sessions.

import tkinter as tk
from tkinter import font
import logging
import json
import os
import io

import tools.colors as colors
from tools.scroll import AutoscrollBehavior
from tools.apppointers import AppPointers

# TODO: when eventually porting to kivy/pyqt you'll need to migrate
# all the tkinter references in here.

# helpers
def merge(defaults, custom):
    """Merge two settings dicts, prioritizing custom"""

    if not custom:
        logging.info("no custom")
        return defaults

    merge = {}

    for k, v in defaults.items():
        c = custom.get(k)
        merge[k] = c if c != None else v

    return merge


def ms_to_fps(ms):
    return 1000 / ms


def fps_to_ms(fps):
    return


class Settings(AppPointers):
    """Class for managing program wide settings."""

    def __init__(self, parent):
        AppPointers.__init__(self, parent)

        # path for custom settings file
        self.custom_path = "./data/settings.json"

        # make sure the custom settings file exists.
        self.validate_settings(self.custom_path)

        # store all configurable settings in a nested dict.
        # assign setters/getters to pull from this when possible and push updates to it.
        self.custom = self.load_settings(self.custom_path)
        # TODO: first try to reload the configurable dict.

        # self.misc_settings()
        self.appset = AppSettings(self, "AppSettings")
        self.arrow = ArrowSettings(self, "ArrowSettings")
        self.scroll = AutoScrollSettings(
            self, "AutoScrollSettings"
        )  # TODO: move speed params etc here
        self.chunk = ChunkScrollSettings(self, "ChunkScrollSettings")
        self.editor = EditSettings(self, "EditSettings")
        self.fonts = FontSettings(self, "FontSettings")
        self.importer = ImportSettings(self, "ImportSettings")
        self.library = LibrarySettings(self, "LibrarySettings")
        self.keys = KeySettings(self, "KeySettings")
        self.meta = MetaSettings(self, "MetaSettings")
        self.paths = PathSettings(self, "PathSettings")  # changed from dirs
        self.scalers = ScalerSettings(self, "ScaleSettings")
        self.setlist = SetlistSettings(self, "SetlistSettings")
        self.tags = TagSettings(self, "TagSettings")
        self.transposer = TransposerSettings(self, "TransposerSettings")
        self.view = ViewSettings(self, "ViewSettings")
        self.windows = WindowSettings(self, "WindowSettings")
        self.workspace = WorkspaceSettings(self, "WorkspaceSettings")

        # register modules here so they get updated
        self.modules = self.library

        # log custom settings
        logging.info(f"custom settings at init: {self.custom.items()}")

    def validate_settings(self, path):
        """Check if settings json file exists, creates if not."""
        # adapted from: https://stackoverflow.com/questions/32991069/python-checking-for-json-files-and-creating-one-if-needed

        # TODO: Doesn't yet verify that the settings file is viable to load.
        if os.path.isfile(self.custom_path) and os.access(self.custom_path, os.R_OK):
            logging.info("Custom settings file exists and is readable")
        else:
            logging.info(
                "Custom settings file is missing or is not readable, creating file..."
            )
            with io.open("./data/settings.json", "w") as f:
                f.write(json.dumps({}))

    def load_settings(self, path):
        """Load the settings file."""

        # TODO: verify contents of settings file
        with open(path, "r") as f:
            custom = json.load(f)

        return custom if custom else {}

    def dump_settings(self, path="./data/settings.json"):
        """Dump the settings dict back to a json file."""

        with open(path, "w") as f:
            json.dump(self.custom, f)


# TODO: implement ABC?
class SettingsBaseClass:
    """Base class for a settings module that sets up the custom settings
    dict and app pointers, along with any generic methods used across
    modules."""

    def __init__(self, settings, name):
        self.app = settings.app
        self.settings = settings
        self.callbacks = []

        # initialize the custom dict for this module.
        if name not in settings.custom:
            settings.custom[name] = {}

        self.custom = self.settings.custom.get(name)

    def _update_customs(self, name, value):
        """Updat an entry in the local custom settings dict."""

        self.custom[name] = value

    def _trace(self, tkvar, name):
        """Add callback for tkvar."""
        tkvar.trace("w", lambda *args: self._update_customs(name, tkvar.get()))

    def _make_callback_trigger(self, tkvar):
        """Register tkvar to trigger module callbacks."""
        tkvar.trace("w", lambda *args: self.do_callbacks())

    def setting(
        self,
        tkvarclass,
        name: str,
        inits: dict,
        triggers_callbacks=False,
        saves=True,
    ) -> object:
        """Make a new setting and assign a default value and callback,
        returning a tkinter variable."""
        setting = tkvarclass()
        setting.set(inits.get(name))
        self._trace(setting, name) if saves else None
        self._make_callback_trigger(setting) if triggers_callbacks else None
        return setting

    def add_callback(self, c):
        self.callbacks.append(c)

    def do_callbacks(self, *args):
        if not self.callbacks:
            return
        [c() for c in self.callbacks]


class PathSettings(SettingsBaseClass):
    """Class for directory defaults & custom."""

    def __init__(self, settings, name):
        SettingsBaseClass.__init__(self, settings, name)

        self.defaults = {"appdata": "./data/appdata.db", "exports": "./data/exports"}

        inits = merge(self.defaults, self.custom)

        # TODO: 'library' is a bit of a misnomer, name better
        # these three defaults and should not be made configurable,
        # always want the default paths available to browse

        self.texts = tk.StringVar()
        txtdir = "./data/text_files"
        os.makedirs(txtdir) if not os.path.exists(txtdir) else None
        self.texts.set(txtdir)

        # sqlite3 database
        self.db = tk.StringVar()
        self.db.set(inits.get("appdata"))


class ChunkScrollSettings(SettingsBaseClass):
    """Class for chunk scroll settings."""

    # TODO: dataclass?

    def __init__(self, settings, name):
        SettingsBaseClass.__init__(self, settings, name)

        self._duration_ms = 300
        self._pixels_advanced = 100
        self._step = self.update_step()
        self.enabled = False

    @property
    def duration_ms(self):
        return self._duration_ms

    @duration_ms.setter
    def duration_ms(self, duration_ms):
        self._duration_ms = duration_ms
        self._step = self.update_step()

    @property
    def pixels_advanced(self):
        return self._pixels_advanced

    @pixels_advanced.setter
    def pixels_advanced(self, pixels_advanced):
        self._pixels_advanced = pixels_advanced
        self._step = self.update_step()

    @property
    def step(self):
        return self._step

    def update_step(self):
        return self.duration_ms // self.pixels_advanced


class AppSettings(SettingsBaseClass):
    """Class for settings for overall app behavior. For example,
    whether other settings are saved."""

    def __init__(self, settings, name):
        SettingsBaseClass.__init__(self, settings, name)

        # set defaults
        self.defaults = {"recall_custom": True}

        inits = merge(self.defaults, self.custom)

        self.recall_custom = self.setting(tk.BooleanVar, "recall_custom", inits)


# TODO: dataclass?
class TransposerSettings(SettingsBaseClass):
    """Class for storing transposer settings."""

    def __init__(self, settings, name):
        SettingsBaseClass.__init__(self, settings, name)

        # set defaults here
        self.defaults = {
            "enabled": False,
            "nashville": False,
            "apply_to_cued": True,
            "apply_to_current": False,
            "key": "",
        }

        inits = merge(self.defaults, self.custom)

        self.enabled = self.setting(tk.BooleanVar, "enabled", inits)
        self.nashville = self.setting(tk.BooleanVar, "nashville", inits)
        self.apply_to_cued = self.setting(tk.BooleanVar, "apply_to_cued", inits)
        self.apply_to_current = self.setting(tk.BooleanVar, "apply_to_current", inits)
        self.key = self.setting(tk.StringVar, "key", inits)

    def reset(self):
        """Clear transposer settings. Doesn't affect Nashville mode"""

        self.enabled.set(False)
        self.apply_to_cued.set(False)
        self.apply_to_current.set(False)
        self.key.set("")


# TODO: dataclass?
class ImportSettings(SettingsBaseClass):
    """Class for import / export settings."""

    def __init__(self, settings, name):
        SettingsBaseClass.__init__(self, settings, name)

        # define default settings here
        self.defaults = {
            "raw": False,
            "auto_tag": True,
            "valid_ext": (".txt", ".rtf"),
        }

        # merge default and custom settings to get inits
        inits = merge(self.defaults, self.custom)

        # apply settings to vars

        # import files raw by default
        self.raw = self.setting(tk.BooleanVar, "raw", inits)

        # automatically tag text files on import
        self.auto_tag = self.setting(tk.BooleanVar, "auto_tag", inits)

        # valid extensions for imported files
        self.valid_ext = inits.get("valid_ext")


class EditSettings(SettingsBaseClass):
    """Class for editor settings."""

    def __init__(self, settings, name):
        SettingsBaseClass.__init__(self, settings, name)

        # define default settings here
        self.defaults = {
            "enabled": False,
            "talent_follows_monitor_when_editing": True,
        }

        inits = merge(self.defaults, self.custom)

        self.enabled = self.setting(tk.BooleanVar, "enabled", inits)
        self.talent_follows_monitor_when_editing = self.setting(
            tk.BooleanVar, "talent_follows_monitor_when_editing", inits
        )


class AutoScrollSettings(SettingsBaseClass):
    """Class for scroll settings."""

    def __init__(self, settings, name):
        SettingsBaseClass.__init__(self, settings, name)

        self.defaults = {
            # 'interval': 1.0,
            "pixels": 3,
            "mon_snap": True,
            "mon_follow": False,
            "mon_fps": 10,
            "running": False,
            "steps": 20,  # number of speed settings on scale
            "pos": 0.8,  # speed scale marker % from end
        }

        inits = merge(self.defaults, self.custom)

        self.running = self.setting(tk.BooleanVar, "running", inits, True)

        # number of pixels scroll per scroll operation
        self.pixels = self.setting(tk.IntVar, "pixels", inits, True)

        # number of steps on scroll speed scale
        self.steps = self.setting(tk.IntVar, "steps", inits, True)

        # speed scale position in %. gets rounded to nearest setting.
        self.pos = self.setting(tk.DoubleVar, "pos", inits, True)

        # monitor snap to talent view between scrolls.
        self.mon_snap = self.setting(tk.BooleanVar, "mon_snap", inits, True)

        # monitor follows talent during scroll
        self.mon_follow = self.setting(tk.BooleanVar, "mon_follow", inits, True)

        # monitor refresh rates when following talent scroll
        self._mon_ms = None
        self._mon_fps = None
        # propagates correct val to self.mon_ms via setter method
        self.mon_fps = inits.get("mon_fps")

        # generate list of autoscroll rates
        self._rates = self.make_scroll_rates()

        # save settings with callback

    def save_setting(self, target: str, tk_setting):
        """Save setting in the custom dict."""
        # TODO: move to SettingsBaseClass / confirm I didn't already write one of these...
        self.custom[target] = tk_setting.get()

    def make_scroll_rates(self):
        """Make the scale used for autoscroll."""
        # # Scale for scroll speed
        # self.autoscroll_rates = \
        #   AutoscrollBehavior(smin=100, smax=1, steps = 100).vals

        # TODO fix this hacky crap
        rates = []
        for i in range(30, 1, -1):
            rates.append(i)

        return rates

    @property
    def rates(self):
        return self._rates

    @rates.setter
    def rates(self, new):
        self._rates = new
        self.do_callbacks()

    @property
    def mon_ms(self):
        return self._mon_ms

    @mon_ms.setter
    def mon_ms(self, ms):
        self._mon_ms = ms
        self._mon_fps = ms_to_fps(ms)
        self.do_callbacks()
        self.custom["mon_ms"] = ms

    @property
    def mon_fps(self):
        return self._mon_fps

    @mon_fps.setter
    def mon_fps(self, fps):
        self._mon_fps = fps
        self._mon_ms = fps_to_ms(fps)
        self.do_callbacks()
        self.custom["mon_fps"] = fps


class ViewSettings(SettingsBaseClass):
    """Class for view settings."""

    def __init__(self, settings, name):
        SettingsBaseClass.__init__(self, settings, name)

        self.defaults = {
            "frozen": False,
            "text_wrap": "none",
            "fullscreen": False,
            "cue_truncate": 45,
        }

        inits = merge(self.defaults, self.custom)

        self.frozen = self.setting(tk.BooleanVar, "frozen", inits)
        self.text_wrap = inits.get("text_wrap")
        self.fullscreen = self.setting(tk.BooleanVar, "fullscreen", inits)
        self.cue_truncate = self.setting(tk.IntVar, "cue_truncate", inits)


class FontSettings(SettingsBaseClass):
    """Class for font settings."""

    def __init__(self, settings, name):
        SettingsBaseClass.__init__(self, settings, name)

        self.defaults = {
            "gui": {"family": "arial", "size": 12},
            "talent": {"family": "monaco", "size": 24},
            "monitor": {"family": "monaco", "size": 24},
            "preview": {"family": "monaco", "size": 12},
            "cue_title": {"family": "monaco", "size": 18},
            "library": {"family": "monaco", "size": 18},
            "button": {"family": "monaco", "size": 18},
            "transposer": {"family": "arial", "size": 18},
        }

        self.gui = self.make_font("gui")
        self.talent = self.make_font("talent")
        self.monitor = self.make_font("monitor")
        self.preview = self.make_font("preview")
        self.cue_title = self.make_font("cue_title")
        self.library = self.make_font("library")
        self.button = self.make_font("button")
        self.transposer = self.make_font("transposer")

    def sub_merge(self, sub):
        """Merges nested dicts for the individual font settings."""
        # TODO: multiple ineritance for Font, pass these in on init?
        return merge(self.defaults.get(sub), self.custom.get(sub))

    def make_font(self, font):
        properties = self.sub_merge(font)
        if not self.custom.get(font):
            self.custom[font] = {}
        return Font(root=self.app, custom=self.custom.get(font), properties=properties)


class Font(tk.font.Font):
    """Augmented tkinter Font class so I can scale fonts from a reference point."""

    def __init__(self, root, custom, properties, *args):
        font.Font.__init__(
            self,
            root=root,
            family=properties.get("family"),
            size=properties.get("size"),
            *args,
        )

        # needed to pass custom settings back to the custom settings dict
        self.custom = custom

        self.family = tk.StringVar()
        self.family.set(properties.get("family"))
        self.family.trace("w", lambda *args: self._family_set())

        self.size = tk.IntVar()
        self.size.set(properties.get("size"))
        self.size.trace("w", lambda *args: self._size_set())

        self.callbacks = []

    def _family_set(self):
        self.custom["family"] = self.family.get()
        self.config(family=self.family.get())
        self.do_callbacks()

    def _size_set(self):
        self.custom["size"] = self.size.get()
        self.config(size=self.size.get())
        self.do_callbacks()

    def add_callback(self, c):
        self.callbacks.append(c)

    def do_callbacks(self):
        if not self.callbacks:
            return
        [c() for c in self.callbacks]


class WindowSettings(SettingsBaseClass):
    """Class tracking windows within program."""

    def __init__(self, settings, name):
        SettingsBaseClass.__init__(self, settings, name)

        self.library = tk.BooleanVar()
        self.preferences = tk.BooleanVar()
        self.transposer = tk.BooleanVar()
        self.metadata = tk.BooleanVar()


class ArrowSettings(SettingsBaseClass):
    """Class for the prompter arrow settings."""

    def __init__(self, settings, name):
        SettingsBaseClass.__init__(self, settings, name)

        self.defaults = {
            "color": "#E44C62",
            "lighten": 0.5,
            "borderwidth": 2,
            "pos": 0.2,
            "scale": 1.0,
        }

        inits = merge(self.defaults, self.custom)

        # TODO: init with self.setting method to shorten code
        self.color = tk.StringVar()
        self.color.set(inits.get("color"))
        self.color.trace("w", self.update_arrow_color)

        self.lighten = inits.get("lighten")

        self.outline = tk.StringVar()
        self.outline.set(colors.gen_outline_color(self.color.get(), self.lighten))

        self.borderwidth = tk.IntVar()
        self.borderwidth.set(2)

        self.pos = tk.DoubleVar()
        self.pos.set(0.2)

        self.scale = tk.DoubleVar()
        self.scale.set(1.0)  # muptliplier for base arrow size

        self.callbacks = []

    def update_arrow_color(self, *args):
        color = self.color.get()
        self.outline.set(colors.gen_outline_color(color, self.lighten))
        self.custom["color"] = color
        self.do_callbacks()


class MetaSettings(SettingsBaseClass):
    """Settings for metadata pane(s)."""

    def __init__(self, settings, name):
        SettingsBaseClass.__init__(self, settings, name)

        # TODO: defaults
        # TODO: necessary?

        # editable
        self.edit = tk.BooleanVar()

        # current song properties
        self.title = tk.StringVar()
        self.key = tk.StringVar()
        self.confidence = tk.IntVar()
        self.songwriter = tk.StringVar()
        self.comments = tk.StringVar()
        self.created = tk.StringVar()
        self.modified = tk.StringVar()


class SetlistSettings(SettingsBaseClass):
    """Settings for setlist behavior & currently loaded setlist."""

    def __init__(self, settings, name):
        SettingsBaseClass.__init__(self, settings, name)

        self.defaults = {
            "locked": True,
            "played_yview": 0.6,
            "played_seconds": 60,
            "city": "",
            "venue": "",
            "thanks": "",
            "band": {},
            "guest_list": [],
        }

        inits = merge(self.defaults, self.custom)

        # editable
        self.locked = self.setting(tk.BooleanVar, "locked", inits)

        # mark as played if you unload a song past this point
        self.played_yview = self.setting(tk.DoubleVar, "played_yview", inits)

        # mark as played if you unload a song after it was loaded for this many seconds.
        # None = disable
        self.played_seconds = self.setting(tk.IntVar, "played_seconds", inits)

        # TODO: much of this should be stored in a setlist object, not settings
        self.city = self.setting(tk.StringVar, "city", inits)
        self.venue = self.setting(tk.StringVar, "venue", inits)
        self.thanks = self.setting(tk.StringVar, "thanks", inits)

        # TODO: make these work with self.setting constructor
        # dict of {musician: blurb}
        self.band = inits.get("band")

        # list of guests, pointer for selected guest
        self.guest_list = inits.get("guest_list")

        # define colors in the setlist.
        # TODO: get these into custom settings pattern
        self.colors = SetlistColors(self.settings, name)


class SetlistColors(SettingsBaseClass):
    """Text styles for setlist."""

    def __init__(self, settings, name):
        SettingsBaseClass.__init__(self, settings, name)
        # TODO: dict

        self.default = "light grey"
        self.skipped = "dark grey"
        self.previous = "pink"
        self.nextup = "light yellow"
        self.live = "light green"


class KeySettings(SettingsBaseClass):
    """Class to store all the keyboard mappings throughout the app."""

    def __init__(self, settings, name):
        SettingsBaseClass.__init__(self, settings, name)

        # TODO: defaults

        # use lists for multiple assignment
        self.scroll_toggle = ["<space>"]


class TagSettings(SettingsBaseClass):
    """Track the different style / word tags used in app."""

    def __init__(self, settings, name):
        SettingsBaseClass.__init__(self, settings, name)

        # TODO: defaults

        # keep separate lists of styles and types, might need
        self.styles = ["bold", "italic", "underline", "strike", "size"]
        self.types = [
            "chord",
            "key",
            "lyric",
            "slashchord",
            "bar",
            "bvs",
            "header",
            "ws",
            "nl",
            "typo",
        ]

        # tag properties go here. value is kwargs passed to configure_text_tags in loader
        # TODO: will be some variation in tag color between talent and monitor (ie. there will be some
        # invisible text options on talent). separate dict for those.

        # test font
        # bold_font = font.Font(None)

        # TODO: may need to separate out the non-color tags due to tkinter implementation
        self.tags = {
            # styles
            # TODO: tuples should reference variables
            "bold": {"font": ("menlo", "24", "bold")},
            "italic": {"font": "italic"},
            "underline": {"font": "underline"},
            # TODO: strikethru
            # TODO: size, linked to the size scale calc.
            # TODO: alternate size setting for monitor
            # types
            "lyric": {"foreground": "white"},
            "chord": {"foreground": "light blue"},
            "slashchord": {"foreground": "light blue"},
            "key": {"foreground": "lime"},
            "bar": {"foreground": "light blue"},
            "nl": {},
            "ws": {},
            "header": {"foreground": "orange"},
            "bvs": {"foreground": "yellow"},
        }

        self.special = {
            "operator": lambda talent: {"foreground": "black"}
            if talent
            else {"foreground": "grey"},
        }

        self.systemWindowBackgroundColor = (
            "light grey"  # TODO: get actual reference working
        )


class WorkspaceSettings(SettingsBaseClass):
    """Class for workspace settings."""

    def __init__(self, settings, name):
        SettingsBaseClass.__init__(self, settings, name)

        self.defaults = {
            # store the last non-zero gig_id (0 is reserved for workspace) so on subsequent
            # runs you can save the workspace back to the same gig.
            "last_gig_id": None,
            "reload_at_init": True,
        }

        inits = merge(self.defaults, self.custom)

        # TODO: callback so this updates when gig_id changes
        self.last_gig_id = self.setting(tk.IntVar, "last_gig_id", inits)
        self.reload_at_init = self.setting(tk.BooleanVar, "reload_at_init", inits)


class ScalerSettings(SettingsBaseClass):
    """Settings for scaling text / arrow / etc. in talent & editor views."""

    def __init__(self, settings, name):
        SettingsBaseClass.__init__(self, settings, name)

        self.defaults = {
            "all": 1,
            "arrow": 1,
            "editor": 1,
            "talent": 1,
        }

        inits = merge(self.defaults, self.custom)

        self.all = self.setting(tk.DoubleVar, "all", inits)
        self.arrow = self.setting(tk.DoubleVar, "arrow", inits)
        self.editor = self.setting(tk.DoubleVar, "editor", inits)
        self.talent = self.setting(tk.DoubleVar, "talent", inits)


class LibrarySettings(SettingsBaseClass):
    """Class for library settings, especially read/write behaviors."""

    def __init__(self, settings, name):
        SettingsBaseClass.__init__(self, settings, name)

        self.defaults = {
            "overwrite_songs": False,
            "overwrite_setlists": False,
            "cue_selection": False,
        }

        inits = merge(self.defaults, self.custom)

        # when enabled, saving a song / setlist with existing ID to library
        # will overwrite the song / setlist at that ID. when disabled, a
        # new ID will be generated, potentially creating duplicates, but
        # ensuring that references are preserved across all setlists.
        self.overwrite_songs = self.setting(tk.BooleanVar, "overwrite_songs", inits)
        self.overwrite_setlists = self.setting(
            tk.BooleanVar, "overwrite_setlists", inits
        )
        self.cue_selection = self.setting(tk.BooleanVar, "cue_selection", inits)
