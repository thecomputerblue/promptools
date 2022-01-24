import tkinter as tk
import logging

logging.basicConfig(level=logging.INFO)

class TalentWindow(tk.Toplevel):
    """Class for the Talent POV, which should be identical to the TalentMonitor
	but scaled to full screen on a second screen."""

    def __init__(self, parent, *args, **kwargs):
        tk.Toplevel.__init__(
            self,
            parent.frame,
            highlightthickness=10,
            highlightbackground="black",  # when frame is out of focus
            highlightcolor="black",
        )

        # context
        self.parent = parent
        self.app = parent
        self.suite = self
        self.window = self
        self.screens = self.app.tools.screens
        self.settings = self.app.settings

        # window settings
        self.title("Talent")
        # minimize instead of close window with X
        self.protocol("WM_DELETE_WINDOW", self.iconify)

        # Current frame song
        self.song = None
        # Pixel increment
        self.pixels = self.settings.scroll.pixels


        self.frozen = False #TODO: move to settings

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



        # scroll bindings
        self.bind("<space>", lambda _: self.app.monitor.toggle_scroll())
        self.bind("<KeyPress-Shift_L>", lambda _: self.app.monitor.shift_scroll_on())
        self.bind("<KeyRelease-Shift_L>", lambda _: self.app.monitor.shift_scroll_off())
        self.bind("<KeyPress-Shift_R>", lambda _: self.app.monitor.shift_scroll_on())
        self.bind("<KeyRelease-Shift_R>", lambda _: self.app.monitor.shift_scroll_off())
        self.bind("<.>", lambda _: self.app.monitor.arrow_scroll(direction="down"))
        self.bind("<,>", lambda _: self.app.monitor.arrow_scroll(direction="up"))

        # scaler
        self.text_scaler = TextScaler(self) # TODO: move to app tools?
        # self.config(cursor='pencil')

        # callback
        self.app.deck.add_callback('live', self.push)

    def push(self):
        live = self.app.deck.live
        # TODO: reset view test
        self.app.tools.loader.push(frame=self, song=live, reset_view=True)

    def store_winfo(self):
        """Snapshot winfo to restore later."""

        # TODO: might be able to remove this
        # method as I'm using the Mac windows management now.
        self.win_x = self.winfo_width()
        self.win_y = self.winfo_height()

    def match_sibling_yview(self):
        """Match monitor yview."""

        mon_y = self.app.monitor.text.yview()
        self.text.yview_moveto(mon_y[0])

    def receive_edits(self, tk_text_dump):
        """When editing monitor window, send the new text to this to update."""
        if not self.frozen:

            loader = self.app.tools.loader
            mon = self.app.monitor.text
            tal = self.text 
            
            loader.clone_tk_text(mon, tal)

    def scroll(self, direction="down"):
        """Advance scroll based on pixels size."""

        amt = self.pixels if direction=="down" else -self.pixels
        self.text.yview_scroll(amt, "pixels")

    def toggle_fullscreen(self):
        """Toggle the border of the talent window, which can be distracting."""
        operator = self.suite.screens.operator
        talent = self.suite.screens.talent
        # x=0, y=0, width=2560, height=1080, width_mm=None, height_mm=None, name=None, is_primary=True

        # offset coords
        xoffs = talent.x
        yoffs = talent.y

        # screen sizes
        tw = talent.width
        th = talent.height 
        ow = operator.width
        oh = operator.height

        # xw = operator.width
        # xh = operator.height

        if not self.fullscreen.get():
            # toggle OFF
            logging.info('talent went window')
            self.window.wm_attributes("-fullscreen", False)
            self.window.wm_attributes('-topmost', False)
            self.window.geometry(f"{self.window.win_x}x{self.window.win_y}")
        else:
            # toggle ON
            logging.info('talent went fullscreen')
            self.deiconify()
            self.window.store_winfo()
            self.window.wm_attributes('-topmost', True)
            self.window.wm_attributes("-fullscreen", True)
            self.window.geometry(f'{tw}x{th}+{xoffs}-{yoffs}')

