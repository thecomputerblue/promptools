# components of the quick browser go here.

import string
import tkinter as tk
from tkinter import ttk
import pickle
import logging

from os import listdir
from os.path import isfile, join, exists

# helpers
def scrub_text(text):
    """Remove text formatting for search comparison."""
    text = text.strip().lower()
    text = text.translate(str.maketrans('', '', string.punctuation))
    return text


class BrowserSuite(tk.Frame):
    """Quick browser for files and the library database."""

    def __init__(self, parent, *args, **kwargs):
        tk.Frame.__init__(self, parent.frame)

        self.parent = parent
        self.app = parent
        self.suite = self
        self.settings = parent.settings

        # search bar
        self.search = SearchBar(self)
        self.search.pack(side="top", anchor="n", fill="x")

        # tk notebook with file + library tabs.
        # TODO: tab with integrated finder-like browser?
        self.tabs = BrowserNotebook(self)
        self.tabs.pack(side="bottom", anchor="n", fill="both", expand=True)

        # expose tab contents more shallowly
        self.files = self.tabs.files
        self.library = self.tabs.library 

        # trace search & update files / library filters
        query = self.search.query
        query.trace("w", lambda *args: self.files.search_trace(query.get()))
        query.trace("w", lambda *args: self.library.search_trace(query.get()))

        # frame settings   
        # stop frame from resizing when info spills.
        # self.pack_propagate(False)

        # weigh column so it fills correctly
        # self.columnconfigure(0, weight=1)

        # prevent h-scroll
        # self.listbox.bind('<Right>', lambda event: "break")

        # generate the file list and update the window
        # TODO: probably move this into the FilesTab class

class SearchBar(tk.Frame):
    """Frame for the search bar and any options."""

    def __init__(self, parent, *args, **kwargs):
        tk.Frame.__init__(self, parent)

        # orient
        self.parent = parent
        self.app = parent.app
        self.suite = parent.suite
        self.settings = parent.settings

        # search query var
        self.query = tk.StringVar()

        self.entry = tk.Entry(self, textvariable=self.query)
        self.header = QuickSearchHeader(self, entry=self.entry)

        self.header.pack(side="top", fill="x")
        self.entry.pack(side="top", fill="x")

        self.entry.bind("<Down>", self.focus_set_active_tab_from_search)

    def focus_set_active_tab_from_search(self, event=None):
        """Change focus from search entry to active tab."""
        t = self.get_active_tab()
        if t == 0:
            self.focus_set_library_from_search()
        elif t == 1:
            self.focus_set_files_from_search()
        else:
            logging.warning("focus_set_active_tab_from_search didn't know what to do with tab id")

    def focus_set_files_from_search(self, event=None):
        """When you press the down arrown in search field,
        move focus to the search field."""

        # TODO: if list item was previously selected, focus to that. Basically
        # change (0) to whatever the widget variable is for focused item.
        l = self.suite.files.listbox
        # Move focus to listbox.
        l.focus_set()
        # Immediately focus the first list item.
        if not l.curselection():
            l.select_set(0)

    def focus_set_library_from_search(self, event=None):
        l = self.suite.library.tree
        # TODO: does not focus if nothing was previously selected.
        # can't figure out the magic word!!!
        # TODO: need to look at callback that loads selection.
        sel = l.focus() if l.focus() is not "" else 0
        l.selection_set(sel)
        l.focus_set()


    def get_active_listbox(self):
        """Return the listbox of the currently open tab."""
        return self.get_active_tab().listbox

    def get_active_tab(self):
        """Return the index of the currently open tab."""
        nb = self.suite.tabs
        i = nb.index(nb.select())
        return i


class BrowserNotebook(ttk.Notebook):
    """Notebook whose pages are different targets for the quick search.
    By default this will have a file browser for quick import, and a
    simplified library browser (references the DB)."""

    def __init__(self, parent):
        ttk.Notebook.__init__(self, parent,
            padding=0
            )

        self.app = parent.app
        self.suite = parent.suite

        self.library = LibraryTab(self)
        self.library.pack(fill="both", expand=True)
        self.add(self.library, text="Library")

        self.files = FilesTab(self)
        self.files.pack(fill="both", expand=True)
        self.add(self.files, text="Files")


class LibraryTab(tk.Frame):
    """Frame for the Library browser."""

    def __init__(self, parent):
        tk.Frame.__init__(self, parent)

        self.app = parent.app
        self.suite = parent.suite

        self.tv = ScrolledTreeview(self)
        self.tv.pack(fill='both', expand=True)

        # expose treeview
        self.tree = self.tv.tree

        self.refresh_library()

    def search_trace(self, query):
        """Filter library tree by search contents."""

        self.refresh_library(query=query)

    def refresh_library(self, data=None, query=None):
        """Generate the library song list."""

        # clear tree
        self.clear_tree()

        # get song metadata
        if data is None:
            dbmanager = self.app.tools.dbmanager
            data = dbmanager.get_all_song_meta_from_db(option='library')

        # filter by search
        data = self.filter_library(data, query) if query else data

        # sort by song name
        # TODO: retrieve name index dynamically
        name_index = 2
        data.sort(key=lambda t:t[name_index])

        # insert to tree
        for i, meta in enumerate(data):
            song_id, lib_id, name, created, modified, comments, confidence, def_key = meta
            needed = (song_id, lib_id, name)
            self.tree.insert(parent='', index="end", iid=i, values=needed)

        # self.treeview_sort()

    def filter_library(self, data, query):
        """Return data filtered by query."""

        if not query:
            return data

        # TODO: filter() / comprehension?
        filtered = []
        for tup in data:
            filtered.append(tup) if scrub_text(query) in scrub_text(tup[2]) else None

        return filtered

    def clear_tree(self):
        """Clear the tree."""

        for item in self.tree.get_children():
            self.tree.delete(item)

    def treeview_sort(self):
        """Sort the treeview alphabetically."""
        logging.info('treeview_sort in ScrolledTreeview')
        reverse = False
        t = self.tree

        l = [(t.item(k)["text"], k) for k in t.get_children()]
        l.sort(key=lambda t: t[1], reverse=reverse)

        for index, (val, k) in enumerate(l):
            t.move(k, '', index)

        # t.heading(col, command=lambda: treeview_sort_column())


