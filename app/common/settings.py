# manages app settings, including storing / recalling settings
# between sessions.

import tkinter as tk
from tkinter import font
import logging
import json
import os
import io

from tools.scroll import AutoscrollBehavior

# helpers
def merge(defaults, custom): 
    """Merge two settings dicts, prioritizing custom"""

    if not custom:
        return defaults

    merge = {}

    for k,v in defaults.items():
        c = custom.get(k)
        merge[k] = c if c != None else v

    return merge


class Settings:
    """Class for managing program wide settings."""

    def __init__(self, app):
        self.app = app

        # path for custom settings file
        self.custom_path = './data/settings.json'

        # make sure the custom settings file exists.
        self.validate_settings(self.custom_path)

        # store all configurable settings in a nested dict.
        # assign setters/getters to pull from this when possible and push updates to it.
        self.custom = self.load_settings(self.custom_path)
        # TODO: first try to reload the configurable dict.

        # self.misc_settings()
        self.arrow = ArrowSettings(self, "ArrowSettings")
        self.chunk = ChunkSettings(self, "ChunkSettings")
        self.editor = EditSettings(self, "EditSettings")
        self.fonts = FontSettings(self, "FontSettings")
        self.importer = ImportSettings(self, "ImportSettings")
        self.library = LibrarySettings(self, "LibrarySettings")
        self.keys = KeySettings(self, "KeySettings")
        self.meta = MetaSettings(self, "MetaSettings")
        self.paths = PathSettings(self, "PathSettings") # changed from dirs
        self.scroll = ScrollSettings(self, "ScrollSettings") # TODO: move speed params etc here
        self.setlist = SetlistSettings(self, "SetlistSettings")
        self.tags = TagSettings(self, "TagSettings")        
        self.transposer = TransposerSettings(self, "TransposerSettings")
        self.view = ViewSettings(self, "ViewSettings")
        self.windows = WindowSettings(self, "WindowSettings")
        self.workspace = WorkspaceSettings(self, "WorkspaceSettings")

        # register modules here so they get updated
        self.modules = (self.library)

        # log custom settings
        logging.info(f'custom settings at init: {self.custom.items()}')

    def validate_settings(self, path):
        """Check if settings json file exists, creates if not."""
        # adapted from: https://stackoverflow.com/questions/32991069/python-checking-for-json-files-and-creating-one-if-needed

        # TODO: Doesn't yet verify that the settings file is viable to load.
        if os.path.isfile(self.custom_path) and os.access(self.custom_path, os.R_OK):
            logging.info("Custom settings file exists and is readable")
        else:
            logging.info("Custom settings file is missing or is not readable, creating file...")
            with io.open('./data/settings.json', 'w') as f:
                f.write(json.dumps({}))

    def load_settings(self, path):
        """Load the settings file."""

        # TODO: verify contents of settings file
        with open(path, 'r') as f:
            custom = json.load(f)

        return custom if custom else {}

    def dump_settings(self, path):
        """Dump the settings dict back to a json file."""

        with open('./data/settings.json', 'w') as f:
            json.dump(self.custom, f)


# TODO: implement ABC?
class SettingsBaseClass:
    """Base class for a settings module that sets up the custom settings
    dict and app pointers, along with any generic methods used across
    modules."""

    def __init__(self, settings, name):
        self.app = settings.app 
        self.settings = settings

        # initialize the custom dict for this module.
        if name not in settings.custom:
            settings.custom[name] = {}

        self.custom = self.settings.custom.get(name)

    def update(self, name, value):
        """Updat an entry in the local custom settings dict."""
        self.custom[name] = value


# TODO: didn't work cleanly with tkinter vars, might be some use for this later
# class Setting:
#     """Class for an individual setting with setter method that automatically
#     creates or updates the associated custom dictionary k:v."""

#     def __init__(self, name, value, custom_dict, obj=None):
#         self.name = name
#         # object of the setting if one exists (ie. tk.StringVar)
#         self._obj = obj
#         # value of the setting
#         self._value = value
#         # when the setting is changed, a reference to the new value
#         # is stored in the custom dictionary.
#         self.custom = custom_dict

#     def __get__(self):
#         """Interface with the value directly through the Setting object."""
#         logging.info('returning self.value via Setting.__get__')
#         return self.value

#     def __set__(self, new):
#         """Interface with the value directly through the Setting object."""
#         self.value = new

