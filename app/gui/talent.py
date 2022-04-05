import tkinter as tk
import logging

from tools.apppointers import AppPointers

# logging.basicConfig(level=logging.INFO)

# helpers
def fs_coords(operator, talent):
    """Return dict of talent and operator coords for go_fullscreen"""
    coords = {}

    # offset coords
    coords["xoffs"] = talent.x
    coords["yoffs"] = talent.y

    # screen sizes
    coords["tw"] = talent.width
    coords["th"] = talent.height
    coords["ow"] = operator.width
    coords["oh"] = operator.height

    return coords


class TalentWindow(tk.Toplevel, AppPointers):
    """Class for the Talent POV, which should be identical to the TalentMonitor
    but scaled to full screen on a second screen."""

    def __init__(self, gui, *args, **kwargs):
        tk.Toplevel.__init__(
            self,
            gui.root,
            highlightthickness=10,
            highlightbackground="black",  # when frame is out of focus
            highlightcolor="black",
        )
        AppPointers.__init__(self, gui)

        # context
        # self.parent = parent
        # self.app = parent
        # self.suite = self

        self.window = self
        self.screens = self.tools.screens
        # self.settings = self.app.settings

        # window settings
        self.title("Talent")
        # minimize instead of close window with X
        self.protocol("WM_DELETE_WINDOW", self.iconify)

        # Current frame song
        self.song = None

        self.pixels = self.settings.scroll.pixels.get()
        self.frozen = False  # TODO: move to settings

        # fullscreen tkvar. trace to trigger toggle
        self.fullscreen = self.settings.view.fullscreen
        self.fullscreen.trace("w", lambda *args: self.toggle_fullscreen())

        # store window dimensions for fullscreen toggle
        self.store_winfo()

        # widgets
        # Dummy scrollbar so I can clone talent monitor y_pos.
        # TODO: probably not needed, can probably just grab text yview
        self.scrollbar = tk.Scrollbar(self, orient="vertical")

        self.text = tk.Text(
            self,
            font=self.settings.fonts.talent,
            height=15,
            width=45,
            bg="black",
            fg="white",
            state="disabled",
            borderwidth=0,
            highlightthickness=0,
            yscrollcommand=self.scrollbar.set,
            wrap=self.settings.view.text_wrap,
            # cursor='hand2'
        )
        self.text.grid(row=0, column=1, sticky="nesw")

        self.arrow = PromptArrow(self, width=40, height=100)
        self.arrow.grid(row=0, column=0, ipadx=20, sticky="nesw")

        # popup menu
        # TODO: popup color swatch for arrow? low priority
        self.popup_menu = RightClickMenu(self)
        self.bind("<Button-2>", self.popup_menu.do_popup)

        # grid config
        # determines ratio of arrow to text field.
        # TODO: move to settings, make adjustable in preferences
        self.grid_columnconfigure(0, weight=2)
        self.grid_columnconfigure(1, weight=15)
        # giving columns weight allows vertical expansion.
        self.grid_rowconfigure(0, weight=1)

        # scaler
        self.text_scaler = TextScaler(self)  # TODO: move to app tools?
        # self.config(cursor='pencil')

        # callbacks
        self.deck.add_callback("live", self.push)
        self.settings.scroll.add_callback(self.refresh_scroll)

    def refresh_scroll(self, *args):
        """Fetch scroll params."""
        self.pixels = self.settings.scroll.pixels.get()

    def push(self):
        self.loader.push(frame=self, song=self.deck.live, reset_view=True)

    def store_winfo(self):
        """Snapshot winfo to restore later."""

        # TODO: might be able to remove this
        # method as I'm using the Mac windows management now.
        self.win_x = self.winfo_width()
        self.win_y = self.winfo_height()

    def match_sibling_yview(self):
        mon_y = self.monitor.text.yview()
        self.text.yview_moveto(mon_y[0])

    def esc_fs_toggle(self, event):
        self.fullscreen.set(False if self.fullscreen.get() else True)

    def receive_edits(self, tk_text_dump):
        """When editing monitor window, send the new text to this to update."""
        if self.frozen:
            return
        loader = self.tools.loader
        mon = self.monitor.text
        tal = self.text
        loader.clone_tk_text(mon, tal)

    def scroll(self, direction="down"):
        """Talent scroll behavior."""
        x_scroll = self.text.xview_scroll
        y_scroll = self.text.yview_scroll
        amt = self.scale_pixels_by_font_size(self.pixels)
        if direction == "up":
            y_scroll(-amt, "pixels")
        elif direction == "down":
            y_scroll(amt, "pixels")
        elif direction == "right":
            x_scroll(-amt, "pixels")
        elif direction == "left":
            x_scroll(amt, "pixels")

    def scale_pixels_by_font_size(self, amt):
        """Scale pixel increment by text size for more consistent speed on resize."""
        if not amt:
            return 0
        scaler = self.gen_font_scaler()
        return max(1, int(amt * scaler))

    def gen_font_scaler(self):
        """Generate a float which scales pixel rate in a helpful way."""
        base = self.text_scaler.font_size
        normal = 44  # 'normal' font size. bigger skips more pixels, smaller fewer.
        return base / normal

    def toggle_fullscreen(self):
        self.go_windowed() if self.fullscreen.get() else self.go_fullscreen()

    def go_fullscreen(self):
        logging.info("talent went window")
        self.window.wm_attributes("-fullscreen", False)
        self.window.wm_attributes("-topmost", False)
        self.window.geometry(f"{self.window.win_x}x{self.window.win_y}")

    def go_windowed(self):
        c = fs_coords(
            operator=self.suite.screens.operator, talent=self.suite.screens.talent
        )
        logging.info("talent went fullscreen")
        self.deiconify()
        self.window.store_winfo()
        self.window.wm_attributes("-topmost", True)
        self.window.wm_attributes("-fullscreen", True)
        self.window.geometry(
            f"{c.get('tw')}x{c.get('th')}+{c.get('xoffs')}-{c.get('yoffs')}"
        )


