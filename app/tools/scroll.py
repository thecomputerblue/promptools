import datetime

class ScrollTool():
    """Class for scroll & follow behaviors."""

    def __init__(self, app):
        self.app = app

        # init frame counter for delay comp
        self.reset_scroll_frame_counter()

    def reset_scroll_frame_counter(self):
        """Reset the frane counter for delay comp."""
        self.next_frame = datetime.datetime.now()

    def scroll_loop(self):
        """Schedulet the autoscroll based on rate slider."""
        app = self.app
        scroll = app.settings.scroll
        running = scroll.running.get()
        talent = app.talent

        # TODO: Move monitor.running to self
        # TODO: something seems like it could be optimized here...
        if running:
            rate = scroll.current.get()
            talent.scroll() if rate != 0 else None
            self.schedule_scroll()
        elif app.settings.scroll.mon_snap.get():
            app.monitor.match_sibling_yview()

            
    def scaled_sleep_time(self):
        """Sleep for the time set by the speed slider."""

        app = self.app
        pos = app.monitor.autoscroll_scale.get()
        # running = app.monitor.running.get()
        running = app.settings.scroll.running.get()
        rates = app.settings.scroll.rates

        return int(rates[pos]) if running else int(rates[-1])

    def start_scroll(self):
        """When you start scroll from stopped, reset next frame."""

        self.next_frame = datetime.datetime.now()
        self.schedule_scroll()

    def schedule_scroll(self):
        """Schedule next scroll, accounting for latency in the after queue."""

        self.app.after(self.delay_comp(), self.scroll_loop)

    def delay_comp(self):
        """Return ms with delay compensation for smoother autoscroll."""

        self.next_frame += datetime.timedelta(milliseconds=self.scaled_sleep_time())
        now = datetime.datetime.now()
        delta = max(datetime.timedelta(), self.next_frame - now)

        return int(delta.total_seconds() * 1000)

    def chunk_scroll(self, direction):
        """Scrolls for a little bit."""

        def toggle(chunk):
            chunk.enabled = False if chunk.enabled else True

        app = self.app
        settings = app.settings
        editing = settings.editor.enabled.get()

        # do not chunk scroll when editing
        if editing:
            return

        scroll = app.settings.scroll
        chunk = scroll.chunk
        talent = app.talent
        monitor = app.monitor

        if not chunk.enabled:

            duration = chunk.duration_ms
            pixels = chunk.pixels_advanced
            step = chunk.step

            chunk.enabled = True

            for i in range(0, duration, step):
                app.after(i, talent.scroll, direction)

            # allow overlapping chunk scrolls as long as first is half done.
            # TODO: make this configurable
            app.after(duration//2, lambda: toggle(chunk))

            mon_snaps_to_talent_pos = app.settings.scroll.mon_snap.get()
            if mon_snaps_to_talent_pos:
                app.after(duration, monitor.match_sibling_yview)

# TODO: re-integrate the monitor refresh loop
    def monitor_refresh_loop(self):
        """Refresh loop for monitor update."""
        # TODO: only run this when talent is running.
        # Currently scheduling even when talent is not running.
        app = self.app
        monitor = app.monitor
        ms = app.settings.scroll.mon_ms # TODO: MonitorSettings()

        # TODO: Get this running smoother someday. underlying tkinter issue imo
        if self.monitor_refresh_conditions():
            monitor.match_sibling_yview()

        app.after(ms, self.monitor_refresh_loop)

    def monitor_refresh_conditions(self):
        """Conditions for monitor refresh loop to execute refresh."""
        scroll = self.app.settings.scroll

        if scroll.mon_follow.get():
            return scroll.running

        return False


class AutoscrollBehavior():
    """Define range of speed values for autoscroll speed slider as a list."""

    def __init__(self, smin=0.1, smax=0.001, steps=101, *args, **kwargs):

        self.set(smin, smax, steps)

    def set(self, smin, smax, steps):
        # hard limit loop speed for safety.
        smin = self.limit(smin)
        smax = self.limit(smax)
        mult = 10 # mult to scale this up for my uses.

        # Max pixels per second
        xps  = 1 / smax
        inc = xps / steps

        # Make an empty list of correct length.
        vals = [None] * steps

        # Base pps for min speed.
        pix = 1 / smin

        for i in range(steps):
            vals[i] = 1 / pix * mult
            pix += inc

        self._vals = vals

    def limit(self, param, limit=0.0001):
        """Limit param value if it exceeds limit."""
        return limit if param < limit else param

    @property
    def vals(self):
        return self._vals