#     def set(self, new):
#         logging.info('called Setting.set()')
#         self._obj.set(new) if self._obj else None
#         self._value = new
#         self.custom[self.name] = new

#     def get(self):
#         return self._obj.get()

#     @property
#     def value(self):
#         """Return value via the obj (trigger callbacks) if there is an object,
#         else return the value bare."""

#         return self._obj if self._obj else self._value

#     @value.setter
#     def value(self, new):
#         """Update obj, value, custom dict."""
#         self.set(new)
    

class PathSettings(SettingsBaseClass):
    """Class for directory defaults & custom."""

    def __init__(self, settings, name):
        SettingsBaseClass.__init__(self, settings, name)

        self.defaults = {
        'appdata' : './data/appdata.db',
        'exports' : './data/exports'
        }

        inits = merge(self.defaults, self.custom)

        # TODO: 'library' is a bit of a misnomer, name better
        # these three defaults and should not be made configurable,
        # always want the default paths available to browse 

        self.texts = tk.StringVar()
        txtdir = './data/text_files'
        os.makedirs(txtdir) if not os.path.exists(txtdir) else None
        self.texts.set(txtdir)

        # sqlite3 database
        self.db = tk.StringVar()
        self.db.set(inits.get("appdata"))

    @property
    def custom_library(self):
        return self._custom_library

    @custom_library.setter
    def custom_library(self, new):
        # when you set the custom library path, update the custom dict as well.
        self.custom["custom_library"] = new 
        self._custom_library.set(new)

    @property
    def custom_collections(self):
        return self._custom_collections

    @custom_collections.setter
    def custom_collections(self, new):
        # when you set the custom collections path, update the custom dict as well.
        self.custom["custom_collections"] = new 
        self._custom_collections.set(new)        

    @property
    def custom_workspaces(self):
        return self._custom_workspaces

    @custom_collections.setter
    def custom_workspaces(self, new):
        # when you set the custom collections path, update the custom dict as well.
        self.custom["custom_workspaces"] = new 
        self._custom_workspaces.set(new)        


class ChunkSettings(SettingsBaseClass):
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

# TODO: dataclass?
class TransposerSettings(SettingsBaseClass):
    """Class for storing transposer settings."""

    def __init__(self, settings, name):
        SettingsBaseClass.__init__(self, settings, name)

        # set defaults here
        self.defaults = {
        'enabled': False,
        'nashville': False,
        'apply_to_cued': True,
        'apply_to_current': False,
        'key': '',
        }

        inits = merge(self.defaults, self.custom)

        self.enabled = tk.BooleanVar()
        self.enabled.set(inits.get('enabled'))

        self.nashville = tk.BooleanVar()
        self.nashville.set(inits.get('nashville'))

        self.apply_to_cued = tk.BooleanVar()
        self.apply_to_cued.set(inits.get('apply_to_cued'))

        self.apply_to_current = tk.BooleanVar()
        self.apply_to_current.set(inits.get('apply_to_current'))

        self.key = tk.StringVar()
        self.key.set('')

    def reset(self):
        """Clear transposer settings. Doesn't affect Nashville mode"""
        self.enabled.set(False)
        self.apply_to_cued.set(False)
        self.apply_to_current.set(False)
        self.key.set('')


# TODO: dataclass?
class ImportSettings(SettingsBaseClass):
    """Class for import / export settings."""

    def __init__(self, settings, name):
        SettingsBaseClass.__init__(self, settings, name)

        # define default settings here
        self.defaults = {
        'raw': False,
        'auto_tag': True,
        'valid_ext': ('.txt', '.rtf'),
        }

        # merge default and custom settings to get inits
        inits = merge(self.defaults, self.custom)

        # apply settings to vars

        # import files raw by default
        self._raw = tk.BooleanVar()
        self._raw.set(inits.get('raw'))

        # automatically tag text files on import
        self._auto_tag = tk.BooleanVar()
        self._auto_tag.set(inits.get('auto_tag'))

        # valid extensions for imported files
        self.valid_ext = inits.get('valid_ext')

    @property
    def raw(self):
        return self._raw.get()

    @raw.setter
    def raw(self, new):
        """When you set raw in app, also update custom dict."""
        self.custom['raw'] = new
        self._raw.set(new)
    
    @property
    def auto_tag(self):
        return self._auto_tag.get()

    @auto_tag.setter
    def auto_tag(self, new):
        """When you set autotag in app, also update custom dict."""
        self.custom['auto_tag'] = new
        self._auto_tag.set(new)