class PromptArrow(tk.Frame, AppPointers):
    """Frame for scroll arrow."""

    def __init__(self, parent, *args, **kwargs):
        tk.Frame.__init__(self, parent)
        AppPointers.__init__(self, parent)

        # self.parent = parent
        # self.app = parent.app
        # self.settings = self.app.settings.arrow
        # # Sibling arrow for two-way positional update, not currently used...
        self.sibling = None

        self.canvas = self.create_canvas(**kwargs)
        self.canvas.pack(expand=True, fill="both")

        self.mainframe()

    def mainframe(self):

        # Define starting coordinates of upper left vertex.
        # TODO: define y as 'window starting height' / 2.
        x, y = 0, 80

        # Create the triangle polygon that will serve as the prompter arrow.
        # TODO: storing this just creates an int.
        self.create_arrow(
            canvas=self.canvas,
            x=x,
            y=y,
            color=self.settings.arrow.color.get(),
            outline=self.settings.arrow.outline.get(),
            borderwidth=self.settings.arrow.borderwidth.get(),
        )

        # Make the canvas elements scale with the window.
        self.scaler = ArrowScaler(self)
        self.scaler.bind_config()

        # Track dragging motion.
        self._drag_data = {"x": 0, "y": 0, "item": None}

        # Bind DnD behavior to anything tagged 'arrow'.
        self.canvas.tag_bind("arrow", "<ButtonPress-1>", self.drag_start)
        self.canvas.tag_bind("arrow", "<ButtonRelease-1>", self.drag_stop)
        self.canvas.tag_bind("arrow", "<B1-Motion>", self.drag)

        self.settings.arrow.add_callback(self.color_arrow)

    def create_canvas(self, *args, **kwargs):
        """Create the canvas."""
        canvas = tk.Canvas(
            self, bg="black", highlightthickness=0, borderwidth=0, **kwargs
        )

        return canvas

    def create_arrow(self, canvas, x, y, color, outline, borderwidth):
        """Create the teleprompter arrow polygon."""

        # Map vertices. Arrow shape.
        x0, y0 = x + 0, y + 0
        x1, y1 = x + 75, y + 50
        x2, y2 = x + 0, y + 100

        arrow = canvas.create_polygon(
            x0,
            y0,
            x1,
            y1,
            x2,
            y2,
            fill=color,
            outline=outline,
            width=borderwidth,
            tags="arrow",
        )

        # return arrow

    def color_arrow(self):
        arrow = self.settings.arrow
        color = (arrow.color.get(),)
        outline = (arrow.outline.get(),)
        borderwidth = arrow.borderwidth.get()
        self.canvas.itemconfig(
            "arrow",
            fill=(arrow.color.get(),),
            outline=(arrow.outline.get(),),
            width=arrow.borderwidth.get())

    def drag_start(self, event):
        """Begining drag of an object"""
        # record the item and its location
        self._drag_data["item"] = self.canvas.find_closest(event.x, event.y)[0]
        self._drag_data["x"] = event.x
        self._drag_data["y"] = event.y

    def drag_stop(self, event):
        """End drag of an object"""
        # reset the drag information
        self._drag_data["item"] = None
        self._drag_data["x"] = 0
        self._drag_data["y"] = 0

    def drag(self, event):
        """Handle dragging of an object"""
        # TODO: make this less... squirmy
        # move arrow, keeping within view
        obj = self._drag_data["item"]
        coords = self.canvas.coords(obj)
        self.drag_obj(
            canvas=self.canvas,
            obj=obj,
            head=coords[1],
            foot=coords[5],
            deltas=self.deltas(event),
            win_xy=self.win_xy(),
        )
        self.update_pos(event)

    def win_xy(self):
        return (self.winfo_width(), self.winfo_height())

    def drag_obj(self, canvas, obj, head, foot, deltas, win_xy):
        # TODO: move out of this class since it isn't dependent on it
        if head < 0:
            canvas.move(obj, 0, 1)
        elif foot > win_xy[1] and head > 0:
            canvas.move(obj, 0, -1)
        else:
            canvas.move(obj, 0, deltas[1])

    def update_pos(self, event):
        self._drag_data["x"] = event.x
        self._drag_data["y"] = event.y

    def deltas(self, event) -> tuple:
        delta_x = event.x - self._drag_data["x"]
        delta_y = event.y - self._drag_data["y"]
        return (delta_x, delta_y)

    def move_sibling(self, delta_y):
        """Update arrow position to match position of another arrow."""

        # TODO: sibling currently disabled. may not use

        if not self.sibling:
            logging.info("Havent't defined arrow sibling.")
            return

        # TODO: This obviously will need to scale so arrows are pointing
        # at the same text. Figure out the formula. I think it will involve
        # instantiating the talent window at the exact size of the monitor
        # window then scaling from there.
        self.sibling.canvas.move(self._drag_data["item"], 0, delta_y)


