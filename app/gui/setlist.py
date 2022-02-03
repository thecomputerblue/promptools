import tkinter as tk
import time

# import copy
import logging

# from tools.tooltip import CreateToolTip


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

        # live setlist
        self.live = self.data.live

        # self.manager = SetlistManager(self)

        # expose song pool
        self.songs = self.data.songs

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
        self.data.callback = self

        # deck callback
        self.app.deck.add_callback("live", self.refresh_markers_deck)

    def refresh_markers_deck(self):
        """Refresh the markers when the live song changes."""
        logging.info("refresh_markers_deck in setlist")
        deck = self.app.deck
        d = self.data

        # update marks
        if deck.live in self.songs:
            logging.info("refresh_markers_deck marked current song in setlist")
            d.current = deck.live

        if deck.previous in self.songs:
            logging.info("refresh_markers_deck marked previous song in setlist")
            d.previous = deck.previous

        # refresh
        self.listbox_update()

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
        selection = l.nearest(event.y)

        # Update selection
        l.selection_clear(0, "end")
        l.selection_set(selection)
        l.activate(selection)

        # Popup
        self.menu.do_popup(event, selection)

    def on_remove(self):
        """Remove selected song."""

        d = self.data
        l = self.listbox
        sel = l.curselection()

        if not sel:
            return

        # TODO: if deleted song is currently in song info, clear the song info
        # achieve with listeners within song? more comprehensive callback manager?
        i = sel[0]
        del d.songs[i]
        self.listbox_update()
        # move cursor back to where it was, or end of the list.
        # TODO: confirm its necessary to clear after a deletion
        l.selection_clear("1", "end")
        l.selection_set(sel[0]) if i < l.size() else l.selection_set("end")

    def get_selection(self):
        """Get selected index."""

        l = self.listbox
        sel = l.curselection()
        return sel[0] if sel else None

    def move(self, target: str or int):
        """Move song within list."""

        sel = self.get_selection()

        if sel == None:
            return

        l = self.listbox
        d = self.data

        # TODO: refactor
        # accept 'top' or 'end' to force
        if target == "top":
            new = 0
        elif target == "end":
            new = -1
        else:
            new = sel + target

            # if it's at the edge of the list, don't do anything.
            if new > len(d.songs) - 1 or new < 0:
                new = sel

        # move the song, refresh the list representation
        d.songs.insert(new, d.songs.pop(sel))

        # move within list representation
        self.listbox_update()

        l.selection_clear(0, "end")
        l.selection_set(new)

    def on_skip(self):
        """What to do when song is skipped."""

        sel = self.get_selection()

        if sel == None:
            return

        l = self.listbox
        d = self.data

        skipped = d.skipped
        song = d.songs[sel]

        if song not in skipped:
            # skip
            l.itemconfig(sel, bg="grey")
            skipped.append(song.name)
        else:
            # unskip
            l.itemconfig(sel, bg="light grey")
            skipped.remove(song.name)

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
        song = d.songs[i] if d.songs else None
        app.deck.cued = song
        app.meta.song_detail.refresh_callback = self.listbox_update

    def listbox_update(self):
        """Update listbox colors"""

        # TODO: huge function, refactor
        self.update_marks()

        l = self.listbox
        d = self.data
        live = d.live

        if not live.songs:
            return

        # live setlist specific
        names = live.names
        numbered_names = live.numbered
        songs = live.songs

        # markers
        skipped = d.skipped
        played = d.played
        nextup = d.nextup
        previous = d.previous
        current = d.current

        sel = l.curselection() if l.curselection() else None

        l.delete(0, "end")

        # colors
        colors = self.app.settings.setlist.colors

        # assign skipped
        strategies = {
            lambda song: song.name
            in skipped: lambda i: l.itemconfig(i, bg=colors.skipped),
            lambda song: nextup
            and song.name == nextup.name: lambda i: l.itemconfig(i, bg=colors.nextup),
            lambda song: previous
            and song.name
            == previous.name: lambda i: l.itemconfig(i, bg=colors.previous),
            lambda song: current
            and song.name == current.name: lambda i: l.itemconfig(i, bg=colors.current),
            # lambda song: song.name in played:                       lambda i: l.itemconfig(i, overstrike=1)
        }

        # TODO: messy
        for i, name in enumerate(names):

            # strikeout played songs
            # TODO: switch from name list to using song objs
            if name in played:
                l.insert("end", self.strike(numbered_names[i]))
            else:
                l.insert("end", numbered_names[i])

            # assign color / format
            for k, v in strategies.items():
                if k(songs[i]):
                    v(i)
                    break

        # restore listbox selection if there was one.
        # TODO:
        if sel:
            l.selection_set(sel)
            l.activate(sel)

        # update current and next markers
        # self.update_marks()

    def strike(self, text):
        """Strikethru text."""

        # TODO: fix janky strikethru appearance...
        result = ""
        for _, c in enumerate(text):
            result += c + "\u0336"
        return result

    def mark_previous(self, pos):
        """Mark song at target index as previous, updating flag & listbox.
        TODO: Eventually integrate the song chain."""

        l = self.listbox
        d = self.data
        colors = self.app.settings.setlist.colors

        # clear old
        # TODO: check for identity equivalence on song objs instead
        for i, song in enumerate(d.songs):
            if d.previous and song.name == d.previous.name:
                l.itemconfig(i, bg=colors.default)
                break

        # apply new previous
        d.previous = d.songs[pos]

    def update_marks(self):
        """Mark current and next song."""

        d = self.data 
        d.current = None

        live_song = self.app.deck.live

        if not live_song:
            return

        for i, song in enumerate(d.songs):
            if song.name == live_song.name:
                d.current = song
                self.mark_nextup(target=i+1, count=len(d.songs))
                break

    def mark_nextup(self, target, count):
        """Manage the previous and next pointers."""

        l = self.listbox
        d = self.data

        if target >= count:
            d.nextup = None
            return

        skipped = d.skipped
        songs = d.songs

        # starting with the target, find the first not-skipped song.
        for i in range(target, count):
            if songs[i].name not in skipped:
                d.nextup = songs[i]
                return

        # if everything was skipped, no nextup
        d.nextup = None

    def add_song(self, song):
        """Add song to setlist."""
        d = self.data

        d.songs.append(song)
        d.live.songs.append(song)

        # TODO: I suspect there is some redundancy to work out here...
        self.update_marks()
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
