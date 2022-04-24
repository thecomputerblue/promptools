import logging
import tkinter as tk

from tools.apppointers import AppPointers

class TxtExportWindow(tk.Toplevel, AppPointers):
    """Window for the text exporter."""
    def __init__(self, parent, *args, **kwargs):
        tk.Toplevel.__init__(self, parent)
        AppPointers.__init__(self, parent)

        self._init_config()
        self._init_widgets()
        self._init_geometry()
        # self._register_callbacks()
        self.sync()

    def _init_config(self):
        """Initialize window config"""
        self.settings.windows.tempo.set(True)
        self.title('Export TXT')
        self.attributes('-topmost', True)
        self.protocol("WM_DELETE_WINDOW",self.quit_window)

    def _init_geometry(self):
        # default window size
        win_w = 200
        win_h = 200
        self.geometry(f'{str(win_w)}x{str(win_h)}')
        self.resizable(width=False, height=False)
        self.geometry(self.gui.screen_center(win_w, win_h))

    def _init_widgets(self):
        """Build window widgets."""
        self.qe_label = tk.Label(self, text='Quick Export Options')
        self.qe_label.pack(anchor="n")

        self.exp_live_btn = tk.Button(self, text='Export Live to TXT', command=self.export_live)
        self.exp_live_btn.pack(anchor="s")

        self.exp_sl_btn = tk.Button(self, text='Export Set to TXT', command=self.export_setlist)
        self.exp_sl_btn.pack(anchor="s")

    def export_live(self):
        song = self.app.deck.live
        self.app.tools.txt_exporter.export_one_song(song) if song else None
    
    def export_setlist(self):
        songs = self.setlists[0].songs
        self.app.tools.txt_exporter.export_many_songs(songs) if songs else None

    def sync(self):
        pass

    def quit_window(self):
        self.settings.windows.txt_exporter.set(False) 
        self.destroy()