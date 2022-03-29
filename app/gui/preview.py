# preview the cued song

import tkinter as tk

class Preview(tk.Frame):
    """Frame for showing a preview of whatever is on deck to be prompted
    including any key changes."""

    def __init__(self, parent, *args, **kwargs) -> None:
        tk.Frame.__init__(self, parent.frame)

        # orient
        self.parent = parent
        self.app = parent
        self.settings = parent.settings

        # vars
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

    def push(self, song=None, reset_view=None):
        """Push cued song to preview pane whenever cued song changes."""
        cued = song if song else self.app.deck.cued
        if reset_view is None:
            reset_view = False if cued is self.song else True
        self.app.tools.loader.push(frame=self, song=cued, reset_view=reset_view)

    def on_focus(self):
        self.focus_set()
        self.app.deck.focused = self.song

    # TODO: old push method, afaict I don't use this anywhere. Confirm and delete.
    # def push(self, song, reset_view=None):
    #   """Refresh contents of preview window."""
    #   if reset_view is None:
    #       reset_view = False if song is self.song else True
    #   self.app.tools.loader.push(frame=self, song=song, reset_view=reset_view)

    # TODO: not used, confirm & delete
    # def empty(self):
    #   """Set preview when nothing is loaded or invalid file selected."""

    #   # TODO: make more generic to work on a text widget as argument?
    #   message = ''
    #   state = self.text.cget("state")
    #   self.text.config(state='normal')
    #   self.text.config
    #   self.text.delete('1.0', 'end')
    #   self.text.insert('1.0', message)
    #   self.text.config(state=state)
