import logging
from tools.song import Song
from tkinter import font

from tools.apppointers import AppPointers
# helpers
def unpack_pos(pos: str) -> list:
    """Convert tkinter pos to line and column integers.
    Does not subtract 1 (tkinter starts line count at 1)."""

    line, col = pos.split(".")
    return int(line), int(col)

def pack_pos(line: int, col: int) -> str:
    """Merge line and column integers into tkinter format.
    Does NOT add 1, (tkinter start line count at 1)."""

    return str(line) + "." + str(col)

class LoadTool(AppPointers):
    """Contain functions for loading songs between frames."""

    def __init__(self, app):
        AppPointers.__init__(self, app)

    def preserve_sel(method):
        """Preserve selection while executing a method."""
        def inner(self, *args, **kwargs):

            logging.info('preserve_sel in LoadTool')
            event = kwargs.get('event')
             # TODO: make sure event.widget is a listbox before trying to get curselection
            sel = event.widget.curselection() if event else None       

            method(self, *args, **kwargs)

            event.widget.selection_set(sel) if event else None
            event.widget.activate(sel) if event else None

        return inner


    def with_tk_text(self, widget, wrapped, reset=None):
        """Snapshot a text widget, perform an action, restore state.
        Pass wrapped functiona as lambda with arguments."""

        # TODO: change to decorator fn

        # reset view if cue and live mismatch
        if reset is None:
            reset = False if self.app.deck.live is self.app.deck.cued else True

        edit_state, yview = self.get_state_and_yview(widget)
        self.clear_tktext(widget)

        # do the lambda
        wrapped()

        widget.config(state=edit_state)
        widget.yview_moveto(0) if reset else widget.yview_moveto(yview[0])

    def clear_tktext(self, tktext):
        """Clear contents of a target frames text box."""

        tktext.config(state="normal")
        tktext.delete("1.0", "end")

    def get_state_and_yview(self, widget):
        """Get edit state and yview from text widget."""

        return widget.cget("state"), widget.yview()

    def update_song_mods(self, song: Song, key: str):
        """Pass current transpose / formatting settings
        to song so it is up to date when shown."""

        # TODO: redundant, weed this out
        self.transpose_song(song=song, key=key) if self.keychange_enabled() else None

    def transpose_song(self, song, key):
        """Pass song & key into the transposer."""

        transposer = self.app.tools.transposer
        transposer.transpose_tk(song=song, target=key)

    def reset_song(self, song):
        """Reset song to original key."""

        self.app.tools.transposer.reset(song=song)

    def load_with_settings(self, frame, song):
        """Show song with the correct color, etc. settings."""

        # TODO: refactor
        if not self.song_changes_enabled():
            self.show_raw(frame, song)
        elif self.colors_enabled():
            self.configure_text_tags(frame.text)
            self.app.tools.transposer.show_colors_tk(frame, song)
        else:
            self.show_plain(self, song)

        # size tag across entire doc makes it scalable
        # TODO: check for extant size tag and don't apply if it already exists
        self.add_size_tag(frame.text)

    def add_size_tag(self, text):
        """Tag tk_text contents with size tag so auto-resizer works."""

        text.tag_add("size", "1.0", "end")

    def song_changes_enabled(self):
        """Return True if Nashville mode or transposition enabled."""
        return (
            self.keychange_enabled() or self.nashmode_enabled() or self.colors_enabled()
        )

    def keychange_enabled(self):
        """Return True if keychange is enabled."""
        return self.app.settings.transposer.enabled.get()

    def nashmode_enabled(self):
        """Return True if Nashville mode enabled."""
        # TODO: un nest this toggle!
        return self.app.settings.transposer.nashville.get()

    def colors_enabled(self):
        """Return True if colors are enabled."""
        return not self.app.settings.importer.raw.get()

    def configure_text_tags(self, text, talent=False):
        """Apply tag settings to the tkinter text tags."""

        # get the tag dicts
        tags = self.app.settings.tags.tags
        special = self.app.settings.tags.special

        # configure tags with settings
        for k, v in tags.items():
            text.tag_configure(k, **v)

        # configure the special tags. if talent==True, some tags will
        # be assigned black foreground, and be invisible on talent monitor
        for k, v in special.items():
            # choose appropriate dict
            d = v(talent)
            text.tag_configure(k, **d)


    def get_key(self):
        """Return key from transposer if enabled, or 0 if disabled."""

        t = self.app.settings.transposer
        return t.key.get() if t.enabled.get() else '0'

    def push(self, frame, song, reset_view=None):
        """Push song to a target frame with settings."""

        logging.info('push in LoadTool')

        if not song:
            return

        # update the frame song reference to the new song
        frame.song = song        

        self.with_tk_text(
            widget=frame.text,
            wrapped=lambda: self.show_with_options(frame),
            reset=reset_view
            )

    def show_with_options(self, frame):
        # get the target key when enabled, or reset transposition if not.
        song = frame.song
        key = self.get_key()

        # TODO: preview transposition hinges on this call. backwards logic...
        self.update_song_mods(song, key)

        strategies = {
        self.show_raw_conditions: self.show_raw,
        self.show_color_conditions: self.show_colors,
        self.show_plain_conditions: self.show_plain
        }

        for k,v in strategies.items():
            v(frame, song) if k() else None

        self.add_size_tag(frame.text)

        # TODO: decorator wrapper function for frame state
        # reset undo stack.
        frame.text.edit_reset()

    def show_raw(self):
        # TODO: write new show raw method
        pass

    def show_raw_conditions(self):
        return not (self.keychange_enabled() or self.nashmode_enabled() or self.colors_enabled())

    def show_color_conditions(self):
        return self.colors_enabled()

    def show_plain(self):
        # TODO: write new show plain method
        pass

    def show_plain_conditions(self):
        return not (self.colors_enabled())

    def show_colors(self, frame, song): 

        self.configure_text_tags(frame.text)
        self.app.tools.transposer.show_colors_tk(frame, song)

    def cue_from_file(self, filename=None):
        """Creates song obj from file and pushes to cue."""

        file = self.app.browser.files.path
        song = self.app.tools.factory.new_song(file=file)
        self.app.deck.cued = song

    def cue_from_library(self, tree_entry):
        """Cue a library song from a tree_entry."""
        
        # get pass the tree_entry to the db_interface, returning a song obj from lib
        # push the song obj to deck

    def clone_tk_text(self, source, dest):
        """Clone a tk_text frames contents & formatting to another."""

        dump = source.dump("1.0", "end", tag=True, text=True)
        self.with_tk_text(
            widget=dest,
            wrapped=lambda: self.insert_tk_text(dest, dump)
            )

    def insert_tk_text(self, widget, dump):
        """Insert tk_text dump into a text widget."""
        # TODO: think this is duplicated...

        tag = ""

        for e in dump:
            if e[0] == "tagon":
                tag = e[1]
            elif e[0] == "text":
                widget.insert("end", e[1], tag)

        widget.tag_add("size", "1.0", "end")

        return widget

    @preserve_sel
    def load_cued_to_live(self, event=None):
        """Push cued song to live."""
        logging.info('load_cued_to_live in LoadTool')
        self.app.deck.live = self.app.deck.cued

    def get_key(self):
        """Return target key from transposer, or '0' if not enabled."""
        transposer = self.app.settings.transposer

        if transposer.enabled:
            return transposer.key.get()

        return '0'