class PromptArrow(tk.Frame):
    """Frame for scroll arrow."""

    def __init__(self, parent, *args, **kwargs):
        tk.Frame.__init__(self, parent)

        self.parent = parent
        self.app = parent.app
        self.settings = self.app.settings.arrow
        # Sibling arrow for two-way positional update.
        self.sibling = None

        # Create canvas
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
            color=self.settings.color.get(),
            outline=self.settings.outline.get(),
            borderwidth=self.settings.borderwidth.get()
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

    def create_canvas(self, *args, **kwargs):
        """Create the canvas."""
        canvas = tk.Canvas(
            self,
            bg="black",
            highlightthickness=0,
            borderwidth=0,
            **kwargs
        )

        return canvas

    def create_arrow(self, canvas, x, y, color, outline, borderwidth):
        """Create the teleprompter arrow polygon."""

        # Map vertices. Arrow shape.
        x0, y0 = x + 0, y + 0
        x1, y1 = x + 75, y + 50
        x2, y2 = x + 0, y + 100

        arrow = canvas.create_polygon(
            x0, y0, x1, y1, x2, y2, fill=color, outline=outline, width=borderwidth, tags="arrow"
        )

        # return arrow

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
        # TODO: prevent dragging out of sight.

        # Compute how much the mouse has moved.
        delta_x = event.x - self._drag_data["x"]
        delta_y = event.y - self._drag_data["y"]
        # Move the object the appropriate amount.
        # 0 is x, vertical drag only...


        # TODO: make this less... squirmy
        # move arrow, keeping within view
        coords = self.canvas.coords(self._drag_data["item"])
        arrow_top = coords[1]
        arrow_foot = coords[5]
        win_y = self.winfo_height()
        
        if arrow_top < 0:
            self.canvas.move(self._drag_data["item"], 0, 1)

        elif arrow_foot > win_y and arrow_top > 0: 
            self.canvas.move(self._drag_data["item"], 0, -1)

        else:
            self.canvas.move(self._drag_data["item"], 0, delta_y)  

        # record the new position
        self._drag_data["x"] = event.x
        self._drag_data["y"] = event.y

    def arrow_within_view(self, event):
        """Return True if y value is within the bounds of the screen."""

    def move_sibling(self, delta_y):
        """Update arrow position to match position of another arrow."""

        # TODO: sibling currently disabled. may not use

        if not self.sibling:
            logging.info('Havent\'t defined arrow sibling.')
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

        if event.widget == self.parent and (
            self.width != event.width or self.height != event.height
        ):

            # Get the % change as a float (should be around 1 +- .1)
            wscale = float(event.width) / self.width
            hscale = float(event.height) / self.height

            # Update dimensions
            self.width, self.height = event.width, event.height

            # Scale the arrow (and whatever else is in there...)
            self.resize_shapes(wscale, hscale)

    def resize_shapes(self, wscale, hscale):
        """Resize canvas shapes, retaining proportions."""
        # Change last arg to 'hscale' to allow arrow to deform
        self.parent.canvas.scale("all", 0, 0, wscale, wscale)


class TextScaler:
    """Track resizing of Talent window to update font size. """

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


    def bind_config(self):
        self._func_id = self.suite.bind("<Configure>", self.on_resize)

    def on_resize(self, event):
        """Calculate new text on resize."""
        # TODO: this is a hack to ignore the momentary 1x1 resize on program init.
        if event.widget == self.suite and event.width <= 1 or event.width <= 1:
            logging.info("talent window was resized to 1x1 or less. text not resized.")
            return

        if event.widget == self.suite and (
            self.width != event.width or self.height != event.height
        ):
            logging.info(f'{event.widget=}: {event.height=}, {event.width=}\n')

            # Scaling for arrow resize.
            wscale = float(event.width) / self.width
            hscale = float(event.height) / self.height

            self.width, self.height = event.width, event.height

            self.scale_text()

    def scale_text(self):
        # Font
        font = self.settings.fonts.talent

        # Size formula
        self.size = self.width // 30

        # Construct new.
        # TODO: switch to tuple
        new = font.copy()
        new.config(size=self.size)
        # new = font + " " + str(self.size)

        # Update text and arrow size.
        self.suite.text.tag_configure("size", font=new)
        # self.app.arrow.pack_config(ipady=size)

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
        main_menu = tk.Menu(self.parent, title='Talent Options')
        main_menu.add_checkbutton(label="Fullscreen", variable=self.window.fullscreen)

        self.main_menu = main_menu

    def do_popup(self, event):
        """Popup right click menu."""
        # TODO: need to get screen info and offset x_root, and y_root as appropriate.
        try:
            logging.info(f'popup coords: {event.x_root}, {event.y_root}')
            self.main_menu.tk_popup(event.x_root, event.y_root)
        finally:
            self.main_menu.grab_release()