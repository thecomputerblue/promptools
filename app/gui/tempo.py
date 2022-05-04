# popup window for tap tempo tool
import tkinter as tk
import logging

from tools.apppointers import AppPointers

# TODO: button to assign generated tempo to live song.

class TempoToolWindow(tk.Toplevel, AppPointers):
    """Popup viewer for history. Should load to preview when you click an entry."""

    def __init__(self, parent, *args, **kwargs):
        tk.Toplevel.__init__(self, parent)
        AppPointers.__init__(self, parent)

        self._init_config()
        self._init_widgets()
        self._init_geometry()
        self._register_callbacks()
        self.sync()

    def _init_config(self):
        """Initialize window config"""
        self.settings.windows.tempo.set(True)
        self.title('TT')
        self.attributes('-topmost', True)
        self.protocol("WM_DELETE_WINDOW",self.quit_window)

    def _init_geometry(self):
        # default window size
        win_w = 100
        win_h = 100
        self.geometry(f'{str(win_w)}x{str(win_h)}')
        self.resizable(width=False, height=False)
        self.geometry(self.gui.screen_center(win_w, win_h))

    def _init_widgets(self):
        """Build window widgets."""
        self.label = tk.Label(self, text='Tap Tempo')
        self.label.pack(anchor="n")
        self.tempo = tk.Label(self, text='-', font=("Menlo", 25))
        self.tempo.pack(anchor="center")
        self.button = tk.Button(self, text='TAP', command=self.tap)
        self.button.pack(anchor="s")

    def _register_callbacks(self):
        pass
        
    def sync(self):
        pass

    def tap(self):
        self.app.tools.tempo.tap()
        self.try_get_tempo()

    def try_get_tempo(self):
        t = self.app.tools.tempo.tempo
        self.tempo.config(text=str(round(t, 1))) if t else self.tempo.config(text='-')

    def quit_window(self):
        self.settings.windows.tempo.set(False) 
        self.destroy()