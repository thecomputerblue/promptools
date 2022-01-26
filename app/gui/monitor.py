import tkinter as tk
import time
import logging

# TODO: change the name of this to Editor, and its instance in app
# to editor. Will require fixing a bunch of references but will be
# less confusing in the long run.

class TalentMonitor(tk.Frame):
    """Class for Text field that shows
    what the talent is seeing on the Teleprompter."""

    def __init__(self, parent, *args, **kwargs):
        tk.Frame.__init__(
            self,
            parent.frame,
            highlightbackground="grey",  # when frame is out of focus
            highlightcolor="lightgreen",  # when frame is in focus
            highlightthickness=10,  # border width
            # background='black'
        )

        # context pointers
        self.parent = parent
        self.app = parent
        self.suite = self
        self.settings = self.app.settings

        # relevant frame parameters
        self.song = None
        self.loaded = time.time()
        self.running = self.settings.scroll.running
        self.editable = self.settings.editor.enabled
        self.tfollow = self.settings.editor.talent_follows_monitor_when_editing
        self.color_tags = self.settings.tags.types

        # pointers TODO: probably not explicitly needed
        self.sel_start = None
        self.sel_end = None
        self.cursor_pos = None # TODO: implement this can probably just call text directly
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

        rates = self.settings.scroll.rates
        scrollvar = self.settings.scroll.current
        self.autoscroll_scale = tk.Scale(
            self,
            from_=0,
            to=len(rates) - 1,  # adjust based on global scroll scale
            orient="horizontal",
            showvalue=0,
            sliderlength=20,
            length=500,
            variable=scrollvar
        )

        self.default_autoscroll_speed()

        # Speed label
        self.speed_label = tk.Label(
            self,
            text="Autoscroll speed",
        )

        # self.autoscroll_scale.grid(row=3, column=1)
        # self.speed_label.grid(row=3, column=1)

        self.menu = RightClickMenu(self)

        # bind callbacks

        # key bindings

        # scrollbar
        self.scrollbar.config(command=self.text.yview)

        # Key bindings to update talent view while editing.
        self.text.bind("<KeyRelease>", self.refresh_while_editing)
        # TODO: simpler method for this one
        # self.text.bind("<Button-1>", self.update_talent_view)
        self.text.bind("<MouseWheel>", self.update_talent_view)

        #edit toggle
        self.text.bind("<Command-e>", self.toggle_edit)
        self.bind("<Command-e>", self.toggle_edit)

        # self.text.bind("<space>", lambda _: self.toggle_scroll())
        # Make it so clicking in the talent window gives frame focus.
        self.bind("<Button-1>", lambda _: self.focus_set())
        self.text.bind("<Button-1>", lambda _: self.focus_set())

        # Scroll key bindings. These need to be bound to inner & outer frame
        # TODO: figure if there is a way to bind just once
        self.bind("<space>", lambda _: self.toggle_scroll())
        self.text.bind("<space>", lambda _: self.toggle_scroll())

        self.bind("<KeyPress-Shift_L>", lambda _: self.shift_scroll_on())
        self.text.bind("<KeyPress-Shift_L>", lambda _: self.shift_scroll_on())

        self.bind("<KeyRelease-Shift_L>", lambda _: self.shift_scroll_off())
        self.text.bind("<KeyRelease-Shift_L>", lambda _: self.shift_scroll_off())

        self.bind("<KeyPress-Shift_R>", lambda _: self.shift_scroll_on())
        self.text.bind("<KeyPress-Shift_R>", lambda _: self.shift_scroll_on())

        self.bind("<KeyRelease-Shift_R>", lambda _: self.shift_scroll_off())
        self.text.bind("<KeyRelease-Shift_R>", lambda _: self.shift_scroll_off())

        self.bind("<.>", lambda _: self.arrow_scroll(direction="down"))
        self.text.bind("<.>", lambda _: self.arrow_scroll(direction="down"))

        self.bind("<,>", lambda _: self.arrow_scroll(direction="up"))
        self.text.bind("<,>", lambda _: self.arrow_scroll(direction="up"))

        # Binding to get coords of selected text. Will use this later for applying color tags.
        self.text.bind("<ButtonRelease>", lambda _: self.selection_info())

        self.text.bind("<Double-Button-1>", self.double_clicked_text)
        # self.text.bind("<BackSpace>", self.on_backspace)

        # binding for popup menu
        self.text.bind("<Button-2>", self.menu.do_popup)

        # callback
        self.app.deck.add_callback('live', self.push)

    def push(self):
        """Push live song to monitor with appropriate view reset."""

        live = self.app.deck.live
        prev = self.app.deck.previous
        reset_view = False if live is prev else True
        
        self.app.tools.loader.push(frame=self, song=live, reset_view=reset_view)

    @property
    def song(self):
        return self._song

    @song.setter
    def song(self, new):
        """When you change the song, update loaded time."""

        if not new:
            self._song = None
            return

        if new is self._song:
            return

        self.mark_played()
        self._song = new
        self.loaded = time.time()
        self.titlebar.name.config(text=new.name)
        # self.app.setlist.listbox_update()

    def commit_changes_to_song(self):
        """Apply any edits made in monitor to the song object."""

        # song = self.app.deck.live
        song = self.song
        dump = self.text.dump("1.0", "end", tag=True, text=True)
        factory = self.app.tools.factory

        # replace song object
        # TODO: best
        self.song = factory.update_song(old=song, tk_text_dump=dump)
        # song = factory.update_song(old=song, tk_text_dump=dump)
    
    def mark_played(self):
        """Mark song as played in setlist if it was loaded for enough time or yview is substantially below the top."""

        # TODO: might make more sense in the setlist pane
        song = self._song

        settings = self.app.settings.setlist
        m = self.app.setlist.manager       

        elapsed = self.elapsed_time()
        seconds = settings.played_seconds
        yview_thresh = settings.played_yview
        yview = self.app.monitor.text.yview()[0]

        # tests for marking as played. if any return True, mark as played
        tests = (
        lambda:  elapsed > seconds,
        lambda: yview > yview_thresh
        )

        if song and song.name in m.names:
            for test in tests:
                if test():
                    m.played.append(song.name)
                    break

    def elapsed_time(self):
        """Get elapsed time from last load action."""

        return time.time() - self.loaded

    def double_clicked_text(self, event):
        """Force focus to text frame on double click."""

        self.text.focus_set() if self.editable else None

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

    def y_advance(self, direction="down"):
        """Advance scroll based on pixels size."""

        # TODO: i think this is duplicated somewhere...
        pixels = self.settings.scroll.pixels
        scroll = -pixels if direction == "up" else pixels
        self.text.yview_scroll(scroll, "pixels")

    def toggle_bool(self, arg):

        return False if arg else True

    def shift_scroll_on(self, event=None):
        """Holding shift scrolls prompter."""

        if self.editable.get():
            return

        self.running.set(True)
        self.schedule_scroll()
        logging.info("shift_scroll_on")

    def shift_scroll_off(self, event=None):
        """Releasing shift stops prompter."""
        self.running.set(False)
        logging.info("shift_scroll_off")

    def toggle_scroll(self):
        """Toggle autoscroll."""

        if self.editable.get():
            return

        scroll = self.app.settings.scroll

        if scroll.running.get():
            scroll.running.set(False)
            logging.info('toggle_scroll OFF')
        else:
            scroll.running.set(True)
            self.schedule_scroll()
            logging.info('toggle_scroll ON')

    def arrow_scroll(self, direction):
        """Scroll behavior for arrow keys arrow."""

        self.app.tools.scroll.chunk_scroll(direction)

    def toggle_edit(self, event):
        """Toggle editing from keyboard shortcut."""

        # pass True so it knows to manually invert the setting.
        self.app.menu.on_edit_mode(keyboard=True)

    def schedule_scroll(self):
        """Run autoscroll."""

        # TODO: pass this along instead of storing explicitly
        self.app.tools.scroll.start_scroll()

    def update_talent_view(self, event):
        # Don't do this when the prompter is running!
        self.text.focus_set()

        # only update if prompter isn't running and edit is enabled.
        if not self.running.get() and self.editable.get():
            # delay slightly to guarantee accurate yview.
            self.app.after(10, self.app.talent.match_sibling_yview)
            logging.info('talent snapped to mon')

    def match_sibling_yview(self):
        """Move monitor view to match talent view."""

        # TODO: rounding errors cause this to get inaccurate, especially when
        # the talent view is a dramatically different proportion. don't rely
        # on monitor view for scrolling, always look at talent.

        # TODO: update reference to sibling.
        talent_view = self.app.talent.text.yview()

        # get view area
        top, bottom = talent_view
        # mid = (top + bottom) / 2

        self.text.yview_moveto(top)

        # self.text.yview_moveto(self.app.talent.text.yview()[0])

    def refresh_while_editing(self, event):

        if not self.editable.get():
            return

        # Dump monitor contents into talent window.
        # TODO: replace edited text only
        dump = self.text.dump("1.0", "end", tag=True, text=True)
        self.app.talent.receive_edits(dump)

        # TODO: toggle for follow behavior.
        if self.tfollow:
            self.app.talent.match_sibling_yview()

    # def talent_match_monitor_yview(self):
    #     """Move talent view to monitor view."""
    #     self.app.talent.text.yview_moveto(self.text.yview()[0])

    def default_autoscroll_speed(self):
        """Set default autoscroll speed."""
        rates = self.settings.scroll.rates
        # Float position of slider with 1 being far right.
        pos = 0.85
        formula = int((len(rates) * pos))
        self.autoscroll_scale.set(formula)

    @property
    def contents(self):
        # self.__contents = self.text.get(start)
        self._contents = self.app.active_text.get()
        return self._contents

    @contents.setter
    def contents(self, new):
        # Get monitor edit state.
        edit_state = self.text.cget("state")

        # Enable editing to clear field.
        self.text.config(state="normal")

        # Clear old monitor contents.
        self.text.delete("1.0", "end")

        self.app.active_text.set(new)

        # Reset monitor edit state
        self.text.config(state=edit_state)

    def add_to_list(self, target):
        """Add current song to target list (collection)."""

        if not self.song:
            return

        factory = self.app.tools.factory

        self.commit_changes_to_song()

        target.add_song(song=self.song)

    def get_info(self):
        """Get info from current song obj."""
        return self.song.meta.info if self.song else None

    def update_marks(self):
        self.app.setlist.update_marks()


