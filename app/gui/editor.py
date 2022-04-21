import tkinter as tk
from tkinter import messagebox
import time
import logging

from gui.prompttoolbar import PromptToolBar
from gui.edittoolbar import EditToolBar
from tools.apppointers import AppPointers

# TODO: change the name of this to Editor, and its instance in app
# to editor. Will require fixing a bunch of references but will be
# less confusing in the long run.

# helpers
def toggle_bool(arg):
    return not arg


class EditorMonitor(tk.Frame, AppPointers):
    """Class for Text field that shows
    what the talent is seeing on the Teleprompter."""

    def __init__(self, gui, *args, **kwargs):
        tk.Frame.__init__(
            self,
            gui.root,
            highlightbackground="grey",  # when frame is out of focus
            highlightcolor="lightgreen",  # when frame is in focus
            highlightthickness=10,  # border width
            # background='black'
        )
        AppPointers.__init__(self, gui)

        # relevant frame parameters
        self._song = None
        self.load_time = time.time()
        self.running = self.settings.scroll.running
        self.editable = self.settings.edit.enabled
        self.tfollow = self.settings.edit.talent_follows_monitor_when_editing
        self.color_tags = self.settings.tags.tags

        # pointers TODO: probably not explicitly needed
        self.sel_start = None
        self.sel_end = None
        self.cursor_pos = (
            None  # TODO: implement this can probably just call text directly
        )
        self.selected_text = None

        self.toolbar = Toolbar(self)
        self.toolbar.grid(row=0, column=0, columnspan=5)

        self.scrollbar = tk.Scrollbar(self, orient="vertical")
        self.scrollbar.grid(row=1, column=5, sticky="nesw")

        self.text = tk.Text(
            self,
            font=self.settings.fonts.monitor,
            height=12,
            width=45,
            bg="black",
            fg="white",
            state="disabled",
            insertbackground="pink",
            borderwidth=0,
            highlightbackground="black",
            yscrollcommand=self.scrollbar.set,
            wrap="none",
            undo=True,
        )
        self.text.grid(row=1, column=0, columnspan=5, sticky="nesw")

        self.titlebar = TitleBar(self)
        self.titlebar.grid(row=2, column=0, columnspan=5, sticky="nesw")
        self.rowconfigure(1, weight=4)
        self.rowconfigure(2, weight=3)

        # TODO: move all this,should not live here. will need to update local fns.
        self.menu = RightClickMenu(self)

        # scrollbar
        self.scrollbar.config(command=self.text.yview)

        # callbacks
        self.deck.add_callback("live", self.push)
        self.settings.fonts.monitor.add_callback(self.refresh_font)
        self.editable.trace("w", self.after_edit_toggle)

        # config scroll behavior
        # self.scroll_action = self.match_sibling_yview
        self.scroll_action = self.do_nothing

    def do_nothing(self):
        pass
        
    def refresh_font(self):
        self.suite.text.tag_configure("size", font=self.settings.fonts.monitor)

    def get_font_family(self):
        """Get font family from settings."""
        return self.settings.fonts.monitor.family.get()

    def on_focus(self):
        """When you click in the widget, do the tkinter focus_set() method
        and also update the deck."""
        self.focus_set()
        self.app.deck.focused = self.song

    def push(self):
        """Push live song to monitor with appropriate view reset."""
        live, previous = self.deck.live, self.deck.previous 
        reset_view = False if live is previous else True
        self.loader.push(frame=self, song=live, reset_view=reset_view)

    @property
    def song(self):
        return self._song

    @song.setter
    def song(self, new):
        """When you change the song, update loaded time."""
        if new is self._song:
            return
        self.try_mark_played(new)
        self._update_titlebar(new)
        self._update_load_time()
        self._song = new

    def _update_load_time(self):
        self.load_time = time.time()

    def _update_titlebar(self, song):
        title = song.name if song else ""
        self.titlebar.name.config(text=title)

    def try_mark_played(self, song):
        """Mark song as played in setlist if it was loaded for
        enough time or yview is substantially below the top."""
        if song and self.play_checks():
            self.gig.markers["played"].append(song)

    def play_checks(self):
        """Return True if conditions are met to mark song as played"""
        if self.elapsed_time() > self.settings.setlist.played_seconds.get():
            return True
        if self.monitor.text.yview()[0] > self.settings.setlist.played_yview.get():
            return True

    def elapsed_time(self):
        """Get elapsed time from last load action."""
        return time.time() - self.load_time

    def double_clicked_text(self, event):
        """Force focus to text frame on double click."""
        self.text.focus_set() if self.editable.get() else None

    def selection_info(self):
        """For now, print information about selected text. Adapt this later to apply tags."""
        if self.text.tag_ranges(tk.SEL):
            first, last = tk.SEL_FIRST, tk.SEL_LAST
            # selected string, start and end coordinates
            self.selected_text = self.text.get(first, last)
            self.sel_start = self.text.index(first)
            self.sel_end = self.text.index(last)

            # logging.info(f'selection text "{self.selected_text}"')
            # logging.info(f'selection pointers: {self.sel_start}, {self.sel_end}'')
        else:
            self.selected_text = None
            self.sel_start = None
            self.sel_end = None

        return (self.sel_start, self.sel_end, self.selected_text)

    def do_edit_toggle(self):
        self.editable.set(not self.editable.get())

    def after_edit_toggle(self, event, *args):
        """Toggle editing from keyboard shortcut."""

        if self.editable.get():
            self.config(highlightcolor="yellow", highlightbackground="#6E5D00")
            self.text.config(state="normal")
            self.tools.scroll.running.set(False)
        else:
            self.config(highlightcolor="light green", highlightbackground="dark grey")
            self.text.config(state="disabled")
        self.on_focus()

    def update_talent_view(self, event):
        # Don't do this when the prompter is running!
        self.text.focus_set()

        # only update if prompter isn't running and edit is enabled.
        if not self.scroller.running.get() and self.editable.get():
            # delay slightly to guarantee accurate yview.
            self.gui.after(10, self.talent.match_sibling_yview)
            logging.info("talent snapped to mon")

    def match_sibling_yview(self):
        """Move monitor view to match talent view."""
        # TODO: rounding errors cause this to get inaccurate, especially when
        # the talent view is a dramatically different proportion. don't rely
        # on monitor view for scrolling, always look at talent.
        self.text.yview_moveto(self.talent.text.yview()[0])

    def match_target_yview(self, target):
        """Genericized match_sibling_yview method requiring target yview arg."""
        self.text.yview_moveto(target)     

    def refresh_while_editing(self, event):
        """Brute force talent refresh. Will completely clear and reload talent
        window every time an edit is made in editor. As text is lightweight,
        this is inefficient but works fine. Eventually do this more elegantly."""

        if not self.editable.get():
            return
        dump = self.text.dump("1.0", "end", tag=True, text=True)
        self.talent.receive_edits(dump)
        self.talent.match_sibling_yview() if self.tfollow else None

    @property
    def contents(self):
        # self.__contents = self.text.get(start)
        self._contents = self.app.active_text.get()
        return self._contents

    @contents.setter
    def contents(self, new):
        # TODO: move edit toggle to decorator
        edit_state = self.text.cget("state")
        self.text.config(state="normal")
        self.text.delete("1.0", "end")
        self.app.active_text.set(new)
        self.text.config(state=edit_state)

    def dump(self, tag=True) -> list:
        """Dump the text widget to a list."""
        return self.text.dump("1.0", "end", tag=tag, text=True)

    def try_reload_song(self):
        """Reload extant script from song object with prompt."""
        if messagebox.askokcancel("Confirm Reload", "Reload song? Changes will be lost."):
            self.tools.loader.push(frame=self, song=self.song, reset_view=False)

    def save_song(self):
        """Push tktext back to song obj."""
        self.tools.tk_text_interface.tkt_into_song(
            song=self.song,
            tkt=self.monitor.dump())


