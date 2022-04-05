# control mappings go here!
import logging

from tools.apppointers import AppPointers

class AppControls(AppPointers):
    """Class for initializing all proprietary keyboard / mouse / controller
    functionality in promptools."""

    def __init__(self, app):
        AppPointers.__init__(self, app)

        self.init_global_controls(menu=self.app.gui.menu)
        self.init_talent_controls(talent=self.talent, scroller=self.scroller)
        self.init_monitor_controls(monitor=self.monitor, scroller=self.scroller)

    def init_global_controls(self, menu):
        """Controls that work anywhere in the app."""
        self.gui.bind_all("<Command-o>", lambda _: menu.on_add_song_to_pool())
        self.gui.bind_all("<Command-l>", lambda _: menu.on_add_song_to_setlist())
        self.gui.bind_all("<Command-p>", lambda _: menu.on_load_cued_to_live())

    def init_talent_controls(self, talent, scroller):
        """Controls for the talent window."""
        # autoscroll
        talent.bind("<space>", lambda _: scroller.toggle_scroll())
        # shift scroll
        talent.bind("<KeyPress-Shift_L>", lambda _: scroller.shift_scroll_on())
        talent.bind("<KeyRelease-Shift_L>", lambda _: scroller.shift_scroll_off())
        talent.bind("<KeyPress-Shift_R>", lambda _: scroller.shift_scroll_on())
        talent.bind("<KeyRelease-Shift_R>", lambda _: scroller.shift_scroll_off())
        # chunk scroll
        talent.bind("<.>", lambda _: scroller.chunk_scroll(direction="down"))
        talent.bind("<,>", lambda _: scroller.chunk_scroll(direction="up"))
        talent.bind("</>", lambda _: scroller.chunk_scroll(direction="left"))
        talent.bind("<z>", lambda _: scroller.chunk_scroll(direction="right"))
        # carriage return
        talent.bind("<Return>", lambda _: self.talent_on_enter(scroller))
        talent.bind("<KeyPress-Escape>", talent.esc_fs_toggle)

    def init_monitor_controls(self, monitor, scroller):
        """Controls for the monitor/editor window."""

        # Key bindings to update talent view while editing.
        monitor.text.bind("<KeyRelease>", monitor.refresh_while_editing)
        # TODO: simpler method for this one
        # self.text.bind("<Button-1>", self.update_talent_view)
        monitor.text.bind("<MouseWheel>", monitor.update_talent_view)

        #edit toggle
        monitor.text.bind("<Command-e>", monitor.toggle_edit)
        monitor.bind("<Command-e>", monitor.toggle_edit)

        # self.text.bind("<space>", lambda _: self.toggle_scroll())
        # Make it so clicking in the talent window gives frame focus.
        monitor.bind("<Button-1>", lambda _: monitor.on_focus())
        monitor.text.bind("<Button-1>", lambda _: monitor.on_focus())

        # Scroll key bindings. These need to be bound to inner & outer frame
        # TODO: figure if there is a way to bind just once
        monitor.bind("<space>", lambda _: scroller.toggle_scroll())
        monitor.text.bind("<space>", lambda _: scroller.toggle_scroll())

        monitor.bind("<KeyPress-Shift_L>", lambda _: scroller.shift_scroll_on())
        monitor.text.bind("<KeyPress-Shift_L>", lambda _: scroller.shift_scroll_on())

        monitor.bind("<KeyRelease-Shift_L>", lambda _: scroller.shift_scroll_off())
        monitor.text.bind("<KeyRelease-Shift_L>", lambda _: scroller.shift_scroll_off())

        monitor.bind("<KeyPress-Shift_R>", lambda _: scroller.shift_scroll_on())
        monitor.text.bind("<KeyPress-Shift_R>", lambda _: scroller.shift_scroll_on())

        monitor.bind("<KeyRelease-Shift_R>", lambda _: scroller.shift_scroll_off())
        monitor.text.bind("<KeyRelease-Shift_R>", lambda _: scroller.shift_scroll_off())

        # chunk scroll controls
        monitor.bind("<.>", lambda _: scroller.chunk_scroll(direction="down"))
        monitor.text.bind("<.>", lambda _: scroller.chunk_scroll(direction="down"))

        monitor.bind("<,>", lambda _: scroller.chunk_scroll(direction="up"))
        monitor.text.bind("<,>", lambda _: scroller.chunk_scroll(direction="up"))

        monitor.bind("</>", lambda _: scroller.chunk_scroll(direction="left"))
        monitor.text.bind("</>", lambda _: scroller.chunk_scroll(direction="left"))

        monitor.bind("<z>", lambda _: scroller.chunk_scroll(direction="right"))
        monitor.text.bind("<z>", lambda _: scroller.chunk_scroll(direction="right"))

        monitor.bind("<Return>", lambda _: scroller.carriage_return())
        monitor.text.bind("<Return>", lambda _: scroller.carriage_return())

        # Binding to get coords of selected text. Will use this later for applying color tags.
        monitor.text.bind("<ButtonRelease>", lambda _: monitor.selection_info())

        monitor.text.bind("<Double-Button-1>", monitor.double_clicked_text)
        # self.text.bind("<BackSpace>", self.on_backspace)

        # binding for popup menu
        monitor.text.bind("<Button-2>", monitor.menu.do_popup)