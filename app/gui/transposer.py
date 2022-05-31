import tkinter as tk

from tools.api import PrompToolsAPI

class TransposerWindow(tk.Toplevel, PrompToolsAPI):
    """Window for the Transposer tools."""

    def __init__(self, parent, *args, **kwargs):
        tk.Toplevel.__init__(self, parent)
        PrompToolsAPI.__init__(self, parent)

        self.parent = parent
        self.app = parent.app # TODO: not needed? 
        
        # raise flag when the window is open    
        self.settings.windows.transposer.set(True)

        # always top level window.
        self.attributes('-topmost', True)

        # disable resize
        self.resizable(False, False)

        # title
        self.title('Transposer')

        # destroy method 
        self.protocol("WM_DELETE_WINDOW",self.quit_window)

        self.label_font = "arial 13 underline"

        # self.transposer = TransposerTools(self)
        self.transposer = FastTransposer(self)
        self.transposer.pack()
        # self.pack()

    def quit_window(self):
        #TODO: probably make this a tk variable. at least move to transposer settings
        settings = self.app.settings 
        transposer = self.transposer

        settings.windows.transposer.set(False) 
        transposer.key.set('')
        settings.transposer.enabled.set(False)

        # delete the key trace so it doesnt crash TODO: better solution?
        transposer.key.trace_vdelete("w", transposer.key_trace)
        self.destroy()

class FastTransposer(tk.Frame):
    """Replacing evious TransposerTools class with something less convoluted."""

    def __init__(self, parent, *args, **kwargs):
        tk.Frame.__init__(
            self, parent, highlightthickness=2, borderwidth=2, relief="sunken"
        )

        # pointers
        self.app = parent.app
        settings = self.app.settings

        # key entry variable
        self.key = self.app.settings.transposer.key
        self.key_trace = self.key.trace("w", lambda *args: self.push_updates())

        # key entry label
        self.label = tk.Label(self, text="Custom starting key",)
        self.label.pack(side="top")

        # key entry widget
        self.entry = tk.Entry(
            self,
            font=settings.fonts.transposer,
            width=10,
            border=10,
            justify="center",
            state="disabled",
            textvariable=self.key
        )
        # TODO: think this is also refreshing when i toggle enable?
        # self.entry.bind("<1>", lambda *args: self.refresh())
        self.entry.pack(side="top", anchor="n")

        # options
        self.enabled = settings.transposer.enabled
        self.enable_toggle = tk.Checkbutton(self, text="Enable Transposer", variable=self.enabled, command=self.toggle_enable)
        self.enable_toggle.pack(side="top", anchor="w")

        self.nashville = settings.transposer.nashville
        self.nash_toggle = tk.Checkbutton(self, text="Show Nashville Numbers", variable=self.nashville, command=self.refresh)
        self.nash_toggle.pack(side="top", anchor="w")

        self.apply_to_cued = settings.transposer.apply_to_cued
        self.cued_toggle = tk.Checkbutton(self, text="Apply to Cued", variable=self.apply_to_cued, command=self.refresh)
        self.cued_toggle.pack(side="top", anchor="w")

        # self.apply_to_current = self.settings.apply_to_current
        self.current_button = tk.Button(self, text="Apply to Current", pady=5)
        self.current_button.pack(side="top", anchor="n")

    def toggle_enable(self):
        if self.enabled.get():
            self.entry.configure(state="normal")
        else:
            # TODO: Improve this hacky reset workaround.
            self.enabled.set(True)
            self.key.set('')
            self.enabled.set(False)

            self.entry.configure(state="disabled")

    def refresh(self):
        """On any button click or edit to key, scan settings and refresh song views as needed."""

        self.app.deck.push('cued')

    def update_key(self):
        """Truncate and update key."""
        if len(self.entry.get()) > 0:
            # impose character limit
            new = self.entry.get()[:3]
            self.key.set(new)
        else:
            self.key.set('')

        self.refresh()

    def push_updates(self):
        self.refresh()