import tkinter as tk
import time

# import copy
import logging

# from tools.tooltip import CreateToolTip

# helpers
def strike(text):
    """Strikethru text."""

    # TODO: fix janky strikethru appearance...
    result = ""
    for _, c in enumerate(text):
        result += c + "\u0336"
    return result

def number(n: int, name: str) -> str:
    """Return item formatted for list."""
    return '(' + str(n) + ') ' + name

class SetlistFrame(tk.Frame):
    """Class for the setlist manager"""

    def __init__(self, parent, *args, **kwargs):
        tk.Frame.__init__(
            self, parent, highlightthickness=2, borderwidth=2, relief="sunken"
        )

        # context
        self.parent = parent
        self.app = parent.app
        self.suite = parent.suite
        # TODO: confusing
        self.setlist = self 

        # manages the song list & its representation in the listbox
        self.data = self.app.data.setlists
        self.pool = self.data.songs
        # TODO: move markers in the setlists module
        self.markers = self.app.data.setlists.markers

        # live setlist & songs
        self.live = self.data.live
        self.songs = self.live.songs

        # widgets
        self.header = SetlistHeader(self)
        self.header.pack(side="top", anchor="w")

        self.listbox = tk.Listbox(
            self, width=40, height=20, bg="lightgrey", fg="black", exportselection=False
        )
        # self.listbox.grid(row=2, column=0, columnspan=4, sticky="nesw")
        self.listbox.pack(side="top", fill="both", expand=True)
        self.listbox.bind("<<ListboxSelect>>", self.on_listbox_select)

        # lock preventing editing the setlist
        self.locked = tk.BooleanVar()  # TODO: move to settings

        self.controls = SetlistControlRow(self)
        self.controls.pack(anchor="s", side="left", fill="both", expand=False)

        # add the lock trace and set to locked TODO: move this stuff into control row maybe
        self.locked.trace("w", lambda *args: self.toggle_controls())
        self.locked.set(True)

        # popup menu
        self.menu = RightClickMenu(self)
        self.listbox.bind("<Button-2>", self.right_click)

        # create a reference to this frame in the collection
        # so it can be refresshed when there is db activity.
        # TODO: best method? weakref?

        # deck callback
        self.app.deck.add_callback("live", self.listbox_update)
        self.data.add_callback(self.listbox_update)


        # make strategies for updating listbox
        self.make_listbox_strategies()

    def preserve_sel(method):
        """Capture then restore listbox selection after executing inner method"""
        def inner(self, *args, **kwargs):

            l = self.listbox
            sel = l.curselection() if l.curselection() else None

            method(self, *args, **kwargs)

            if sel:
                l.selection_clear(0, "end")
                l.selection_set(sel)
                l.activate(sel)

        return inner

    def toggle_controls(self, event=None):
        """Update state of setlist controls based on toggle."""

        togglable = self.controls.togglable
        locked = self.locked.get()
        state = "disabled" if locked else "normal"

        for button in togglable:
            button.config(state=state)

    def toggle_lock(self):
        """Update lock label and tkvar."""

        lock = self.controls.lock

        if self.locked.get():
            # unlock unicode \U0001F513
            lock.config(text="\U0001F513")
            self.locked.set(False)
        else:
            # lock unicode \U0001F512
            lock.config(text="\U0001F512")
            self.locked.set(True)

    def right_click(self, event):
        """When right clicking in listbox, update selection and bring up context options."""

        l = self.listbox
        sel = l.nearest(event.y)
        self.lb_sel(sel)
        self.menu.do_popup(event, sel)

    def on_remove(self):
        """Remove selected song."""

        sel = self.get_selection()

        if sel is None:
            return

        self.live.remove_song(i=sel)
        self.listbox_update()
        self.lb_sel(sel)

    def get_selection(self):
        """Get selected index."""

        l = self.listbox
        sel = l.curselection()

        return sel[0] if sel else None

    def move(self, target: str or int):
        """Move song within list."""

        sel = self.get_selection()

        if sel is None:
            return

        dest = self.target_to_i(start_i=sel, target=target)
        self.data.move_song(self.live, sel, dest)
        self.listbox_update()
        self.lb_sel(dest)

    def lb_sel(self, sel):
        """Clear and apply new target listbox selection."""

        l = self.listbox
        l.selection_clear(0, "end")
        l.selection_set(sel) if sel < l.size() else l.selection_set("end")
        l.activate(sel)

    def target_to_i(self, start_i, target):
        """Convert a listbox target to an index."""

        if target == "top":
            return 0
        elif target == "end":
            return -1
        new = start_i + target
        return new if new >=0 else 0

    def on_skip(self):
        """What to do when song is skipped."""

        sel = self.get_selection()

        if sel is None:
            return

        d = self.data
        l = self.listbox
        song = self.songs[sel]

        d.skip_toggle(song)
        l.itemconfig(sel, bg="grey") if song in d.skipped else l.itemconfig(sel, bg="light grey")

    def on_listbox_select(self, event):
        """What to do when clicking an item in the setlist."""

        # TODO: this method will not work once search is implemented.
        current = event.widget.curselection()
        self.push_song_to_preview(current) if current else None

    def push_song_to_preview(self, current):
        """Push info to infobox, and song obj to preview frame."""

        app = self.app
        d = self.data
        i = current[0]

        # if songs in setlist, get the song at index
        song = d.live.songs[i] if d.live.songs else None
        app.deck.cued = song
        app.meta.song_detail.refresh_callback = self.listbox_update

    def make_listbox_strategies(self):
        """Define strategies for formatting listbox items."""

        # TODO: clunky...
        colors = self.app.settings.setlist.colors

        self.listbox_strategies = {
            lambda song: self.song_is_skipped(song): lambda l, i: l.itemconfig(i, bg=colors.skipped),
            lambda song: self.song_is_nextup(song): lambda l, i: l.itemconfig(i, bg=colors.nextup),
            lambda song: self.song_is_previous(song): lambda l, i: l.itemconfig(i, bg=colors.previous),
            lambda song: self.song_is_live(song): lambda l, i: l.itemconfig(i, bg=colors.live),
            # lambda song: song.name in played: lambda i: l.itemconfig(i, overstrike=1)
        }

    def song_is_skipped(self, song):
        return song in self.markers.get('skipped') if self.markers.get('skipped') else False

    def song_is_nextup(self, song):
        return song is self.markers.get('nextup')

    def song_is_live(self, song):
        return song is self.markers.get('live')

    def song_is_previous(self, song):
        return song is self.markers.get('previous')

    @preserve_sel
    def listbox_update(self):
        """Update listbox contents and formatting."""

        self.listbox.delete(0, "end")
        # self.update_marks()

        live = self.data.live
        if not live.songs:
            return

        for i, name in enumerate(live.names):
            name = strike(name) if name in self.markers.get('played') else name
            name = number(i+1, name)
            self.listbox.insert("end", name)
            self.apply_colors(i)

    def apply_colors(self, i:int) -> None:
        """Apply colors to listbox items."""

        logging.info('apply_colors in SetlistFrame')
        l = self.listbox

        for k, v in self.listbox_strategies.items():
            if k(self.songs[i]):
                logging.info('color applied!')
                v(l, i)
                break

    def add_to_listbox(self, item: str):
        self.listbox.insert("end", item)

    def add_song(self, song):
        """Add song to setlist."""
        d = self.data

        d.songs.append(song)
        d.live.songs.append(song)

        # TODO: I suspect there is some redundancy to work out here...
        # self.update_marks()
        self.listbox_update()


