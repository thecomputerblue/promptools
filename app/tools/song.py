import regex as re
import os
from dataclasses import dataclass
import time
import logging
import striprtf.striprtf as striprtf

# TODO: better import hierarchy...
# from .res import id_slices, res.id_transposible
import common.res as res
import common.ids as ids
import tools.words as words
from tools.words import WordFactory

from common.settings import Settings


# Helper functions
def assign(part):
    """Instead of returning 'None' return ''."""
    return part if part else ""

def timestamp():
    """Create a timestamp of the current time."""
    return time.strftime("%Y-%m-%d %H:%M:%S", time.gmtime())


class SongFactory:
    """Class that constructs song objects. """

    def __init__(self, app=None):
        self.app = app
        self.tagger = WordFactory()
        self.rtf_importer = RtfImporter()

        # strategies for importing song text from different sources
        self.text_strategies = {
        lambda **kwargs: 'file' in kwargs: lambda song, **kwargs: 
        self.ingest_file_new(song, kwargs.get('file')),

        lambda **kwargs: 'string' in kwargs: lambda song, **kwargs: 
        self.ingest_string_new(song, kwargs.get('string')),

        lambda **kwargs: 'tk_text_dump' in kwargs: lambda song, **kwargs:
        self.ingest_tk_text_dump_new(song, kwargs.get('tk_text_dump')),

        lambda **kwargs: 'formatted_tuples' in kwargs: lambda song, **kwargs:
        self.ingest_formatted_tuples_new(song, kwargs.get('formatted_tuples')),

        lambda **kwargs: 'dictionary' in kwargs: lambda song, **kwargs:
        self.ingest_song_dictionary(song, kwargs.get('dictionary'))
        }

        # TODO: probabl a less cluttered way to convey this
        self.naming_strategies = (
        (lambda song, string, name: name, 
            lambda song, string, name: name),

        (lambda song, string, name: song.file,
            lambda song, string, name: song.file.rsplit("/", 1)[-1].rsplit(".", 1)[0]),

        (lambda song, string, name : string,
            lambda song, string, name: string.split("\n", 1)[0][:20],

        (lambda song, string, name : not name and not file and not string,
            lambda **kwargs: "Untitled")),
        )

    def make_many_songs(self, songs: list) -> list:
        """Convert list of song dicts into list of song objects."""
        objs = []
        for d in songs:
            objs.append(self.new_song(dictionary=d))
        return objs

    def new_song(self, meta=None, **kwargs):
        """Create a new song object from valid text source
        (text/rtf file, string, tkinter textbox, or database).
        Optionally apply pre-built metadata."""

        # apply metadata if it exists
        song = Song(self.app, meta) if meta else Song(self.app)

        return self.import_text(song, **kwargs) if kwargs else song

    def update_song(self, old, meta=None, **kwargs):
        """Update an existing song object."""
        
        # apply metadata if it exists
        old.meta = meta(old) if meta else old.meta

        # update modified stamp on save.
        # TODO: update 'opened' stamp on push to live.
        old.meta.modified = timestamp()

        return self.import_text(old, **kwargs) 

    def import_text(self, song, **kwargs):
        """Import text with appropriate strategy, return song."""

        # ingest text source, will also generate metadata when appropriate
        for k, v in self.text_strategies.items():
            if k(**kwargs):
                return v(song, **kwargs)

        logging.warning('import_text in song failed to choose import strategy. generating empty song')


    def new_meta(self, name=None, created=None, modified=None, info=None, confidence=None, opened=None):
        """Construct a new song metadata object."""

        # make a metadata object with no song
        meta = SongMetadata(song=None)

        # assign various metadata args
        meta.name = name if name else ''
        meta.created = created 
        meta.modified = modified
        meta.opened = opened
        meta.info = info # TODO: deprecate plz, change to comments
        meta.comments = info
        meta.confidence = confidence

        return meta

    def ingest_file_new(self, song, file):
        """Create song object from a file."""
        logging.info('song factory ingested file')

        # return empty song if bad file ext
        if not self.valid_file_ext(file):
            return self.empty_song(song)

        # get raw string
        raw = self.read_file(file)

        # strip rtf formatting if necessary to get the usable string
        string = self.rtf_importer.strip(raw, file) if file.endswith(".rtf") else raw

        # TODO: decide if you actually need to save these with song meta
        # TODO: the remainder of this is meta assignment. break off?
        song.meta.file = file
        song.meta.raw = raw
        song.meta.string = string

        song = self.ingest_string_new(song, string)
        song = self.name_song(song, string)

        return song

    def ingest_song_dictionary(self, song, dictionary):
        """Ingest from a dictionary."""

        d = dictionary

        song.meta.name = d.get('title')
        song.song_id = d.get('song_id')
        song.library_id = d.get('library_id')
        song.meta.created = d.get('created')
        song.meta.modified = d.get('modified')
        song.meta.confidence = d.get('confidence')
        song.meta.info = d.get('comments')
        song.key.default = d.get('key')
        song.tk_tuples = d.get('tk_tuples')

        return song

    def name_song(self, song, string, name=None):
        """Try to name song from available info."""

        # if already named, don't bother
        if song.name:
            return song

        for s in self.naming_strategies:
            if s[0](song, string, name):
                song.meta.name = s[1](song, string, name)
                # logging.info(f'named a song {song.name}')
                break

        return song

    def empty_song(self, song):
        """If you try to ingest a bad file, and the song doesn't
        have any tuples, create a dummy song."""
        
        # TODO: rethink this...
        if not song.tk_tuples:
            logging.warning('Bad file ext, returning empty song.')
            song.tk_tuples = [('1.0', 'text', '')]

        return song

    def ingest_string_new(self, song, string):
        """Ingest text from a string."""

        # logging.info('processing text string into song')
        song, string = self.strip_meta_from_string(song, string)
        slices = re.split(res.id_slices, string)

        # throw away empty slices TODO: regex should do this...
        filtered = list(filter(('').__ne__, slices))


        # return song with tagged tuples
        return self.tagger.auto_tag(song=song, slices=filtered)

    def strip_meta_from_string(self, song, string):
        """Strip metadata from string and apply to song."""

        if song.meta.info is None: 
            string, song.meta.info = self.strip_end_notes_new(song, string)

        if song.meta.confidence is None:
            string, song.meta.confidence = self.strip_confidence_asterisks_new(string)

        return song, string

    def ingest_tk_text_dump_new(self, song, tk_text_dump):
        """Ingest from a text dump from a tktext widget. They dump a slightly
        different format from what Song stores so some prep is needed."""

        def tagon_flag():
            """Update tag if word is a promptools tag type.
            Append a flag if it is a style."""
            nonlocal tag
            tag = word if word in types else tag
            song.tk_tuples.append((pos, flag, word)) if word in styles else None

        def text_flag():
            """If text, append with current tag"""
            song.tk_tuples.append((pos, tag, word))

        # TODO: need to handle tagoffs and unknowns for styling
        def tagoff_flag():
            pass

        def unknown_warning():
            pass

        # use these to determine how to ingest each tuple
        styles = self.app.settings.tags.styles
        types = self.app.settings.tags.types

        song.tk_tuples = []
        tag = None

        # TODO: tagoff, unknown warning
        strategies = {
        lambda flag: flag == 'tagon': tagon_flag,
        lambda flag: flag == 'text': text_flag,
        }

        for tup in tk_text_dump:

            flag, word, pos = tup

            for k, v in strategies.items():
                v() if k(flag) else None

        return song

    def ingest_formatted_tuples_new(self, song, formatted_tuples):
        """Ingest tuples already correctly formatted for Song use."""
    
        logging.info('ingested formatted tuples')
        song.tk_tuples = formatted_tuples

        return song

    def strip_end_notes_new(self, song, string):
        """Strip info from end of string."""

        # if info already exists, 
        if song.meta.info:
            return string, song.meta.info

        delim = "---"
        info = ''

        if "---" in string:
            string, info = string.rsplit(delim, 1)
            string = self.cleanup_end_new(string)

        return string, info

    def cleanup_end_new(self, string):
        """Strip extra --- from endnotes."""
        while string.endswith("-") and len(string) > 1:
            string = string[:-1]

        return string

    def strip_confidence_asterisks_new(self, string):
        """Strip the confidence asterisks I put at top of files."""

        # no asterisks, full confidence (10)!
        if not string.startswith('*'):
            return string, 10

        worry = 0

        while string.startswith('*'):
            string = string[1:]
            worry += 1

        return string, 10 - worry

    def valid_file_ext(self, file):
        """Return True for valid file formats."""

        valid_ext = self.app.settings.importer.valid_ext
        return file.endswith(valid_ext)

    def read_file(self, file) -> str:
        """Dump the contents of the file to be read, or an empty string if an
        invalid path is attempted."""

        # TODO: not very robust...
        if not self.valid_file_ext(file):
            logging.warning(f'tried to read invalid file: {file}\n')
            return

        contents = ""

        try:
            with open(file, "r", encoding="utf-8") as f:
                contents = f.read()
        except IsADirectoryError:
            logging.warning(f'tried to load a directory, whoops.')
        finally:
            return contents