class ScrolledTreeview(tk.Frame):
    """Attach a scrollbar to treeview."""

    def __init__(self, parent):
        tk.Frame.__init__(self, parent)

        self.app = parent.app
        self.suite = parent.suite

        # library data tree (left side of frame)
        tree = ttk.Treeview(self, selectmode="browse", show="tree")
        tree['columns']=("song_id", "lib_id", "name")
        
        tree.column("#0", width=0, stretch=False)
        tree.column("song_id", width=0, anchor="center", stretch=False)
        tree.column("lib_id", width=0, anchor="center",stretch=False)
        tree.column("name", anchor="w", stretch=True)


        tree.heading("#0", text='', anchor="center")
        tree.heading("song_id", text="song_id", anchor="center")
        tree.heading("lib_id", text="lib_id", anchor="center")
        tree.heading("name", text="title", anchor="w")

        tree.pack(side="left", fill="both", expand=True)
        self.tree = tree

        self.scrollbar = ttk.Scrollbar(self, orient="vertical")
        self.scrollbar.config(command=self.tree.yview)
        self.tree.configure(yscrollcommand=self.scrollbar.set)
        self.scrollbar.pack(side="left", fill="y")

        self.tree.bind("<<TreeviewSelect>>", self.on_tree_select)

    def on_tree_select(self, event):
        """Make a song obj from library selection and push to cued."""

        sel = self.tree.focus()
        song_id = self.tree.set(sel, column="song_id")
        song_data = self.app.tools.dbmanager.make_song_dict_from_db(song_id=song_id)
        song_obj = self.app.tools.factory.new_song(dictionary=song_data)
        self.app.deck.cued = song_obj


class FilesTab(tk.Frame):
    """Frame for the file browser."""

    def __init__(self, parent):
        tk.Frame.__init__(self, parent)

        self.app = parent.app
        self.suite = parent.suite

        # vars for file loading
        self.directory = self.app.settings.paths.texts.get()
        self.filename = ""
        self.files = []

        # tk widgets
        self.scrollbar = tk.Scrollbar(self, orient="vertical")
        self.scrollbar.pack(side="right", fill="y")
        
        self.listbox = tk.Listbox(
            self,
            # font=self.app.settings.fonts.library,
            yscrollcommand=self.scrollbar.set,
            bg="lightgrey",
            fg="black",
            exportselection=False,
            # width=20,
            # height=11
        )
        self.listbox.pack(side="left", fill="both", expand=True, padx=5, pady=0)
        self.listbox.bind("<<ListboxSelect>>", self.files_listbox_on_select)
        self.listbox.bind("<Shift-Up>", lambda _: self.entry.focus_set)

        self.scrollbar.config(command=self.listbox.yview)

        # populate the listbox
        self.gen_file_list(self.directory)
        self.listbox_update(self.files)

    @property
    def path(self):
        return self.directory + "/" + self.filename

    def files_listbox_on_select(self, event):
        """When you select a file from the file listbox, push selection to preview."""
        if event.widget.curselection():
            # TODO: untangle
            self.filename = event.widget.get(event.widget.curselection())
            self.app.tools.loader.cue_from_file()

    def listbox_update(self, data):
        self.listbox.delete(0, "end")
        data = sorted(data, key=str.lower)
        for item in data:
            self.listbox.insert("end", item)

    def gen_file_list(self, target):
        """Generate file list from the target directory."""
        if target:
            self.directory = target
            # filter out directories and anything not beginning with an accepted file extension
            valid_ext = ('.rtf', '.txt') # TODO: move to settings
            self.files = [f for f in listdir(target) if isfile(join(target, f)) and f.endswith(valid_ext)]
            # self.files = list(filter(f for f in listdir(target))
            self.listbox_update(self.files)
        else:
            logging.warning(f"gen_file_list in browser recieved no target: target = '{target}'")

    def search_trace(self, query):
        # TODO: listbox update to decorator
        query = scrub_text(query)
        data = self.files if not query else self.get_search_result(query)
        self.listbox_update(data)

    def get_search_result(self, query):
        data = []
        for item in self.files:
            data.append(item) if query in scrub_text(item) else None
        return data

    def import_to_song(self, filename):
        """Import a text file and convert it into a song object."""
        # TODO: replace self.app.cue_from_file with this
        pass


class QuickSearchHeader(tk.Frame):
    """Class for the quick search bar header."""

    def __init__(self, parent, *args, **kwargs):
        tk.Frame.__init__(self, parent)
        self.suite = parent.suite

        self.label = tk.Label(self, text="Quick Search")
        self.label.pack(side="left", fill="y", anchor="w")

        entry = kwargs.get('entry')
        self.clear = tk.Button(self, text="Clear", command=lambda: entry.delete(0, 'end'))
        self.clear.pack(side="right", fill="y", anchor="e")





