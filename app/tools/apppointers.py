import tkinter as tk 
# import logging


class AppPointers:
    """Multiple-inherit or instantiate this as an attribute
    to give an object an interface for the rest of the app. Properties
    within this class reduce the amount of dot notation to access nested
    modules, and prevent accidental overwriting by the inheriting class."""

    def __init__(self, parent, *args, **kwargs):

        # logging.info('initializing AppPointers')
        self.parent = parent
        self.app = parent.app
        self.suite = self if parent.suite == None else parent.suite

    @property
    def settings(self):
        return self.app.settings

    @property
    def data(self):
        return self.app.data

    @property
    def deck(self):
        return self.app.deck

    @property
    def tools(self):
        return self.app.tools

    @property
    def db_interface(self):
        return self.app.tools.db_interface

    @property
    def helper(self):
        return self.app.tools.helper

    @property
    def loader(self):
        return self.app.tools.loader

    @property
    def scroller(self):
        return self.app.tools.scroll

    @property
    def talent(self):
        return self.app.talent

    # TODO: RENAME MONITOR INSTANCES TO EDITOR
    @property
    def monitor(self):
        return self.app.monitor
    
    @property
    def editor(self):
        return self.app.monitor

    @property
    def setlists(self):
        return self.app.collections.setlists

    @property
    def pool(self):
        return self.app.collections.pool
    
    