class EditSettings(SettingsBaseClass):
    """Class for editor settings."""

    def __init__(self, settings, name):
        SettingsBaseClass.__init__(self, settings, name)

        self.enabled = tk.BooleanVar()
        self.talent_follows_monitor_when_editing = tk.BooleanVar()
        # self.talent_follows_monitor_when_editing.set(True)

class ScrollSettings(SettingsBaseClass):
    """Class for scroll settings."""

    def __init__(self, settings, name):
        SettingsBaseClass.__init__(self, settings, name)

        self.running = tk.BooleanVar()
        self.chunk = ChunkSettings(settings, name)
        # self.chunk_scrolling = tk.BooleanVar()
        self.interval = 1.0
        self.pixels = 1
        self.rates = self.make_scroll_rates()
        self.current = tk.IntVar()

        # monitor snap to talent view between scrolls.
        self.mon_snap = tk.BooleanVar()
        self.mon_snap.set(True)

        # monitor refresh during scroll.
        self.mon_follow = tk.BooleanVar()
        self.mon_follow.set(False)
        self.mon_fps = 10

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
    def mon_ms(self):
        return self._mon_ms

    @mon_ms.setter
    def mon_ms(self, ms):
        self._mon_ms = ms 
        self._mon_fps = 1000 / ms

    @property
    def mon_fps(self):
        return self._monitor_refresh_fps

    @mon_fps.setter
    def mon_fps(self, fps):
        self._mon_fps = fps
        self._mon_ms = 1000 // fps 


class ViewSettings(SettingsBaseClass):
    """Class for view settings."""

    def __init__(self, settings, name):
        SettingsBaseClass.__init__(self, settings, name)

        self.frozen = tk.BooleanVar()
        self.text_wrap = "none"
        self.fullscreen = tk.BooleanVar()

        # max characters for cue titlecard
        self.cue_truncate = 45

class FontSettings(SettingsBaseClass):
    """Class for font settings."""

    def __init__(self, settings, name):
        SettingsBaseClass.__init__(self, settings, name)

        app = self.app
        # TODO: group fonts into lists for batch scaling.
        self.gui = Font(root=app, family="arial", size=12)
        self.talent = Font(root=app, family="monaco", size=24)
        self.monitor = Font(root=app, family="monaco", size=24)
        self.preview = Font(root=app, family="monaco", size=12)
        self.cue_title = Font(root=app, family="monaco", size=18)
        self.library = Font(root=app, family="monaco", size=18)
        self.button = Font(root=app, family="monaco", size=24)
        self.transposer = Font(root=app, family="arial", size=18)

class Font(tk.font.Font):
    """Augmented tkinter Font class so I can scale fonts from a reference point."""

    def __init__(self, root, family, size, *args):
        font.Font.__init__(self, root=root, family=family, size=size, *args)

        # store these defaults for use later
        self.family = family
        # size used as a base for scaling later on prompter font.
        self.size = size

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

        self.color = tk.StringVar()
        self.color.set("red")

        self.outline = tk.StringVar()
        self.outline.set("pink")

        self.borderwidth = tk.IntVar()
        self.borderwidth.set(2)

        self.pos = tk.DoubleVar()
        self.pos.set(0.2)

        self.scale = tk.DoubleVar()
        self.scale.set(1.0)  # muptliplier for base arrow size

class MetaSettings(SettingsBaseClass):
    """Settings for metadata pane(s)."""

    def __init__(self, settings, name):
        SettingsBaseClass.__init__(self, settings, name)

        # TODO: defaults 

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
        'edit': False,
        'played_yview': 0.6,
        'played_seconds': 60,
        'city': "",
        'venue': "",
        'thanks': "",
        'band': {},
        'muso': "",
        'guest_list': [],
        'guest': ""
        }

        inits = merge(self.defaults, self.custom)

        # editable
        self.edit = tk.BooleanVar()
        self.edit.set(inits.get('edit'))

        # mark as played if you unload a song past this point
        self.played_yview = inits.get('played_yview')

        # mark as played if you unload a song after it was loaded for this many seconds.
        # None = disable
        self.played_seconds = inits.get('played_seconds')

        # TODO: much of this should be stored in a setlist object, not settings
        self.city = tk.StringVar()
        self.city.set(inits.get('city'))

        self.venue = tk.StringVar()
        self.venue.set(inits.get('venue'))

        # people / orgs to thank
        self.thanks = tk.StringVar()
        self.thanks.set(inits.get('thanks'))
        
        # dict of {musician: blurb}
        self.band = inits.get('band')
        # construct muso from the dict "musician (blurb)" or something
        self.muso = tk.StringVar()
        self.muso.set(inits.get('muso'))

        # list of guests, pointer for selected guest
        self.guest_list = inits.get('guest_list')

        self.guest = tk.StringVar()
        self.guest.set(inits.get('guest'))

        # define colors in the setlist.
        # TODO: get these into custom settings pattern
        self.colors = SetlistColors(self.settings, name)

