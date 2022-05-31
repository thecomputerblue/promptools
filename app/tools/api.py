import tkinter as tk 
# import logging


class PrompToolsAPI:
    """API to simplify communication between modules. TODO: As of 5/31/22
    multiple-inherited to a bunch of modules, plan to change this..."""

    def __init__(self, parent, *args, **kwargs):
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
        return self.app.data.setlists

    @property
    def pool(self):
        return self.app.data.pool

    

