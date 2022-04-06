import tkinter as tk 
# import logging


class AppPointers:
    """Multiple-inherit or instantiate this as an attribute
    to give an object an interface for the rest of the app. Properties
    within this class reduce the amount of dot notation to access nested
    modules, and prevent accidental overwriting by the inheriting class."""

    def __init__(self, parent, *args, **kwargs):

        # attributes in the init method can be overwritten by modules
        # inheriting AppPointers. might do this for settings, where in
        # many modules it would be most useful to override the pointer
        # to a specific settings module.
        self.parent = parent
        self.app = parent.app
        self.suite = self if parent.suite == None else parent.suite
        # self.settings = self.app.settings

    @property
    def settings(self):
        return self.app.settings

    # data
    @property
    def data(self):
        return self.app.data

    @property
    def gig(self):
        return self.app.data.gigdata

    # song decks (playlist, history, etc)
    @property
    def deck(self):
        return self.app.deck

    # tools
    @property
    def tools(self):
        return self.app.tools

    @property
    def db_interface(self):
        return self.tools.db_interface

    @property
    def helper(self):
        return self.tools.helper

    @property
    def loader(self):
        return self.tools.loader

    @property
    def scroller(self):
        return self.tools.scroll

    # gui 
    @property
    def gui(self): 
        return self.app.gui

    @property
    def talent(self):
        return self.gui.talent

    # TODO: rename monitor instances to editor
    @property
    def monitor(self):
        return self.gui.monitor
    
    @property
    def editor(self):
        return self.gui.monitor

    @property
    def setlists(self):
        return self.app.collections.setlists

    @property
    def pool(self):
        return self.app.collections.pool

    

