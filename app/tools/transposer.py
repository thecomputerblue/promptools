# contains components for assigning word types transposing the song

import regex as re
import os
import logging

import common.res as res
import common.ids as ids

# helper functions
# TODO: many of the Transposer class functions could go here,
# as they don't directly concern the inner workings of the transposer.

def assign(part):
    """Instead of returning 'None' return ''."""
    return part if part else ""    

def str_represents_int(s) -> bool:
    """Return True if s represents an int,
    including strings beginning with '+' or '-'."""

    if not s:
        return False

    return s[1:].isdigit() if s[0] in "-+" else s.isdigit()

def recursive_qual_checker(quals):
    """Used to confirm qualities are valid.
    Only pass the qualities part of a chord regex match."""

    # base case. if nothing remains, qualities were valid.
    if not quals:
        return True

    # check that quals begin with valid quality, drop, check again.
    for q in ids.qualities:
        if quals.startswith(q):
            return recursive_qual_checker(quals.split(q)[-1])

    return False


class Transposer:
    """Process song objects into different transpositions, or convert to Nashville Numbers."""

    def __init__(self, parent):
        self.app = parent.app
        self.settings = parent.app.settings.transposer

    def transpose_tk(self, song, target): 
        """Transpose a tk tuple list."""

        # if transposition isn't enabled, return.
        if not self.settings.enabled.get():
            return

        transposition = self.convert_transposition_to_int_tk(song=song, target=target)
        if transposition == 0:
            return

        logging.info(f'transposing {song.name}')

        parts = song.tk_tuples
        updated = []

        strategies = {
        'key': self.transpose_key_tk,
        'chord': self.transpose_chord_tk,
        'slashchord': self.transpose_slashchord_tk,
        }

        for i, tup in enumerate(parts):
            pos, tag, word = tup

            # transpose transposible words with appropriate strategy
            for k, v in strategies.items():
                if tag == k:
                    word = v(word=word, song=song, transposition=transposition)
                    break

            # modified entry back into updated.
            updated.append((pos, tag, word))

        # dump updated tuples back to song obj
        song.tk_tuples = updated

    def transpose_key_tk(self, word, song, transposition):
        """Transpose key, updating songs current key to ensure correct accidentals."""

        lbr, note, minor, rbr = self.slice_key(word)
        flats = ids.FLAT_MIN_IDS if minor else ids.FLAT_MAJ_IDS

        old_id = ids.NOTE_IDS.get(note)
        new_id = (old_id + transposition) % 12
        acc = -1 if new_id in flats else 0
        note = ids.NOTE_ID_ACCIDENTALS[new_id][acc]

        song.key.current = note + minor

        return lbr + song.key.current + rbr

    def transpose_chord_tk(self, word, song, transposition):
        """Transpose chord."""

        old_note, qualities = self.slice_chord(word)
        note_id = ids.NOTE_IDS.get(old_note)
        new_id = (note_id + transposition) % 12
        new_note = ids.NOTE_ID_ACCIDENTALS[new_id][song.key.current_acc]

        return new_note + qualities

    def transpose_slashchord_tk(self, word, song, transposition):
        """Transpose slash chord."""

        logging.info(f'transpose_slashchord_tk recieved "{word}"')

        old_note, qualities, slash, bass = self.slice_slash_chord(word)

        new_top = self.transpose_chord_tk(
            word=old_note+qualities,
            song=song,
            transposition=transposition
            )

        new_bass = self.transpose_chord_tk(
            word=bass,
            song=song,
            transposition=transposition
            )

        return new_top + slash + new_bass

    def slice_key(self, word):
        """Slice a key, return [bracket, note, mode, bracket]"""

        lb, chd, rb = word[0], word[1:-1], word[-1]
        key, mode = [chd[:-1], chd[-1]] if chd[-1] in '-m' else [chd, '']

        return [lb, key, mode, rb]

    def slice_chord(self, chd):
        """Slice a chord, return [note, qualities]."""
        l = len(chd)

        strategies = {
        l == 1: lambda: [chd, ''],
        l == 2: lambda: [chd, ''] if chd[1] in 'b#' else [chd[:-1], chd[-1]],
        l >= 3: lambda: [chd[:2], chd[2:]] if chd[1] in 'b#' else [chd[:1], chd[1:]],
        }

        for k, v in strategies.items():
            if k:
                return v()

        logging.warning(f'slice_chord in transposer failed to return a value from "{chd}"')

    def slice_slash_chord(self, chord):
        """Slice slash chord and return [note, qualities, slash, bass]"""

        logging.info(f'slice_slash_chord recieved chord: {chord}')
        top, bass = chord.split('/')
        slices = self.slice_chord(top)

        return [slices[0], slices[1], '/', bass]

    def convert_transposition_to_int_tk(self, song, target):
        """Convert key note to integer transposition."""

        match = re.match(res.id_transposible, target)
        note = match[3] if match else None

        strategies = [
        (isinstance(target, int),       lambda: (target + song.key.default_id - song.key.initial_id) % 12),
        (str_represents_int(target),    lambda: (int(target) + song.key.default_id - song.key.initial_id) % 12),
        (not self.match_chord(match),   lambda: (song.key.default_id - song.key.initial_id) % 12),
        (song.key.initial != None,      lambda: (ids.NOTE_IDS.get(note) - song.key.initial_id) % 12),
        (song.key.initial == None,      lambda: (ids.NOTE_IDS.get(note) - song.key.default_id) % 12),
        ]

        for s in strategies:
            if s[0]:
                return s[1]()

    def match_chord(self, match=re.regex.Match) -> bool:
        """Evaluate transposible_ids regex match for chordiness."""

        if not match:
            return False

        if match[3]:
            quals = assign(match[4])
            return recursive_qual_checker(quals)

        return False

    def show_colors_tk(self, frame, song):
        """Show colors from the tk formatted rep."""

        def style_strat():
            """Strategy for managing style tags in tk text."""
            # TODO: untested!

            add_tag() if tag == 'tagon' else None
            pop_tag() if tag == 'tagoff' else None

        def add_tag():
            """Add tag to list of active."""

            nonlocal active_styles

            style = word
            active_styles.append((pos, style))
            logging.info(f'added tag {style} to active')

        def pop_tag():
            """Apply tag to text range and remove from active."""

            nonlocal active_styles
            nonlocal frame

            style = word

            for i, tup in enumerate(active_styles):
                if tup[1] == style:

                    # apply the style tag then pop from active
                    start = tup[0]
                    frame.text.tag_add(style, start, pos)
                    active_styles.pop(i)
                    logging.info(f'popped tag {style} from active')
                    break

        def chord_strat():
            """Strategy for transposing chords."""

            nonlocal key_id 
            nonlocal minor 
            nonlocal word

            note, qualities = self.slice_chord(word)
            note_id = ids.NOTE_IDS.get(note)

            nash_list = ids.NASH_MIN_FLATS if minor else ids.NASH_MAJ_FLATS
            nash_index = (note_id - key_id) % 12
            nash_note = nash_list[nash_index]

            # TODO: convert qualities to nashville representations

            # update word
            word = nash_note + qualities

        def slashchord_strat():
            """Strategy for transposing slash chords."""

            nonlocal key_id 
            nonlocal minor 
            nonlocal word

            logging.info(f'slashchord_strat recieved chord: {chord}')

            note, qualities, slash, bass = self.slice_slash_chord(chord)
            top = self.nash_chord(chord=chord, key_id=key_id, minor=minor)
            bass = self.nash_chord(chord=bass, key_id=key_id, minor=minor)

            word = top + slash + bass

        def key_strat():
            """Strategy for calculating key_id."""

            nonlocal key_id 
            nonlocal minor 
            nonlocal word

            _, note, minor, _ = self.slice_key(word)
            key_id = ids.NOTE_IDS.get(note)

        def ws_strat():
            """Compensate for whitespace offset due to chord length change."""

            nonlocal word
            nonlocal pos 
            nonlocal end

            ws_len = len(word)
            column = int(end.split('.')[1])
            expected = int(pos.split('.')[1])

            offset = expected - column
            new_len = ws_len + offset

            # recalculate whitespace size, always a minimum one space
            word = ' ' * new_len if new_len >= 1 else ' '


        # TODO: messy
        tups = song.tk_tuples
        key_id = song.key.initial_id
        minor = ''
        nashville = self.settings.nashville.get()
        end = frame.text.index('end-1c')

        active_styles = []

        # choose what to do based on tuple contents
        strategies = {
        lambda: tag == 'tagon' or tag == 'tagoff': lambda: style_strat(),
        lambda: tag == 'chord' and nashville: lambda: chord_strat(),
        lambda: tag == 'slashchord' and nashville: lambda: slashchord_strat(),
        lambda: tag == 'key' and nashville: lambda: key_strat(),
        lambda: tag == 'ws' and i > 0 and tups[i-1] != 'nl': lambda: ws_strat(),
        }

        #iterate over the list of tuples, dumping to tktext and managing various tags
        for i, tup in enumerate(tups):
            pos, tag, word = tup

            for k,v in strategies.items():
                v() if k() else None

            # add anything that's not a style tag and update end marker
            if tag not in ('tagon', 'tagoff'):
                frame.text.insert('end', word, tag)
            end = frame.text.index('end-1c')

