# control mappings go here!
import logging

from tools.api import PrompToolsAPI

class AppControls(PrompToolsAPI):
    """Class for initializing all proprietary keyboard / mouse / controller
    functionality in promptools."""

    def __init__(self, app):
        PrompToolsAPI.__init__(self, app)

        self._init_global_controls(menu=self.app.gui.menu)
        self._init_talent_controls(talent=self.talent, scroller=self.scroller)
        self._init_monitor_controls(monitor=self.monitor, scroller=self.scroller)

    def _init_global_controls(self, menu):
        """Controls that work anywhere in the app."""
        self.gui.bind_all("<Command-o>", lambda _: menu.on_add_song_to_pool())
        self.gui.bind_all("<Command-l>", lambda _: menu.on_add_song_to_setlist())
        self.gui.bind_all("<Command-p>", lambda _: menu.on_load_cued_to_live())
        self.gui.bind_all("<Command-k>", lambda _: self.pp_style_fs_toggle())

    def _init_talent_controls(self, talent, scroller):
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

    def _init_monitor_controls(self, monitor, scroller):
        """Controls for the monitor/editor window."""

        # Key bindings to update talent view while editing.
        monitor.text.bind("<KeyRelease>", monitor.refresh_while_editing)
        # TODO: simpler method for this one
        # self.text.bind("<Button-1>", self.update_talent_view)
        monitor.text.bind("<MouseWheel>", monitor.update_talent_view)

        #edit toggle
        monitor.text.bind("<Command-e>", lambda _: monitor.do_edit_toggle())
        monitor.bind("<Command-e>", lambda _: monitor.do_edit_toggle())

        monitor.text.bind("<Command-r>", lambda _: monitor.try_reload_song())
        monitor.bind("<Command-r>", lambda _: monitor.try_reload_song())

        monitor.text.bind("<Command-s>", lambda _: monitor.save_song())
        monitor.bind("<Command-s>", lambda _: monitor.save_song())

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

    def pp_style_fs_toggle(self):
        """Presentation prompter inspired fullscreen toggle. Automatically
        switches off edit mode and goes full screen, or goes windowed and
        switches on edit mode. On two-screen systems it will eventually NOT
        toggle fullscreen on the talent screen, but instead toggle operator
        modules so the edit view is large and uncluttered while prompting."""

        self.pp_double() if self.app.tools.screens.are_multiple() else self.pp_single()

    def pp_single(self):
        logging.info('presentation prompter style toggle on 1 screen setup')
        if self.talent.fullscreen.get():
            self.talent.fullscreen.set(False)
            self.monitor.editable.set(True)
        else:
            self.monitor.editable.set(False)
            self.talent.fullscreen.set(True)
        # if talent fullscreen:
            # make windowed
            # enable edit mode
        # else:
            # disable edit mode
            # make fullscreen

    def pp_double(self):
        logging.info('presentation prompter style toggle on 2 screen setup')