class SetlistHeader(tk.Frame):
    """Frame for the setlist header elements."""

    def __init__(self, parent):
        tk.Frame.__init__(self, parent)

        # context
        self.parent = parent
        self.app = parent.app
        self.setlist = self.parent.setlist

        self.label = tk.Label(self, text="Setlist | ")
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
        self.suite = parent
        self.setlist = self.parent.setlist

        # TODO: move these functions in?
        move = self.setlist.move
        on_skip = self.setlist.on_skip
        on_remove = self.setlist.on_remove
        locked = self.setlist.locked

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
        self.skip = tk.Button(self, text="\u2938", command=lambda: on_skip(), width=1)
        self.skip.pack(side="left")

        # cross out played song
        self.playmark = tk.Button(self, text="\u2713", command=None)
        self.playmark.pack(side="left")

        self.remove = tk.Button(self, text="\u2715", command=on_remove)
        self.remove.pack(side="left")

        # cue selection in play order TODO: find an appropriate unicode symbol for this
        self.cue = tk.Button(self, text="CUE")
        self.cue.pack(side="left")

        # lock
        self.lock = tk.Label(
            self,
            text="\U0001F512",
        )
        self.lock.bind("<Button-1>", lambda e: self.suite.toggle_lock())
        self.lock.pack(side="right")

        # keep all buttons in a list for lock toggle fn
        self.togglable = [
            self.move_up,
            self.move_down,
            self.skip,
            self.playmark,
            self.remove,
        ]


class RightClickMenu(tk.Frame):
    """Menu for when you right click within monitor frame."""

    def __init__(self, parent, *args, **kwargs):
        tk.Frame.__init__(self, parent)

        self.parent = parent
        self.app = parent.app

        # selection
        self.sel = SelectionProperties(self.app)

        # self.main_menu = main_menu

    def do_popup(self, event, ind):
        """Popup right click menu."""

        # update selection param(s)
        self.update_selection(ind)

        # build menu
        menu = self.build_menu(ind)

        logging.info(f"right clicked on setlist selection: {ind}")
        logging.info("trying popup in setlist")
        try:
            logging.info(
                f"setlist right click popup @ coords: {event.x_root}, {event.y_root}"
            )
            menu.tk_popup(event.x_root, event.y_root)
            # TODO: get and aassign listbox selection.

        finally:
            menu.grab_release()

    def build_menu(self, ind):
        """Construct menu based on context."""

        # make empty menu
        menu = tk.Menu(self.parent, title="Setlist Options")

        # Options for empty setlist
        if ind < 0:
            return self.add_empty_options(menu)

        menu = self.add_song_options(menu)
        return menu

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
        suite = self.app.setlist
        locked = suite.locked.get()

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

    def update_selection(self, selection):
        """Get selection and update selection properties."""
        i = selection
        setlist = self.app.setlist

        if i >= 0:
            self.sel.name.set(setlist.songs[i].name)
        else:
            self.sel.name.set(None)


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
