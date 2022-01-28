# components of the quick browser go here.

import string
import tkinter as tk
from tkinter import ttk
import pickle
import logging

from os import listdir
from os.path import isfile, join, exists


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

        self.entry.bind("<Down>", self.focus_set_listbox_from_entry)

    def focus_set_listbox_from_entry(self, event):
        """When you press the down arrown in search field,
        move focus to the search field."""

        l = self.tabs.files.listbox

        # Move focus to listbox.
        l.focus_set()
        # Immediately focus the first list item.
        # TODO: if list item was previously selected, focus to that. Basically
        # change (0) to whatever the widget variable is for focused item.
        if not l.curselection():
            l.select_set(0)
            self.filename = l.get(0)
            #TODO: what is this line doing
            self.app.cued.selected.set(self.truncate_label(self.filename))
            # Refresh song with new info. TODO: repeated code!!!
            self.parent.cue_from_file()


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

        self.tree = ScrolledTreeview(self)
        self.tree.pack(fill='both', expand=True)

    def search_trace(self, query):
        """Filter library tree by search contents."""
        # TODO
        pass


class ScrolledTreeview(tk.Frame):
    """Attach a scrollbar to treeview."""

    def __init__(self, parent):
        tk.Frame.__init__(self, parent)

        self.app = parent.app

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

        # populate the treeview with library songs
        # TODO: filter to only show library versions

        self.gen_library()

    def gen_library(self, data=None):
        """Generate the library song list."""

        # get song metadata
        # TODO: ONLY get library versions
        if data is None:
            data = self.app.tools.dbmanager.get_all_song_meta_from_db(option='library')

        # filter non-library versions


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

    def on_tree_select(self, event):
        """Make a song obj from library selection and push to cued."""

        sel = self.tree.focus()
        song_id = self.tree.set(sel, column="song_id")
        song_data = self.app.tools.dbmanager.get_song_dict_from_db(song_id=song_id)
        song_obj = self.app.tools.factory.new_song(dictionary=song_data)
        self.app.deck.cued = song_obj

    def treeview_sort(self):
        """Sort the treeview alphabetically."""
        logging.info('treeview_sort in ScrolledTreeview')
        reverse = False
        t = self.tree

        l = [(t.item(k)["text"], k) for k in t.get_children()]
        print(l)
        l.sort(key=lambda t: t[1], reverse=reverse)

        for index, (val, k) in enumerate(l):
            t.move(k, '', index)

        # t.heading(col, command=lambda: treeview_sort_column())




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

        # do nothing if you click out of list
        current = event.widget.curselection()
        if current:
            # TODO: untangle
            self.filename = event.widget.get(event.widget.curselection())
            self.app.tools.loader.cue_from_file()

    def listbox_update(self, data):

        l = self.listbox

        # clear old
        l.delete(0, "end")
        data = sorted(data, key=str.lower)

        # insert sorted
        for item in data:
            l.insert("end", item)

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
        # get text from entry and strip capitalization, punctuation

        # scrub query
        query = query.strip().lower()
        query = self.strip_punctuation(query)

        # get data from file_list
        if not query:
            data = self.files
        else:
            data = []
            # TODO: needs to ignore punctuation when filtering
            for item in self.files:
                data.append(item) if query in self.strip_punctuation(item.lower()) else None

        self.listbox_update(data)

    def strip_punctuation(self, entry):
        """Strip punctuation from strings for search."""
        return entry.translate(str.maketrans('', '', string.punctuation))


    # def listbox_on_select(self, event):

    #     # do nothing if you click out of list
    #     current = event.widget.curselection()
    #     if current:
    #         # TODO: untangle
    #         self.filename = event.widget.get(event.widget.curselection())
    #         self.app.tools.loader.cue_from_file()



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


# TODO: old stuff below, confirm you don't want
# to reuse any of this code and delete.

# class FileSearch(tk.Frame):
#     """Class for the file search and its label."""

#     def __init__(self, parent, *args, **kwargs):
#         tk.Frame.__init__(self, parent)

#         # orient
#         self.parent = parent
#         self.app = parent.app
#         self.suite = parent.suite
#         self.settings = parent.settings

#         # TODO: spaghetti

#         # search query var
#         self.query = tk.StringVar()
#         self.query.trace("w", lambda *args: parent.search_trace())

#         self.entry = tk.Entry(self, textvariable=self.query)
#         self.entry.bind("<Down>", parent.focus_set_listbox_from_entry)