class RtfImporter:
    """Import and convert RTF files to plain string, handling errors."""

    def strip(self, raw: str, file: str):
        """Strip rtf formatting from raw rtf string."""
        try:
            stripped = striprtf.rtf_to_text(raw)
        except UnicodeEncodeError:
            # Flag this in case you have to deal with it later on.
            print(
                f"Unicode encode error in file '{file}'."
                + "\nStripping header. Expect issues."
            )
            # drop header and sub bad unicode
            stripped = self.drop_rtf_header(raw)
            stripped = self.sub_unicode_errors(stripped)
            # Try again. Haven't run into additional errors after this, but...
            try:
                stripped = striprtf.rtf_to_text(stripped)
            except UnicodeDecodeError:
                print('SECOND unicode error, yikes. passing the raw file back, which will probably look bad.')
                stripped = raw

        return stripped

    @staticmethod
    def drop_rtf_header(contents):
        """Drops header of erroneous rtf file. Used in response to exception
        UnicodeEncodeError when running rtf_to_text."""
        contents = contents.split("\\cf0 ", maxsplit=1)[-1]
        return contents

    @staticmethod
    def sub_unicode_errors(contents):
        """Fix some specific unicode errors that occur after dropping header.
        Not comprehensive, but clean up almost all the problematic files
        in the song library. Will remove this when I get around to batch
        processing the song library into plain text files."""

        # TODO: hacky
        contents = contents.replace("\\u8232", "\\\n")
        contents = contents.replace("\\uc0", "")
        # Solve most issues in 'I Don't Want To Go Home'
        contents = contents.replace("\\'91", "")
        contents = contents.replace("\\'92", "'")

        return contents


