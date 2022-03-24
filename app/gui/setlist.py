import tkinter as tk
import time
import logging

# helpers
def strike(text):
    """Strikethru text."""
    # TODO: looks weird
    return ''.join([u'\u0336{}'.format(c) for c in text])

def number(n: int, name: str) -> str:
    """Return item formatted for list."""
    # TODO: styles
    return '(' + str(n) + ') ' + name

class SetlistFrame(tk.Frame):
    """Frame for showing the active setlists."""

    def __init__(self, parent, *args, **kwargs):
        tk.Frame.__init__(
            self, parent, highlightthickness=2, borderwidth=2, relief="sunken"
        )

        # context
        self.parent = parent
        self.app = parent.app
        self.suite = self
        self.settings = self.app.settings.setlist
        self.tools = self.app.tools.gui
        self.gig = self.app.data.gig

        # live setlist & songs
        self.deck = self.app.deck

        # widgets
        self.header = SetlistHeader(self)
        self.header.pack(side="top", anchor="w")

        self.listbox = tk.Listbox(
            self, width=40, height=20, bg="lightgrey", fg="black", exportselection=False
        )
        # self.listbox.grid(row=2, column=0, columnspan=4, sticky="nesw")
        self.listbox.pack(side="top", fill="both", expand=True)
        self.listbox.bind("<<ListboxSelect>>", self.on_listbox_select)

        self.controls = SetlistControlRow(self)
        self.controls.pack(anchor="s", side="left", fill="both", expand=True)

        # popup menu
        self.menu = RightClickMenu(self)
        self.listbox.bind("<Button-2>", self.right_click)

        # callbacks so it refreshes whenever something changes
        self.deck.add_callback("live", self.listbox_update)
        self.gig.add_callback(self.listbox_update)

        # make strategies for updating listbox
        self.make_listbox_strategies()

        # refresh once to show anything that was already loaded at init
        self.listbox_update()

    # TODO: better method than a bunch of properties?

    @property
    def data(self):
        return self.gig.setlists

    @property
    def pool(self):
        return self.gig.pool
    
    @property
    def markers(self):
        return self.gig.markers

    @property
    def live(self):
        return self.gig.live_setlist

    @property
    def songs(self):
        return self.live.songs
    
    def preserve_sel(method):
        """Capture then restore listbox selection after executing inner method"""
        # TODO: move to guitools

        def inner(self, *args, **kwargs):

            sel = self.tools.get_sel(self.listbox)
            method(self, sel, *args, **kwargs)
            self.tools.do_sel(self.listbox, sel) if sel is not None else None

        return inner

    def pass_sel(method):
        """Capture listbox selection and do decorated function only
        if there is a selection."""
        # TODO: move to guitools

        def inner(self, *args, **kwargs):
            sel = self.tools.get_sel(self.listbox)
            if sel is None:
                return
            method(self, sel, *args, **kwargs)

        return inner

    def right_click(self, event):
        """When right clicking in listbox, update selection and bring up context options."""

        l = self.listbox
        sel = l.nearest(event.y)
        self.tools.do_sel(self.listbox, sel)
        self.menu.do_popup(event, sel)

    @preserve_sel
    def mark_nextup(self, sel, *args, **kwargs):
        """Mark the selected song as next up."""
        self.markers['nextup'] = self.live.songs[sel] if sel else self.markers['nextup']
        self.listbox_update()

    @preserve_sel
    def on_remove(self, sel, *args, **kwargs):
        """Remove selected song."""
        if sel is None:
            return
        self.live.remove_song_at_index(i=sel)
        self.listbox_update()

    @pass_sel
    def move(self, sel, target: str or int):
        """Move song within list."""

        dest = self.target_to_i(start_i=sel, target=target)
        self.gig.live_setlist.move(sel, dest)
        self.listbox_update()
        self.tools.do_sel(self.listbox, dest)

    def target_to_i(self, start_i, target):
        """Convert a listbox target to an index."""

        if target == "top":
            return 0
        elif target == "end":
            return -1
        new = start_i + target
        return new if new >=0 else 0

    @pass_sel
    def on_toggle(self, sel, mark):
        """Toggle a songs presence within a marker list."""
        self.data.toggle_mark(mark, self.songs[sel])
        self.listbox_update()

    @pass_sel
    def on_listbox_select(self, sel, event):
        """What to do when clicking an item in the setlist."""
        self.push_song_to_preview(sel) if sel is not None else None

    def push_song_to_preview(self, i):
        """Push info to infobox, and song obj to preview frame."""

        # TODO: this method will not work if you implement search
        # TODO: think of a way to automate this refresh callback
        self.deck.cued = self.songs[i] if self.songs else None
        self.app.meta.song_detail.refresh_callback = self.listbox_update

    def make_listbox_strategies(self):
        """Define strategies for formatting listbox items."""

        # TODO: clunky...
        colors = self.settings.colors
        l = self.listbox

        self.listbox_strategies = {
            lambda song: self.song_is_skipped(song): lambda i: l.itemconfig(i, bg=colors.skipped),
            lambda song: self.song_is_nextup(song): lambda i: l.itemconfig(i, bg=colors.nextup),
            lambda song: self.song_is_previous(song): lambda i: l.itemconfig(i, bg=colors.previous),
            lambda song: self.song_is_live(song): lambda i: l.itemconfig(i, bg=colors.live),
        }

    # TODO: hmmm
    def song_is_skipped(self, song):
        return song in self.markers.get('skipped') if self.markers.get('skipped') else False

    def song_is_nextup(self, song):
        return song is self.markers.get('nextup')

    def song_is_live(self, song):
        return song is self.markers.get('live')

    def song_is_previous(self, song):
        return song is self.markers.get('previous')

    @preserve_sel
    def listbox_update(self, sel=None):
        """Update listbox contents and formatting."""

        self.listbox.delete(0, "end")
        if not self.live.songs:
            return

        logging.info(f'listbox_update names: {self.live.names}')
        for i, name in enumerate(self.live.names):
            name = strike(name) if self.songs[i] in self.markers.get('played') else name
            name = number(i+1, name)
            self.listbox.insert("end", name)
            self.color_item(i)

    def color_item(self, i:int) -> None:
        """Apply appropriate color to a listbox item."""

        logging.info('color_item in SetlistFrame')
        for k, v in self.listbox_strategies.items():
            if k(self.songs[i]):
                v(i)
                logging.info('color applied!')
                break

