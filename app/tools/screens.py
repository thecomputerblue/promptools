import screeninfo
import logging

class Screens():
    """Class for managing monitors, which I call screens for disambiguation."""
    # TODO: move into another module

    def __init__(self, app):
        self.app = app
        self.scan()

    def scan(self):
        """Scan for connected monitors and update list."""

        # clear old
        self.screens = []

        # get monitor info
        for m in screeninfo.get_monitors():
            self.screens.append(m)

        logging.info(f'scanned screens and found: {self.screens}')

    @property
    def operator(self):
        """Return primary screen."""
        # TODO: confirm primary
        return self.screens[0]

    @property
    def talent(self):
        """Return secondary screen if one is attached, else primary."""
        # TODO: actually test that this isn't the primary
        return self.screens[-1]

    def are_multiple(self):
        self.scan()
        return len(self.screens) > 1