class SetlistColors(SettingsBaseClass):
    """Text styles for setlist."""

    def __init__(self, settings, name):
        SettingsBaseClass.__init__(self, settings, name)

        self.default = 'light grey'
        self.skipped = 'dark grey'
        self.previous = 'pink'
        self.nextup = 'light yellow'
        self.current = 'light green'

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
        self.styles = ['bold', 'italic', 'underline', 'strike', 'size']
        self.types = ['chord', 'key', 'lyric', 'slashchord', 'bar', 'bvs', 'header', 'ws', 'nl', 'typo']

        # tag properties go here. value is kwargs passed to configure_text_tags in loader
        # TODO: will be some variation in tag color between talent and monitor (ie. there will be some
        # invisible text options on talent). separate dict for those.

        # test font
        # bold_font = font.Font(None)

        # TODO: may need to separate out the non-color tags due to tkinter implementation
        self.tags = {
            # styles
            # TODO: tuples should reference variables 
            'bold': {"font": ("menlo", "24", "bold")},
            'italic': {"font": "italic"},
            'underline': {"font": "underline"},
            # TODO: strikethru
            # TODO: size, linked to the size scale calc.
            # TODO: alternate size setting for monitor

            # types
            "lyric": {'foreground':'white'},
            "chord": {'foreground':'light blue'},
            "slashchord": {'foreground':'light blue'},
            "key": {'foreground':'lime'},
            "bar": {'foreground': 'light blue'},
            "nl": {},
            "ws": {},
            "header": {'foreground': 'orange'},
            "bvs": {'foreground': 'yellow'},
            }

        self.special = {
            'operator': lambda talent: {"foreground": "black"} if talent else {"foreground": "grey"},
        }

        self.systemWindowBackgroundColor = 'light grey' # TODO: get actual reference working

class WorkspaceSettings(SettingsBaseClass):
    """Class for workspace settings."""

    def __init__(self, settings, name):
        SettingsBaseClass.__init__(self, settings, name)

        self.defaults = {
        # autosave_gig_id keeps workspace autosaves distinct from the last
        # loaded gig. all assets are duplicated for autosaves save so internal
        # changes don't mess up the gig assets.
        'autosave_gig_id': None,
        # commit_gig_id is where workspace overwrites when you "Save Gig".
        # all assets are duplicated for this save, and then any orphaned
        # assets are garbage collected.
        'commit_gig_id': None
        }

class LibrarySettings(SettingsBaseClass):
    """Class for library settings, especially read/write behaviors."""

    def __init__(self, settings, name):
        SettingsBaseClass.__init__(self, settings, name)

        self.defaults = {
        'overwrite_songs': False,
        'overwrite_setlists': False,
        'cue_selection': False,
        }

        inits = merge(self.defaults, self.custom)

        # when enabled, saving a song / setlist with existing ID to library
        # will overwrite the song / setlist at that ID. when disabled, a
        # new ID will be generated, potentially creating duplicates, but
        # ensuring that references are preserved across all setlists.
        self.overwrite_songs = tk.BooleanVar()
        self.overwrite_songs.set(inits.get('overwrite_songs'))

        self.overwrite_setlists = tk.BooleanVar()
        self.overwrite_setlists.set(inits.get('overwrite_setlists'))

        # when enabled, when selecting a song in lib manager, it will be cued.
        self.cue_selection = tk.BooleanVar()
        self.cue_selection.set(inits.get('cue_selection'))
        self.cue_selection.trace(
            "w", lambda *args: self.update("cue_selection", self.cue_selection.get())
            )

