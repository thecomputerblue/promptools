import tkinter as tk
import logging

from tools.apppointers import AppPointers

class CuedUp(tk.Frame, AppPointers):
    """Class that shows the song title cued for prompting."""

    # TODO: merge with preview, as this is basically just the header of
    # the preview frame.

    def __init__(self, parent, *args, **kwargs):
        tk.Frame.__init__(self, parent)
        AppPointers.__init__(self, parent)

        # vars
        self.selected = tk.StringVar()

        # widgets
        self.label = tk.Label(self, text="Cued For Prompt", width=10)
        self.label.pack(side="top", anchor="n", expand=False,
            fill='both'
            )

        self.title = tk.Label(
            self,
            textvariable=self.selected,
            font=self.settings.fonts.cue_title,
            # justify="left",
            relief="groove",
            width=20
        )
        self.title.pack(side="top", anchor="n", expand=False,
            fill="both"
            )

        # add to deck callbacks
        self.app.deck.add_callback('cued', self.push)

    def push(self):
        """Push the cued song name into the titlebar."""

        song = self.app.deck.cued

        if not song:
            self.selected.set('')
            return

        maxlength = self.app.settings.view.cue_truncate.get()
        self.selected.set(self.truncate_title(song.name, maxlength))

    def truncate_title(self, string, maxlength=45):
        """Truncate label to maxlength, appending '...' when too long."""

        if not string:
            return 'Untitled'

        return string if len(string) <= maxlength else string[:maxlength]