#         self.header = QuickSearchHeader(self)
#         self.header.pack(side="top", fill="x")

#         self.entry.pack(side="top", fill="x")

#         self.scrollbar = tk.Scrollbar(self, orient="vertical")
#         self.scrollbar.pack(side="right", fill="y")
        
#         self.listbox = tk.Listbox(
#             self,
#             # font=self.app.settings.fonts.library,
#             yscrollcommand=self.scrollbar.set,
#             bg="lightgrey",
#             fg="black",
#             exportselection=False,
#             width=30,
#             # height=11
#         )
#         self.listbox.pack(side="left", fill="both", expand=True, anchor='n', padx=5, pady=0)
#         self.listbox.bind("<<ListboxSelect>>", parent.listbox_on_select)
#         self.listbox.bind("<Shift-Up>", lambda _: self.entry.focus_set)

#         self.scrollbar.config(command=self.listbox.yview)


# class FileFolderSelector(tk.Frame):
#     """Select customsong library folder."""

#     # TODO: refactor into browser, probably.

#     def __init__(self, parent, *args, **kwargs):
#         tk.Frame.__init__(self, parent)

#         self.parent = parent
#         self.app = parent.app
#         self.suite = parent.suite

#         self.mainframe()

#     def mainframe(self):
#         self.make_vars()
#         self.make_widgets()
#         self.pack_widgets()

#     def make_vars(self):
#         """Make frame variables."""
#         # Initialize variables.
#         self.folder_path = self.app.settings.library_dir
#         self.display_folder = tk.StringVar()
#         self.display_folder.set("No folder specified. Using root.")

#     def make_widgets(self):
#         # Make button and label
#         self.folder_button = tk.Button(self, text="Custom Folder", command=self.click,)
#         self.folder_label = tk.Label(self, textvariable=self.display_folder)

#     def pack_widgets(self):
#         # Pack elements into local frame
#         self.folder_button.pack(side="left")
#         self.folder_label.pack(side="right")

#     def click(self) -> None:
#         """On click, open file browser."""
#         # Choose a target folder.
#         target = tk.filedialog.askdirectory(
#             initialdir=root_directory, title="Choose script library folder"
#         )

#         # Update path if valid path selected.
#         self.folder_path = self.update_path(self.folder_path, target)

#         # Forward path to file list
#         self.parent.browser.gen_file_list(self.folder_path)

#         # Generate label from new path
#         label = self.gen_folder_label(self.folder_path)

#         # Display folder name on label
#         self.display_folder.set(label)

#     def update_path(self, current, target):
#         return target if target else current

#     def gen_folder_label(self, target, maxlength=45):
#         """Generate truncated label text for folder button."""
#         if target == ".":
#             return "No folder specified. Using root."
#         if target:
#             # Truncate
#             if len(target) > maxlength - 3:  # -3 makes room for elipses...
#                 e = "..."
#                 t = -maxlength
#             else:
#                 e = ""
#                 t = -len(target)
#             return e + target[t:]
#         return "No folder specified. Using root."

# class FileBatchImporter:
#     """Towards containing the entire library within a file."""
#     def __init__(self, parent):
#         self.parent = parent
#         self.app = parent.app
#         self.suite = parent.suite

#         # Default library file
#         self.path = 'library.pickle'
#         self.load_previous_library()

#         # If no library file exists, import from the txt file directory
#         if not self.library:
#             self.import_all_from_folder(directory='lib')

#     def load_previous_library(self):
#         file_exists = exists(self.path)
#         if file_exists:
#             with open(self.path, 'rb') as lib:
#                 self.library = pickle.load(lib)
#                 self.list_library_songs()
#         else:
#             self.library = []

#     def list_library_songs(self):
#         for song in self.library:
#             print(song.name)

#     def import_all_from_folder(self, directory):
#         for filename in listdir(directory):
#             path = directory + '/' + filename
#             # song=Song(file=path, tagger=self.app.tagger, factory=self.app.factory)
#             song = self.app.song_factory.create_song(file=path)
#             self.library.append(song)

#     def print_library(self):
#         for song in self.library:
#             print(song.name)

#     def pickle_library(self):
#         """Dump library back to file."""
#         # TODO: can't pickle regex >:(
#         with open(self.path, 'wb') as lib:
#             pickle.dump(self.library, lib)