class SetlistHeader(tk.Frame):
    """Frame for the setlist header elements."""

    def __init__(self, parent):
        tk.Frame.__init__(self, parent)

        # context
        self.parent = parent
        self.app = parent.app
        self.suite = self.parent

        self.label = tk.Label(self, text="Active Setlist | ")
        self.label.pack(side="left", anchor="w", expand=True)

        self.current = tk.Label(self, text="(setlist title will go here)")
        self.current.pack(side="right", anchor="w", expand=True)


class SetlistControlRow(tk.Frame):
    """Row for the setlist buttons for moving entries around."""

    def __init__(self, parent):
        tk.Frame.__init__(self, parent)

        # context
        self.parent = parent
        self.app = parent.app
        self.settings = self.app.settings.setlist
        self.suite = parent
        self.tools = parent.tools

        # TODO: move these functions in?
        move = self.suite.move
        on_remove = self.suite.on_remove
        toggle = self.suite.on_toggle
        nextup = self.suite.mark_nextup

        # move selection up
        self.move_up = tk.Button(self, text="\u25B2", command=lambda: move(-1), width=1)
        self.move_up.pack(side="left")
        # CreateToolTip(self.move_up, text="Move up")

        # move selection down
        self.move_down = tk.Button(
            self, text="\u25BC", command=lambda: move(1), width=1
        )
        self.move_down.pack(side="left")

        # toggle selection skip
        self.skip = tk.Button(self, text="\u2938", command=lambda: toggle('skipped'), width=1)
        self.skip.pack(side="left")

        # cross out played song
        self.playmark = tk.Button(self, text="\u2713", command=lambda: toggle('played'))
        self.playmark.pack(side="left")

        self.remove = tk.Button(self, text="\u2715", command=on_remove)
        self.remove.pack(side="left")

        # cue selection in play order TODO: find an appropriate unicode symbol for this
        self.nextup = tk.Button(self, text="NEXT", command=nextup)
        self.nextup.pack(side="left")

        # keep all buttons in a list for lock toggle fn
        self.togglable = (
            self.move_up,
            self.move_down,
            self.skip,
            self.playmark,
            self.remove,
        )

        # lock
        # TODO: something funky in here... i think toggle_lock is getting the old
        # value instead of the newly assigned value in its conditional
        self.locked = self.settings.locked
        
        self.lock = tk.Label(self, text="\U0001F512" if self.locked.get() else "\U0001F513")
        self.lock.bind("<Button-1>", lambda e: self.tools.toggle_lock(var=self.locked, label=self.lock, follow_fn=self.toggle_controls))
        self.lock.pack(side="right", anchor="e", expand=True)
        
        # TODO: hacky fix
        self.toggle_controls()

    def toggle_controls(self, *args,):
        """Update state of setlist controls based on toggle."""
        state = "disabled" if self.locked.get() else "normal"
        for button in self.togglable:
            button.config(state=state)