class RightClickMenu(tk.Frame, AppPointers):
    """Menu for when you right click within monitor frame."""

    def __init__(self, parent, *args, **kwargs):
        tk.Frame.__init__(self, parent)
        AppPointers.__init__(self, parent)

        # bookmark menu
        special_menu = tk.Menu(self.parent, title="Special")
        special_menu.add_command(label="Add Bookmark")  # bookmark format: @B
        # special_menu.add_command(label='Clear All Bookmarks')
        special_menu.add_separator()
        special_menu.add_command(label="City")
        special_menu.add_command(label="Venue")
        special_menu.add_command(label="Date")
        special_menu.add_command(label="Guest")
        special_menu.add_command(label="Thanks")

        # tag menu
        tag_menu = tk.Menu(self.parent, title="Tags")
        tag_menu.add_command(label="Clear")
        tag_menu.add_separator()
        tag_menu.add_command(
            label="Header", command=lambda: self.apply_tag(tag="header")
        )
        tag_menu.add_command(label="Lyric", command=lambda: self.apply_tag(tag="lyric"))
        tag_menu.add_command(label="BVs", command=lambda: self.apply_tag(tag="bvs"))
        tag_menu.add_command(label="Chord", command=lambda: self.apply_tag(tag="chord"))
        tag_menu.add_command(label="Key", command=lambda: self.apply_tag(tag="key"))

        # style menu
        style_menu = tk.Menu(self.parent, title="Style")
        style_menu.add_command(label="Clear")
        style_menu.add_separator()
        style_menu.add_command(
            label="Bold", command=lambda: self.apply_style(style="bold")
        )
        style_menu.add_command(
            label="Italic", command=lambda: self.apply_style(style="italic")
        )
        style_menu.add_command(
            label="Underline", command=lambda: self.apply_style(style="underline")
        )
        style_menu.add_command(
            label="Strikethru", command=lambda: self.apply_style(style="strikethru")
        )
        style_menu.add_separator()
        style_menu.add_command(label="Show")
        style_menu.add_command(label="Hide")
        style_menu.add_separator()
        style_menu.add_command(
            label="Operator Only", command=lambda: self.apply_style(style="operator")
        )

        # main menu
        main_menu = tk.Menu(self.parent, title="Edit")
        main_menu.add_checkbutton(
            label="Edit Mode",
            variable=self.settings.edit.enabled,
            command=self.on_edit_mode,
        )
        main_menu.add_separator()
        main_menu.add_command(label="Cut")
        main_menu.add_command(label="Copy")
        main_menu.add_command(label="Paste")
        main_menu.add_separator()
        main_menu.add_command(label="Find All")
        main_menu.add_separator()
        main_menu.add_cascade(label="Tag", menu=tag_menu)
        main_menu.add_cascade(label="Style", menu=style_menu)
        main_menu.add_cascade(label="Special", menu=special_menu)
        main_menu.add_separator()
        main_menu.add_command(label="Sub Enharmonics")
        # main_menu.add_separator()
        # main_menu.add_command(label="Get Info")

        self.main_menu = main_menu

    def do_popup(self, event):
        try:
            self.main_menu.tk_popup(event.x_root, event.y_root)
        finally:
            self.main_menu.grab_release()


    # TODO: chop up these next few massive methods...
    def apply_tag(self, tag):
        """Apply a tag to selected text."""

        # get selection and textbox
        start, end, contents = self.suite.selection_info()

        # return if nothing selected or not in edit mode
        if not self.suite.editable:
            return

        # get text frames
        mon_text = self.suite.text
        talent_text = self.talent.text
        texts = [mon_text, talent_text]

        # if nothing is selected, select the cursor pos
        if not start:
            start = self.suite.text.index("insert")
            end = self.suite.text.index("insert")

        # expand selection to whole word
        start = mon_text.index(f"{start} wordstart")
        end = mon_text.index(f"{end} wordend")

        # TODO: on words with apostrophes like "don't" need to expand past
        # the apostrophe to cover whole word. Same goes for keys.

        for text in texts:
            # get editable state
            state = text.cget("state")

            # make editable
            text.config(state="normal")

            # remove any old tags
            self.remove_tags_in_selection(text=text, start=start, end=end)

            # new tag
            text.tag_add(tag, start, end)

            # restore editable state
            text.config(state=state)

    def remove_tags_in_selection(self, text, start, end):
        """Remove tags in selection."""

        for tag in self.suite.color_tags.keys():
            text.tag_remove(tag, start, end)

    def apply_style(self, style):
        """Apply style tags to selected text."""

        # TODO: will be similar to apply tag, so try to combine into one function once both
        # are working.
        # TODO: if a style tag bisects a transposible word, heal it and style the whole thing.

        # get selection and textbox
        start, end, contents = self.suite.selection_info()

        # return if nothing selected or not in edit mode
        if not contents or not self.suite.editable:
            return

        # get text frames
        mon_text = self.suite.text
        talent_text = self.talent.text
        texts = [mon_text, talent_text]

        # expand selection to whole word
        start = mon_text.index(f"{start} wordstart")
        end = mon_text.index(f"{end} wordend")

        logging.info(f"applying style {style} to text {contents}")

        for text in texts:
            # get editable state
            state = text.cget("state")

            # make editable
            text.config(state="normal")

            # for styles, you don't want to remove old tags.
            # self.remove_tags_in_selection(text=text, start=start, end=end)

            # new tag
            text.tag_add(style, start, end)

            # restore editable state
            text.config(state=state)

    def on_edit_mode(self):
        self.gui.menu.on_edit_mode()


