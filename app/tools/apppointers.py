import tkinter as tk 
import logging


class AppPointers:
    """Using multiple-inheritance, creates common interface in app modules
    for accessing app components."""

    def __init__(self, parent, *args, **kwargs):

        logging.info('initializing AppPointers')
        self.parent = parent
        self.app = parent.app
        self.suite = self if parent.suite == None else parent.suite

    # storing shortcuts as properties so components can all initialize
    # and call as needed, and so you can't overwrite these calls
    # locally in the app components (raises an error if you try).

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
    def dbmanager(self):
        return self.app.tools.dbmanager

    @property
    def helper(self):
        return self.app.tools.helper

    @property
    def loader(self):
        return self.app.tools.loader
    




    
    
    
    
"""
AppPointers.__init__(self, parent)
from tools.apppointers import AppPointers


"""