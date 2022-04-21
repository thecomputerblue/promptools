import tkinter as tk
import logging

from tools.apppointers import AppPointers

class GuiMethods(AppPointers):
    """Handles dependency injection of widget functionality."""

    def __init__(self, gui):
        AppPointers.__init__(self, gui.app)

    def do_toggle_lock(self, label, var):
        """Generic lock toggle method. Follow fn_ will execute after lock toggle."""
        # unlock unicode: \U0001F513, lock unicode: \U0001F512
        label.config(text="\U0001F513") if var.get() else label.config(text="\U0001F512")
        var.set(not var.get())

    def get_sel(self, listbox):
        """Get selection index."""
        sel = listbox.curselection()
        return sel[0] if sel else None

    def do_sel(self, listbox, sel):
        """Clear and apply new target listbox selection."""
        listbox.selection_clear(0, "end")
        listbox.selection_set(sel) if sel < listbox.size() else listbox.selection_set("end")
        listbox.activate(sel)