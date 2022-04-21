import tkinter as tk
from tools.apppointers import AppPointers


class EditToolBar(tk.Frame, AppPointers):
    """Toolbar shown in edit mode."""

    def __init__(self, parent):
        tk.Frame.__init__(self, parent)
        AppPointers.__init__(self, parent)

        self.placeholder = tk.Label(self, text="PLACEHOLDER FOR EDIT TOOLBAR")
        self.placeholder.pack(expand=True, fill="both", anchor="w")