class RightClickMenu(tk.Frame):
    """Menu for when you right click within monitor frame."""

    def __init__(self, parent, *args, **kwargs):
        tk.Frame.__init__(self, parent)

        self.parent = parent
        self.app = parent.app
        self.suite = parent.suite
        self.settings = self.app.settings

        # bookmark menu
        special_menu = tk.Menu(self.parent, title='Special')
        special_menu.add_command(label='Add Bookmark') # bookmark format: @B
        # special_menu.add_command(label='Clear All Bookmarks')
        special_menu.add_separator()
        special_menu.add_command(label="City")
        special_menu.add_command(label="Venue")
        special_menu.add_command(label="Date")
        special_menu.add_command(label="Guest")
        special_menu.add_command(label="Thanks")

        # tag menu
        tag_menu = tk.Menu(self.parent, title='Tags')
        tag_menu.add_command(label='Clear')
        tag_menu.add_separator()
        tag_menu.add_command(label='Header', command=lambda: self.apply_tag(tag='header'))
        tag_menu.add_command(label='Lyric', command=lambda: self.apply_tag(tag='lyric'))
        tag_menu.add_command(label='BVs', command=lambda: self.apply_tag(tag='bvs'))
        tag_menu.add_command(label='Chord', command=lambda: self.apply_tag(tag='chord'))
        tag_menu.add_command(label='Key', command=lambda: self.apply_tag(tag='key'))

        # style menu
        style_menu = tk.Menu(self.parent, title='Style')
        style_menu.add_command(label='Clear')
        style_menu.add_separator()
        style_menu.add_command(label='Bold', command=lambda: self.apply_style(style='bold'))
        style_menu.add_command(label='Italic', command=lambda: self.apply_style(style='italic')) 
        style_menu.add_command(label='Underline', command=lambda: self.apply_style(style='underline'))
        style_menu.add_command(label='Strikethru', command=lambda: self.apply_style(style='strikethru'))
        style_menu.add_separator()
        style_menu.add_command(label='Show')
        style_menu.add_command(label='Hide')
        style_menu.add_separator()
        style_menu.add_command(label='Operator Only', command=lambda: self.apply_style(style='operator'))

        # main menu
        main_menu = tk.Menu(self.parent, title='Edit')
        main_menu.add_checkbutton(label="Edit Mode", variable=self.settings.editor.enabled, command=self.on_edit_mode)
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

    def apply_tag(self, tag):
        """Apply a tag to selected text."""

        # get selection and textbox
        start, end, contents = self.suite.selection_info()


        # return if nothing selected or not in edit mode
        if not self.suite.editable:
            return

        # get text frames
        mon_text = self.suite.text
        talent_text = self.app.talent.text
        texts = [mon_text, talent_text]

        # if nothing is selected, select the cursor pos
        if not start:
            start = self.suite.text.index('insert')
            end = self.suite.text.index('insert')

        # expand selection to whole word
        start = mon_text.index(f'{start} wordstart')
        end = mon_text.index(f'{end} wordend')

        # TODO: on words with apostrophes like "don't" need to expand past
        # the apostrophe to cover whole word. Same goes for keys.

        for text in texts:
            # get editable state
            state = text.cget('state')

            # make editable
            text.config(state='normal')

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
        talent_text = self.app.talent.text
        texts = [mon_text, talent_text]

        # expand selection to whole word
        start = mon_text.index(f'{start} wordstart')
        end = mon_text.index(f'{end} wordend')

        logging.info(f'applying style {style} to text {contents}')

        for text in texts:
            # get editable state
            state = text.cget('state')

            # make editable
            text.config(state='normal')

            # for styles, you don't want to remove old tags.
            # self.remove_tags_in_selection(text=text, start=start, end=end)

            # new tag
            text.tag_add(style, start, end)

            # restore editable state
            text.config(state=state)

    def on_edit_mode(self):
        self.app.menu.on_edit_mode()