class ArrowScaler:
    """Class that manages scaling the prompter arrow when the window scales."""

    def __init__(self, parent):

        self.parent = parent
        # Declare generic starting dimensions. These affect the scaling of the
        # arrow...
        # TODO: sloppy. can probably get the intended dimensions from somewhere
        # without causing the 1x1 glitch.
        self.width = 100
        self.height = 200

        # Because the init dimensions are 1x1 this doesn't work, breaks the triangle.
        # self.width, self.height = parent.winfo_width(), parent.winfo_height()
        self.__func_id = None

    def bind_config(self):
        self._func_id = self.parent.bind("<Configure>", self.resize)

    def resize(self, event):
        """If frame size has changed, determine the scale difference."""
        if event.widget != self.parent or (
            self.width == event.width and self.height == event.height
        ):
            return
        wscale = float(event.width) / self.width
        hscale = float(event.height) / self.height
        self.width, self.height = event.width, event.height
        self.resize_shapes(wscale, hscale)

    def resize_shapes(self, wscale, hscale):
        """Resize canvas shapes, retaining proportions."""
        # change last arg to 'hscale' to allow arrow to deform
        self.parent.canvas.scale("all", 0, 0, wscale, wscale)


class TextScaler:
    """Track resizing of Talent window to update font size."""

    def __init__(self, parent):
        self.parent = parent
        self.app = parent.app
        self.suite = parent.suite
        self.settings = parent.settings

        # Don't get w x h from w_info because they start at 1 x 1
        # which breaks arrow scaling.
        self.width, self.height = self.suite.winfo_width(), self.suite.winfo_height()
        # self.width, self.height = 640, 480
        self._func_id = None
        self.bind_config()
        # self.scale_text()

        # set default font size (used to scale scrolling speed)
        self.font_size = self.gen_font_size()

        # callback for refresh
        scaler = self.settings.scalers.talent
        scaler.trace("w", lambda *args: self.refresh_font())

        # refresh font when it changes
        self.settings.fonts.talent.add_callback(self.refresh_font)

    def bind_config(self):
        self._func_id = self.suite.bind("<Configure>", self.on_window_resize)

    def on_window_resize(self, event):
        """Calculate new text on resize."""
        if event.widget != self.suite or not self.valid_resize(event):
            return
        self.width, self.height = event.width, event.height
        self.refresh_font()

    def valid_resize(self, event):
        """Need to reject exceedingly small resizes, which happen at tkinter
        init, and which break scaling on arrow / text."""
        if event.width <= 1 or event.width <= 1:
            return False
        if self.size_changed(event):
            return True

    def size_changed(self, event):
        return self.width != event.width and self.height != event.height

    def refresh_font(self):
        """Update the font parameters."""

        # get base font
        font = self.settings.fonts.talent.copy()
        # apply custom params
        self.font_size = self.gen_font_size()
        font.config(size=self.font_size)
        font.config(family=self.get_font_family())
        # apply customized font to text widget
        self.suite.text.tag_configure("size", font=font)
        # TODO: maybe this should live in settings...

    def gen_font_size(self):
        """Formula for calculating font size."""
        s = self.settings.scalers
        return int(
            (self.width * s.talent.get() * s.all.get()) // 30
        )  # <- TODO: // value could be stored in settings

    def get_font_family(self):
        """Get font family from settings."""
        logging.info("trying to get font family")
        return self.settings.fonts.talent.family.get()


class RightClickMenu(tk.Frame):
    """Menu for when you right click within monitor frame."""

    def __init__(self, parent, *args, **kwargs):
        tk.Frame.__init__(self, parent)

        self.parent = parent
        self.app = parent.app
        self.suite = parent.suite
        self.window = parent.window

        self.fullscreen = False

        # main menu
        main_menu = tk.Menu(self.parent, title="Talent Options")
        main_menu.add_checkbutton(label="Fullscreen", variable=self.window.fullscreen)

        self.main_menu = main_menu

    def do_popup(self, event):
        """Popup right click menu."""
        # TODO: need to get screen info and offset x_root, and y_root as appropriate.
        try:
            logging.info(f"popup coords: {event.x_root}, {event.y_root}")
            self.main_menu.tk_popup(event.x_root, event.y_root)
        finally:
            self.main_menu.grab_release()