class Song:
    """Container for song properties. Pack word list, etc. into this with song factory."""

    def __init__(self, app, meta=None):
        """Init variables that will be filled in by song factory."""

        # apply metadata if it exists, or init
        self.meta = meta(self) if meta else SongMetadata(self)

        # tuple format (pos, tag, word) where tag/word can sometimes be flag/action
        # TODO: dislike this attribute name >:(
        self.tk_tuples = []

        # track song key
        self.key = Key(self)

        # add reference to cache 
        app.cache.add_song(self)

    @property
    def name(self):
        """Expose the name more shallowly."""
        return self.meta.name

    @name.setter
    def name(self, new):
        self.meta.name = new

    @property
    def created(self):
        return self.meta.created

    @property
    def modified(self):
        return self.meta.modified

    @property
    def confidence(self):
        return self.meta.confidence
    
    @property
    def info(self):
        return self.strip_info(self.meta.info)

    @info.setter 
    def info(self, new):
        self.meta.info = new

    @property
    def library_id(self):
        return self.meta.library_id

    @library_id.setter 
    def library_id(self, new):
        self.meta.library_id = new

    def strip_info(self, info):
        """Strip doesn't remove leading / trailing newlines for some reason..."""

        if info is None:
            return ''

        while info.startswith('\n') and len(info)>1:
            info = info[1:]
        return info

    @property
    def line_ct(self):
        # TODO: + 1 avoids... i started to type something here. not sure what
        return self.words[-1].line + 1

    @property
    def lines(self):
        """Return words sorted into lines."""

        # TODO: not used anywhere, will replace.
        # TODO: only refresh when changed.
        # TODO: lots of work happening for a property, bad
        tups = self.tk_tuples
        line_ct = int(tups[-1][0].split('.')[0])
        # list of lists
        lol = []
        # populate lol
        for i in range(line_ct):
            lol.append([])

        for i, tup in enumerate(tups):
            word = tup[2]
            # ignore empty strings
            if word:
                line = int(tup[0].split('.')[0]) - 1
                lol[line].append(word)

        return lol

    @property
    def file(self):
        return self.meta.file

    @property
    def opened(self):
        return self.meta.opened

    def transpose(self, transposer, target):
        """Circuitous method to call tranposer on the song."""
        transposer.transpose(song=self, target=target)

    def print_tk(self):
        """Raw print tk_tuples to terminal, no whitespace management."""
        output = ''
        tup = self.tk_tuples
        for i in range(len(tup)):
            output += tup[i][2]
        print(output)


