# preview the cued song

import tkinter as tk
from tools.api import PrompToolsAPI

class Preview(tk.Frame, PrompToolsAPI):
    """Frame for showing a preview of whatever is on deck to be prompted
    including any key changes."""

    def __init__(self, gui, *args, **kwargs) -> None:
        tk.Frame.__init__(self, gui.root)
        PrompToolsAPI.__init__(self, gui)

        self.song = None

        # widgets
        self.scrollbar = tk.Scrollbar(self, orient='vertical')

        self.text = tk.Text(
            self,
            font= self.settings.fonts.preview,
            height=15,
            width=50,
            wrap='none',
            bg='black',
            fg='white',
            state='disabled',
            yscrollcommand=self.scrollbar.set,
            )

        # bind scrollbar to preview
        # TODO: switch to ScrolledText widget
        self.scrollbar.config(command=self.text.yview)

        # pack widgets
        self.text.pack(side='left', fill='both', expand=True)
        self.scrollbar.pack(side='left', fill='both')

        # automatically fetch cued song from deck
        self.app.deck.add_callback('cued', self.push)

        # bindings
        self.bind("<Button-1>", lambda _: self.on_focus())
        self.text.bind("<Button-1>", lambda _: self.on_focus())

    @property
    def should_reset_yview(self):
        return False if self.app.deck.cued == self.song else True

    def push(self, song=None, reset=None):
        """Push cued song to preview pane whenever cued song changes."""
        cued = song if song else self.app.deck.cued
        if reset is None:
            reset = self.should_reset_yview
        self.app.tools.loader.push(frame=self, song=cued, reset=reset)

    def on_focus(self):
        self.focus_set()
        self.app.deck.focused = self.song
