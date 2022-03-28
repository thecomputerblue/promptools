import tkinter as tk 

class GuiTools:
    """Class with generic methods for gui element manipulation. Using to avoid
    duplicate methods between modules. As you find redundant functions, migrate
    here. """

    def __init__(self, app, *args, **kwargs):
        self.app = app 

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