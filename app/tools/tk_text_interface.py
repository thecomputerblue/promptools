# interface for moving song scripts into and out of tk text boxes
import tkinter as tk
import logging

from tools.apppointers import AppPointers

class TkTextInterface(AppPointers):
    """Translate tk_text tag format into other formats
    for loading between modules."""

    def __init__(self, app):
        AppPointers.__init__(self, app)

        self.styles = self.app.settings.tags.styles
        self.types = self.app.settings.tags.types

    def tkt_to_ptt(self, tkt):
        """Convert tkinter text to promptools tuples,
        the format which promptools song objects store."""
        # TODO: convoluted struct

        def tagon_flag():
            """Update tag if word is a promptools tag type.
            Append a flag if it is a style."""
            nonlocal tag
            tag = word if word in self.types else tag
            ptt.append((pos, flag, word)) if word in self.styles else None

        def text_flag():
            """If text, append with current tag"""
            ptt.append((pos, tag, word))

        # TODO: need to handle tagoffs and unknowns for styling
        def tagoff_flag():
            pass

        def unknown_warning():
            pass

        strategies = {
        lambda flag: flag == 'tagon': tagon_flag,
        lambda flag: flag == 'text': text_flag,
        }

        ptt = []
        tag = None
        for tup in tkt:
            flag, word, pos = tup
            for k, v in strategies.items():
                v() if k(flag) else None
        return ptt

    def tkt_into_song(self, song, tkt):
        """Dum tkt into song object."""
        song.tk_tuples = self.tkt_to_ptt(tkt)

