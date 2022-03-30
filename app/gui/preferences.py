# popup window containing a ttk notebook for setting app preferences

import tkinter as tk
from tkinter import ttk
from tkinter.colorchooser import askcolor
import logging


class PreferencesWindow(tk.Toplevel):
    """Class for the window for configuring program preferences."""

    def __init__(self, parent, *args, **kwargs):
        tk.Toplevel.__init__(self, parent.frame)
        self.parent = parent
        self.app = parent.app
        self.frame = parent.frame
        self.settings = self.app.settings
        app = parent.app

        # flag that this is open
        self.app.settings.windows.preferences.set(True)

        self.title("Preferences")

        # default window size
        win_w = 500
        win_h = 500
        self.geometry(f"{str(win_w)}x{str(win_h)}")

        # TODO: stop window resizing
        self.resizable(width=False, height=False)

        # always popup in center of operator window
        x = int(app.winfo_screenwidth() / 2 - win_w / 2)
        y = int(app.winfo_screenheight() / 2 - win_h / 2)
        self.geometry(f"+{x}+{y}")

        # destroy method
        self.protocol("WM_DELETE_WINDOW", self.quit_window)

        self.notebook = PreferencesNotebook(self)

    def quit_window(self):
        """When you close window, update the flag."""
        self.settings.windows.preferences.set(False)
        self.destroy()


class PreferencesNotebook(ttk.Notebook):
    """ttk notebook for managing several preference tabs."""

    def __init__(self, parent):
        ttk.Notebook.__init__(self, parent)

        self.app = parent.app

        general_tab = GeneralTab(self)
        general_tab.pack(fill="both", expand=True)
        self.add(general_tab, text="General")

        import_export_tab = ImportExportTab(self)
        import_export_tab.pack(fill="both", expand=True)
        self.add(import_export_tab, text="Import & Export")

        talent_tab = TalentTab(self)
        talent_tab.pack(fill="both", expand=True)
        self.add(talent_tab, text="Look & Feel")
        # colors, arrow setting

        self.pack(fill="both", expand=True)
        # self.pack(expand=True)


class GeneralTab(tk.Frame):
    """Class for the General Settings tab."""

    def __init__(self, parent):
        tk.Frame.__init__(self, parent)

        self.app = parent.app
        self.settings = parent.app.settings

        self.testcheck = tk.Checkbutton(self, text="Test checkbox")
        self.testcheck.pack(anchor="w")


class ImportExportTab(tk.Frame):
    """Class for the Import/Export Settings tab."""

    def __init__(self, parent):
        tk.Frame.__init__(self, parent)

        self.app = parent.app
        self.settings = parent.app.settings

        # Settings
        self.import_label = tk.Label(self, text="Import Settings")
        self.import_label.pack(anchor="w")
        self.import_raw = tk.Checkbutton(
            self,
            text="Import Text Raw (no formatting)",
            variable=self.settings.importer.raw,
        )
        self.import_raw.pack(anchor="w")


class TalentTab(tk.Frame):
    """Class for the Talent Settings tab."""

    def __init__(self, parent):
        tk.Frame.__init__(self, parent)

        self.app = parent.app
        self.settings = parent.app.settings

        self.view_label = tk.Label(self, text="View")
        self.view_label.pack(anchor="w")

        self.text_size_label = tk.Label(self, text="Talent Text")
        self.text_size_label.pack(anchor="w")

        self.show_colors = tk.Checkbutton(self, text="Show Colors")
        self.show_colors.pack(anchor="w")

        self.talent_text_scale = tk.Scale(
            self, orient="horizontal", label="Talent Text Size", showvalue=False,
            from_=0.7, to=3, resolution=0.1, variable=self.settings.scalers.talent,
        )
        self.talent_text_scale.pack(anchor="w")

        # font customization
        self.fonts = ["Courier", "Menlo", "Monaco"]
        self.font_family = tk.StringVar()
        self.font_family.set(self.settings.fonts.talent.family.get())
        self.font_family.trace("w", lambda *args: self.font_family_update())
        self.font_family_menu = tk.OptionMenu(self, self.font_family, *self.fonts)
        self.font_family_menu.pack(anchor="w")
        self.arrow_label = tk.Label(self, text="Arrow")
        self.arrow_label.pack(anchor="w")
        self.arrowcolor = tk.Button(self, text="Choose Arrow Color", command=self.color_chooser)
        self.arrowcolor.pack(anchor="w")

    def font_family_update(self):
        """Push font family update to other frames."""
        self.settings.fonts.talent.family.set(self.font_family.get())
        self.settings.fonts.monitor.family.set(self.font_family.get())
        self.settings.fonts.preview.family.set(self.font_family.get())

    def color_chooser(self, *args):
        color = self.settings.arrow.color
        # askcolor returns a tuple of (rgb, hex), note I am grabbing hex
        sel = askcolor(color=color.get(), title="Choose Arrow Color")[1]
        # TODO: update color as you are dragging around the color wheel. will probably need to
        # add something to the askcolor class
        if sel:
            color.set(sel)



