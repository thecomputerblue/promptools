import tkinter as tk
from tools.api import PrompToolsAPI


class EditToolBar(tk.Frame, PrompToolsAPI):
    """Toolbar shown in edit mode."""

    def __init__(self, parent):
        tk.Frame.__init__(self, parent)
        PrompToolsAPI.__init__(self, parent)

        self.placeholder = tk.Label(self, text="PLACEHOLDER FOR EDIT TOOLBAR")
        self.placeholder.pack(expand=True, fill="both", anchor="w")