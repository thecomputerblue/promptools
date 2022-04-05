# assemble tkinter gui from components

import tkinter as tk
import logging

from gui.collections import CollectionsSuite
from gui.browser import BrowserSuite
from gui.talent import TalentWindow
from gui.monitor import TalentMonitor
from gui.preview import Preview
from gui.bigbutton import PromptButton
from gui.cued import CuedUp
from gui.menu import MenuBar
from gui.metapane import MetaSuite
from gui.helpbox import HelpBox
from gui.controls import AppControls

class TkGui(tk.Frame):
    def __init__(self, app, root):
        tk.Frame.__init__(self, root)

        # context
        self.app = app
        self.root = root
        self.suite = None
        
        # 2nd window for talent
        self.talent = TalentWindow(self)

        # main window widgets
        self.monitor = TalentMonitor(self)
        self.monitor.grid(row=0, column=1, columnspan=2, sticky="nesw")

        # big PROMPT button, to be made context sensitive, eventually
        self.bigbutton = PromptButton(self)
        self.bigbutton.grid(
            row=3,
            column=1,
            rowspan=1,
            columnspan=2,
            ipadx=0,
            ipady=10,
            sticky="nesw",
            padx=5,
            pady=5,
        )

        self.browser = BrowserSuite(self)
        # self.browser = LibrarySuite(self) # this is the version that imports everything
        self.browser.grid(
            row=1,
            column=1,
            columnspan=1,
            rowspan=2,
            sticky="nesw",
            padx=8,
            pady=8,
        )

        # TODO: merge preview frame with cued since they will always live in that orientation
        self.cued = CuedUp(self)
        self.cued.grid(row=1, column=2, columnspan=1, sticky="nesw")

        self.preview = Preview(self)
        self.preview.grid(row=2, column=2, columnspan=1, sticky="nesw", padx=8, pady=8)

        self.meta = MetaSuite(self)
        self.meta.grid(row=0, column=3, sticky="nesw", rowspan=4) 

        # setlist / song pool pane on the left
        self.collections = CollectionsSuite(self)
        self.collections.grid(row=0, column=0, rowspan=3, sticky="nesw")

        # this will be a tooltip box in the bottom left corner of the app
        self.helpbox = HelpBox(self)
        self.helpbox.grid(row=3, column=0, sticky="nesw")

        # menubar at the top of the app
        self.menu = MenuBar(self)

        # configure columns
        self.columnconfigure(0, weight=1)
        self.columnconfigure(1, weight=0)
        self.columnconfigure(2, weight=1)
        self.columnconfigure(3, weight=5)

    def toggle_lock(self, label, var, follow_fn=None, *args, **kwargs):
        """Generic lock toggle method. Follow fn_ will execute after lock toggle."""

        if var.get():
            # unlock unicode \U0001F513
            label.config(text="\U0001F513")
            var.set(False)
        else:
            # lock unicode \U0001F512
            label.config(text="\U0001F512")
            var.set(True)
            
        follow_fn(args, kwargs) if follow_fn else None

    def get_sel(self, listbox):
        """Get selection index."""
        sel = listbox.curselection()
        return sel[0] if sel else None

    def do_sel(self, listbox, sel):
        """Clear and apply new target listbox selection."""
        listbox.selection_clear(0, "end")
        listbox.selection_set(sel) if sel < listbox.size() else listbox.selection_set("end")
        listbox.activate(sel)

    # next two might make more sense in screens module
    def get_screen_xy(self, win_w, win_h):
        x = int(self.winfo_screenwidth()/2 - win_w/2)
        y = int(self.winfo_screenheight()/2 - win_h/2)
        return x, y

    def screen_center(self, win_w, win_h):
        """Pass to tkToplevel.geometry method for centered popup"""
        x, y = self.get_screen_xy(win_w, win_h)
        return f"+{x}+{y}"

    def sync(self):
        """Bang sync methods throughout gui widgets."""
        self.collections.sync()