# TODO: dataclass?
class SongMetadata():
    """Class for song metadata (info, properties in setlist, etc.)"""
    def __init__(self, song=None):
        self.song = song
        self.file = None

        self.created = timestamp()
        self.modified = self.created
        self.opened = self.created

        self.name = ''
        self.title = self.name # TODO: migrate references to title
        self._info = None # TODO: migrate references to comments
        self.confidence = None

        # following params track db references
        # song_id points to the song in the appdata database.
        # library_id points to the "definitive" version of the song that is
        # stored in the library. if song_id != None and song_id == library_id,
        # this is the definitive version. otherwise it is considered an alt.
        self.song_id = None
        self.library_id = None

    @property
    def title(self):
        return self.name

    @title.setter
    def title(self, new):
        self.name = new
    
    @property
    def key(self):
        # TODO: allow user to transpose song by changing key here? setter method
        return self.song.key.default

    @property
    def info(self):
        return self._info

    @info.setter 
    def info(self, info):
        self._info = info.strip() if info else ''

    @property
    def comments(self):
        return self._info
    
# TODO: dataclass?
class Key():
    """Class for song key properties."""

    def __init__(self, song):
        self.song = song
        self.default = None
        self.current = None

    @property
    def initial(self):
        """Find first key in song tuples."""
        for tup in self.song.tk_tuples:
            if tup[1] == 'key':
                return tup[2]
        return None

    @property
    def initial_id(self):
        return self.key_to_id(self.initial)

    @property
    def default_id(self):
        return self.key_to_id(self.default)

    @ property
    def current(self):
        return self._current if self._current else self.default

    @current.setter
    def current(self, new):
        self._current = new
    
    @property
    def current_id(self):
        return self.key_to_id(self.current)

    @property
    def current_acc(self):
        return self.key_to_acc(self.current)
    
    # TODO: redundant work between these three fns
    def split_key(self, key):

        key = key[1:] if key.startswith('(') else key
        key = key[:-1] if key.endswith(')') else key

        return (key[:-1], key[-1]) if key[-1] in '-m' else (key, '')

    def key_to_id(self, key):
        """Convert key to note_id"""

        if key is None:
            return None

        note, minor = self.split_key(key)

        return ids.NOTE_IDS.get(note)

    def key_to_acc(self, key):
        """Get correct accidental index for a target key."""

        # default to sharp
        if key is None:
            return 0

        note, minor = self.split_key(key)
        note_id = self.key_to_id(note)
        acc_ids = ids.FLAT_MIN_IDS if minor else ids.FLAT_MAJ_IDS
        
        return -1 if note_id in acc_ids else 0

class SongNew:
    """Redesigning the song structure around a dictionary, and properties
    which access the dictionary."""

    # TODO: implement

    def __init__(self, data: dict):
        self.data = data if data else {}

    @property
    def title(self):
        return self.data.get('title')

    @property
    def artist(self):
        return self.data.get('artist')

    @property
    def key(self):
        """Gets the key object from the dict. Key object contains methods to
        calculate key_id for transposition, and key representations. To get
        current key call key.current, to get default call key.default"""
        return self.data.get('key')
    
    @property
    def lyrics(self): 
        # TODO: filter script to get lyrics only as a string
        return

    @property
    def script(self):
        return self.data.get('script')


"""
SONG DICTIONARY OUTLINE
here's everything that might be storstored in the dict.

title: the title of the song
artist: the original artist of the song

client: the client who will be performing this song

key: default key of the song. when you reset transposition, it will compare
    this value to the first found key element to choose the transposition
    depth.

tempo: song tempo
genre: song genre

created: created timestamp
modified: modified timestamp
opened: opened timestamp

script: (replaces tk_tuples) list of tuples representing the song document
    with all format & id tags

"""    


    