class TagMenu(tk.Frame):
    def __init__(self, parent, *args, **kwargs):
        tk.Frame.__init__(self, parent)

        self.parent = parent
        self.app = parent.app
        self.suite = parent.suite

        menu = tk.Menu(self.parent, title="Tag")


class TitleBar(tk.Frame):
    """Frame for the titlebar."""

    def __init__(self, parent):
        tk.Frame.__init__(self, parent)

        self.parent = parent
        self.app = parent.app
        self.suite = parent.suite

        # widgets
        self.label = tk.Label(self, text="LIVE:")
        self.label.pack(side="left", anchor="w")
        self.name = tk.Label(self)
        self.name.pack(side="left", anchor="w", expand=True)


class Toolbar(tk.Frame, AppPointers):
    """Holds the prompt and edit toolbars, showing one or the other
    depending on edit mode parameter."""

    def __init__(self, parent):
        tk.Frame.__init__(self, parent)
        AppPointers.__init__(self, parent)

        self.edit_toolbar = EditToolBar(self)
        self.prompt_toolbar = PromptToolBar(self)

        self.prompt_toolbar.pack(
            # fill="both",
            expand=False,
            anchor="w",
        )

        # refresh shown toolbar when edit mode changes
        self.app.settings.edit.enabled.trace("w", lambda *args: self.toggle_bar())

    def toggle_bar(self):
        """Show the approrpiate toolbar depending on mode."""
        if self.app.settings.edit.enabled.get():
            self.prompt_toolbar.forget()
            self.edit_toolbar.pack()
        else:
            self.edit_toolbar.forget()
            self.prompt_toolbar.pack()

