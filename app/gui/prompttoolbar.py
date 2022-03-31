import tkinter as tk 

class PromptToolBar(tk.Frame):
    """Toolbar shown above monitor/editor in prompt mode."""

    def __init__(self, parent):
        tk.Frame.__init__(self, parent)

        self.parent = parent
        self.app = parent.app
        self.suite = parent.suite
        self.settings = parent.settings

        self.autoscroll_scale = tk.Scale(
            self,
            from_=0,
            to=1,  # adjust based on global scroll scale
            orient="horizontal",
            showvalue=0,
            sliderlength=20,
            length=200,
            takefocus=0,
            resolution=1/self.settings.scroll.steps.get(),
            variable=self.settings.scroll.pos
        )

        self.autoscroll_label = tk.Label(
            self,
            text="Scroll Speed",
        )

        self.pixels_scale = tk.Scale(
            self,
            from_=0,
            to=15,  # adjust based on global scroll scale
            orient="horizontal",
            showvalue=0,
            sliderlength=20,
            length=200,
            takefocus=0,
            resolution=1,
            variable=self.settings.scroll.pixels
            )

        self.pixels_label = tk.Label(
            self,
            text="Pixels",
        )

        self.autoscroll_label.pack(side="left", anchor="w")
        self.autoscroll_scale.pack(side="left", anchor="w")

        self.pixels_label.pack(side="left", anchor="w")
        self.pixels_scale.pack(side="left", anchor="w")