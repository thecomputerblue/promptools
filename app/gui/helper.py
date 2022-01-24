import tkinter as tk

class HelperBox(tk.Frame):
    """Box that will show info on currently hovered-over tool."""
    
    def __init__(self, parent):
        tk.Frame.__init__(self, parent.frame)

        self.app = parent.app

        self.label = tk.Label(self, text="Helper text will go here.")
        self.label.pack(side="top", anchor="n", expand=False,
            fill='both'
            )