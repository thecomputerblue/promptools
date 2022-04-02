import tkinter as tk
import logging

from tools.apppointers import AppPointers

class HelperBox(tk.Frame, AppPointers):
    """Box that will show info on currently hovered-over tool."""
    
    def __init__(self, parent):
        tk.Frame.__init__(self, parent.frame)
        AppPointers.__init__(self, parent)

        self.tip = tk.Label(self, text="")
        self.tip.pack(side="top", anchor="n", expand=False,
            fill='both'
            )

    def popup(self, msg, dur=2000):
        # prev = self.tip.get("text")
        self.tip.configure(text=msg)
        self.app.after(dur, lambda: self.tip.configure(text=""))

    def set(self, msg):
        self.tip.configure(text=msg)

    # TODO: implement queue to manage popup vs hover