class RightClickMenu(tk.Frame):
    """Menu for when you right click within monitor frame."""

    def __init__(self, parent, *args, **kwargs):
        tk.Frame.__init__(self, parent)

        self.parent = parent
        self.app = parent.app
        self.suite = parent.suite

        # selection
        self.sel = SelectionProperties(self.app)

        # self.main_menu = main_menu

    def do_popup(self, event, i):
        """Popup right click menu."""

        # update selection params
        self.update_selection(i)
        menu = self.build_menu(i)

        try:
            menu.tk_popup(event.x_root, event.y_root)
        finally:
            menu.grab_release()

    def build_menu(self, i):
        """Construct menu based on context."""

        menu = tk.Menu(self.parent, title="Setlist Options")
        return self.add_empty_options(menu) if i < 0 else self.add_song_options(menu)

    def add_empty_options(self, menu):
        """Options when nothing is in the setlist."""
        menu.add_command(label="Empty Setlist", state="disabled")
        menu.add_separator()
        menu.add_command(label="Load Setlist")
        menu.add_command(label="Reload Last Setlist")
        return menu

    def add_song_options(self, menu):
        """Construct menu when song is selected based on selection properties."""

        selection = self.sel
        locked = self.suite.controls.locked.get()

        # context sensitive menu for selection
        strategies = {
            lambda: True: lambda: menu.add_command(
                label=f"{selection.name.get()}", state="disabled"
            ),
            lambda: True: lambda: menu.add_separator(),
            lambda: not locked: lambda: menu.add_command(label="Rename"),
            lambda: not locked: lambda: menu.add_command(label="Delete"),
            lambda: not locked: lambda: menu.add_separator(),
            # mark next
            lambda: not selection.nextup.get(): lambda: menu.add_command(
                label="Play next"
            ),
            # played option
            lambda: selection.played.get(): lambda: menu.add_command(
                label="Clear play mark"
            ),
            lambda: not selection.played.get(): lambda: menu.add_command(
                label="Mark as played"
            ),
            # skipped option
            lambda: selection.skipped.get(): lambda: menu.add_command(label="Include"),
            lambda: not selection.skipped.get(): lambda: menu.add_command(label="Skip"),
            # edit lock
            lambda: True: lambda: menu.add_separator(),
            lambda: not locked: lambda: menu.add_command(label="Lock"),
            lambda: locked: lambda: menu.add_command(label="Unlock"),
        }

        [v() for k, v in strategies.items() if k()]
        return menu

    def update_selection(self, i):
        """Get selection and update selection properties."""
        setlist = self.app.setlist
        self.sel.name.set(setlist.songs[i].name) if i>=0 else self.sel.name.set(None)

class SelectionProperties:
    """Class for holding the properties of selected song to update context menu."""

    def __init__(self, app):
        # TODO: maybe properties that look up selection to get values?
        self.app = app
        self.name = tk.StringVar()
        self.ind = None
        self.skipped = tk.BooleanVar()
        self.played = tk.BooleanVar()
        self.nextup = tk.BooleanVar()
