# rewriting the song object here and its factory here. not yet implemented.

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
from tools.api import PrompToolsAPI

# redoing much of the song construction with the new style of song object
# which will offer more flexibility and is far less bloated.


# Helper functions
def assign(part):
    """Instead of returning 'None' return ''."""
    return part if part else ""

def timestamp():
    """Create a timestamp of the current time."""
    return time.strftime("%Y-%m-%d %H:%M:%S", time.gmtime())


class SongFactory(PrompToolsAPI):
    """New song factory class for producing / modifying SongNew objects."""

    def __init__(self, app):
        PrompToolsAPI.__init__(self, app)

        # strategies for constructing songs from different sources.
        self.import_strategies = {
            lambda **kwargs: 'file' in kwargs: lambda song, **kwargs: 
            self.import_file(kwargs.get('file')),

            lambda **kwargs: 'string' in kwargs: lambda song, **kwargs: 
            self.import_string(kwargs.get('string')),

            # dump from a tk.Text widget
            lambda **kwargs: 'tkText' in kwargs: lambda song, **kwargs:
            self.import_tkText(kwargs.get('tkText')),

            # promptools formatted script
            lambda **kwargs: 'script' in kwargs: lambda song, **kwargs:
            self.import_pt_script(kwargs.get('script')),

            # pre-constructed dictionary of song data.
            lambda **kwargs: 'data' in kwargs: lambda song, **kwargs:
            self.import_data(kwargs.get('data'))
            }

        # strategies for returning an appropriate name. pass song data dict
        # if all these fail, assign "Untitled"
        self.naming_strategies = (
            (lambda data: 'name' in data, 
                lambda **kwargs: data.get('name')),

            (lambda data: 'file' in data,
                lambda data: data.get('file').rsplit("/", 1)[-1].rsplit(".", 1)[0]),

            (lambda data: 'string' in data,
                lambda data: data.get('string').split("\n", 1)[0][:20]),)
 
    def new_song(self, **kwargs):
        """Return a SongNew object from input kwargs."""

        for k,v in self.import_strategies.items():
            if k(kwargs):
                return v(kwargs)

        raise Exception('SongFactory failed to import from kwargs')

    def import_file(self, path: str):
        """Import from a file path."""

        data = {}
        data['path'] = path
        data['string'] = self.strip_formatting_strategies(path)
        data = self.strip_metadata_from_string(data)
        data['script'] = self.generate_script_strategies(data)

    def generate_script_strategies(self, data):
        """Return a formatted song script depending on extant song dictionary
        and program settings."""

        # TODO: account for different import overrides (ie. disabled auto-tag).
        return self.autotag(data.get("string"))


    def strip_metadata_from_string(self, data):
        """Strip any metadata from the song string and store it separately."""

        strategies = {
        "comments" not in data: self.strip_comments,
        "confidence" not in data: self.strip_confidence
        }

        for k, v in strategies:
            if k:
                data = v(data)

        return data

    def strip_confidence(self, data):
        """Strip the confidence asterisks from the beginning of the song."""

        string = data.get("string")

        # no asterisks, full confidence (10)!
        if not string.startswith('*'):
            return string, 10

        worry = 0

        while string.startswith('*'):
            string = string[1:]
            worry += 1

        data["string"] = string 
        data["confidence"] = 10 - worry

        return data


    def strip_comments(self, data):
        """Strip comments from the end of the document."""

        if "comments" in data:
            return data

        string = data.get("string")
        comments = None

        delim = "---"
        if delim in string:
            string, comments  = string.rsplit(delim, 1)
            string = self.cleanup_song_string(string)

        data["string"] = string 
        data["comments"] = comments

        return data

    def cleanup_song_string(self, string):
        """Strip extra --- from endnotes."""

        while string.endswith("-") and len(string) > 1:
            string = string[:-1]

        return string

    def strip_formatting_strategies(self, path):
        """Return a string of the document, stripping any formatting."""

        strategies = {
            lambda: path.endswith('.rtf'): lambda: self.strip_rtf(path)
            lambda: path.endswith('.txt'): lambda: self.read_file(path)
            }

        for k, v in strategies.items():
            if k():
                return v()

        raise Exception("strip_formatting_strategies in SongFactory recieved an invalid file extension")

    def strip_rtf(self, path):
        """First get raw string, then strip rtf formatting."""

        raw = self.read_file(path)

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


    def import_string(self, string: str):
        """Import from a string."""

    def import_tkText(self, tkText: tuple):
        """Import from a tk.Text dump."""

    def import_script(self, script: list):
        """Import from a promptools formatted script (list of tuples)."""

    def import_data(self, data: dict):
        """Import a pre-constructed dictionary of song data."""

        return SongNew(data=data)

    def init_song_data(self):
        """Generate the most basic song data dict."""

        data = {}
        data['created'] = timestamp()

        return data

    def read_file(self, file) -> str:
        """Dump the contents of the file to be read, or an empty string if an
        invalid path is attempted."""

        # TODO: not very robust...
        if not self.valid_file_ext(file):
            raise Exception("Invalid file extension.")
            return

        contents = ""

        try:
            with open(file, "r", encoding="utf-8") as f:
                contents = f.read()
        except IsADirectoryError:
            logging.warning(f'tried to load a directory, whoops.')
        finally:
            return contents

    def validate_file_ext(self, file):
        """Return True for valid file formats."""

        valid_ext = self.app.settings.importer.valid_ext
        return file.endswith(valid_ext)


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