class TagMenu(tk.Frame):

    def __init__(self, parent, *args, **kwargs):
        tk.Frame.__init__(self, parent)

        self.parent = parent
        self.app = parent.app
        self.suite = parent.suite 

        menu = tk.Menu(self.parent, title='Tag')


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


class Toolbar(tk.Frame):
    """Holds the prompt and edit toolbars, showing one or the other
    depending on edit mode parameter."""

    def __init__(self, parent):
        tk.Frame.__init__(self, parent)

        self.parent = parent
        self.app = parent.app
        self.suite = parent.suite

        self.edit = EditToolBar(self)
        self.prompt = PromptToolBar(self)

        self.prompt.pack(fill="both", expand=True, anchor="w")

        # trace editmode and update view when it changes.
        self.editmode = self.app.settings.editor.enabled
        self.editmode.trace("w", lambda *args: self.toggle_bar())

    def toggle_bar(self):
        """Show the approrpiate toolbar depending on mode."""

        # logging.info('EDIT TOGGLE triggered toggle_bar')
        if self.editmode.get():
            self.prompt.forget()
            self.edit.pack()
        else:
            self.edit.forget()
            self.prompt.pack()


class PromptToolBar(tk.Frame):
    """Toolbar shown in prompt mode."""

    def __init__(self, parent):
        tk.Frame.__init__(self, parent)

        self.parent = parent
        self.app = parent.app
        self.suite = parent.suite

        self.placeholder = tk.Label(self, text="PLACEHOLDER FOR PROMPT TOOLBAR")
        self.placeholder.pack(expand=True, fill="both", anchor="w")

class EditToolBar(tk.Frame):
    """Toolbar shown in edit mode."""

    def __init__(self, parent):
        tk.Frame.__init__(self, parent)

        self.parent = parent
        self.app = parent.app
        self.suite = parent.suite

        self.placeholder = tk.Label(self, text="PLACEHOLDER FOR EDIT TOOLBAR")
        self.placeholder.pack(expand=True, fill="both", anchor="w")
