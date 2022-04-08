"""Contains all the classes and subclasses for words in the song."""

# from abc import ABC
import regex as re
import logging

# tuples for chord id & transposition
import common.ids as ids
# regex objects for slicing, id
import common.res as res


# Helper functions
def assign(part):
    """Instead of returning 'None' return ''."""
    return part if part else ""


class CoordPointers:
    """Class that tracks x and y coordinates."""

    def __init__(self):
        self.x_pos = 0  # character 0
        self.y_pos = 1  # tkinter starts line at 1

    def update(self, string):
        """Update pointers based on string."""
        if string == "\n":
            self.x_pos = 0
            self.y_pos += 1
        else:
            self.x_pos += len(string)

    @property
    def pos(self):
        """Return a string concat that matches the tkinter pos format."""
        return str(self.y_pos) + "." + str(self.x_pos)

    # TODO: maybe return x and y pos as properties / strings,
    # but store under the hood as ints.


class WordFactory:
    """Class that takes a list of strings, identifies types
    and applies appropriate tags."""

    def __init__(self):
        """init any references that get used repeatedly"""

        # these tags are ignored for purposes of calculating most common word
        # type during ambiguous reassignment
        self.ignore = [
            "ws",
            "key",
            "bar",
            "nl",
            "chord",
        ]
        self.ambiguous = [
            "A",
            "Am",
            "I",
        ]
        # these tags as neighbors to Am / A generally mean Am / A is a chord
        self.chordy_neighbors = ("chord", "slashchord", 'slash', "bar")

        # strategies for different stages of ID

        # strategies for transposibles using regex
        self.match_strategies = {
            self.match_keychange: "key",
            self._match_slash_chord: "slashchord",
            self.match_chord_tk: "chord",
        }

        # strategies for non-transposibles
        self.word_strategies = {
            self.is_header: "header",
            self._match_whitespace: "ws",
            self._match_newline: "nl",
            self._match_barline: "bar",
            # self.flag_ambiguous: 'ambiguous'
        }

        # strategies should return appropriate tag if match, or None if not.
        # TODO: move outside function
        self.ambiguous_strategies = (
            self.ambiguous_a_am,
            self.ambiguous_digit,
            self.ambiguous_to_most,
        )

        # strategies for reassigning already assigned words.
        self.reassign_strategies = (
            self.reassign_header_precedence,
            self.reassign_most_precedence,
        )

    def auto_tag(self, song, slices):
        """Automatically identify and tag a list of words, returning a list of
        tuples in the format (pos, tag, word)."""

        # TODO: reorder tests based on relative frequency. i think the order should be
        # lyric, whitespace, chord, newline, header, etc.
        # TODO: allow multiple tags, then filter by priority. much later
        # can do something on line level.

        # pointers obj generates the pos for each tuple
        pointers = CoordPointers()
        output = []  # output may be longer than slices due to typo splits etc.
        line = []  # keep line as a unit to resolve ambiguities

        for i, word in enumerate(slices):
            match = re.match(res.id_transposible, word)
            typos = self.flag_typos(match)

            # logging.info(f'word: "{word}", match: "{match[0] if match != None else None}"')

            # tag strategies
            tag = "ambiguous" if self.flag_ambiguous(word) else None
            tag = (
                self.try_tag(match, self.match_strategies) if match and not tag else tag
            )
            tag = self.try_tag(word, self.word_strategies) if not tag else tag
            tag = "lyric" if not tag else tag

            # after tagging, do one or more of the following based on assigned tag

            # at keychange, pass new key along to song
            self.update_key(
                song=song, match=match
            ) if tag == "key" and not song.key.default else None

            # append word to line with extra typos list at [3]
            line.append((pointers.pos, tag, word, typos))

            # end of line procedures
            output = self.finalize_line(output, line) if tag == "nl" else output
            line.clear() if tag == "nl" else None

            # update pointers before moving on to next word.
            pointers.update(word)

        # assign back to song
        song.tk_tuples = output

        return song

    def finalize_line(self, elements, line):
        """When you reach the end of a line, resolve typos and ambiguities."""

        # cleanup line
        line = self.resolve_typos(line)
        line = self.resolve_ambiguities(line)

        # dump line to elements
        for word in line:
            elements.append(word)

        return elements

    def try_tag(self, element, tests):
        """Try to apply tag from element with tests."""

        for k, v in tests.items():
            if k(element):
                return v

    def update_key(self, song, match):
        """Update default key from match."""

        note = match[3]
        minor = match[4]

        # assign default + current key
        if not song.key.default:
            song.key.default = note + minor

    def resolve_typos(self, line):
        """Resolve typos, potentially splitting elements."""

        # TODO: more strategies for different typos!
        typo_strategies = {self.partial_key_bracket: self.split_key_parts}

        fixed = []

        for i, tup in enumerate(line):
            # unpack
            pos, tag, word = self.unpack_tk_tuple(tup)
            typos = tup[3]

            if typos:
                for test, fix in typo_strategies.items():
                    if test(tup=line[i]):
                        fix(tup=line[i], fixed=fixed)
            else:
                fixed.append((pos, tag, word))

        return fixed

    def partial_key_bracket(self, tup):
        """Detect partial key bracket in word."""

        return True if bool("(" in tup[2]) != bool(")" in tup[2]) else False

    def split_key_parts(self, tup, fixed):
        """Split parts of a partial key match."""

        pos, tag, word = self.unpack_tk_tuple(tup)
        parts = re.match(res.id_transposible, word)

        # break out parts, testing chord validity in the middle.
        for i in range(2, len(parts)):

            if i == 3 and parts[i]:

                chord = parts[3] + parts[4] if parts[4] else parts[3]
                fixed.append((pos, "chord", chord)) if self.recursive_chord_id(
                    chord
                ) else fixed.append((pos, "typo", chord))

                continue

            elif i == 4:

                continue

            elif i == 6:

                pass

            fixed.append((pos, "typo", parts[i])) if parts[i] else None
            # TODO: update pos for accuracy?
            # TODO: split elements need to be reevaluated for type.

    def resolve_ambiguities(self, line):
        """consider word context and reassign tags if appropriate."""

        # TODO: skip this if nothing is ambiguous

        edited = [None] * len(line)
        tags = [e[1] for e in line if e[1] not in self.ignore]

        # most common non ambiguous type on line
        most = max(tags, key=tags.count) if tags else None
        count = tags.count(most) if tags else 0

        ignore = ("ws", "key", "bar", "nl", "chord", "slashchord")

        # TODO: mess!
        for i, tup in enumerate(line):
            pos, tag, word = self.unpack_tk_tuple(tup)

            # ignore tags with low false positive rate
            if tag in ignore:
                pass
            # deal with ambiguous elements
            elif tag == "ambiguous":
                tag = self.do_strategies(
                    strategies=self.ambiguous_strategies,
                    default=tag,
                    line=line,
                    i=i,
                    most=most,
                    count=count,
                )
            # deal with lyrics in headers, and headers in lyrics
            else:
                tag = self.do_strategies(
                    strategies=self.reassign_strategies,
                    default=tag,
                    line=line,
                    i=i,
                    most=most,
                    count=count,
                )

            # repack to line
            edited[i] = (pos, tag, word)

        return edited

    def do_strategies(self, strategies, default, **kwargs):
        """Try a list of strategies, return match or default if no match."""

        for test in strategies:
            match = test(**kwargs)
            if match:
                return match

        return default

    def ambiguous_a_am(self, line, i, most, count):
        """Return True if A or Am are chord."""

        # TODO: rewrite this, doesn't catch everything correctly.

        pos, tag, word = self.unpack_tk_tuple(line[i])

        if word != "A" and word != "Am":
            return False

        for w, tup in enumerate(line):

            # TODO: strategy
            # ignore the word in question or it's
            # ambiguity will trigger chord assignment!
            if w == i:
                continue
            elif tup[1] in self.chordy_neighbors:
                return "chord"
            elif tup[1] == "header":
                return "header"
            elif tup[1] == "lyric":
                return "lyric"

        return "lyric"

    def unpack_tk_tuple(self, tup):
        """Unpack tk tuple, ignores any extra info at tup[3]"""

        pos = tup[0]
        tag = tup[1]
        word = tup[2]

        return pos, tag, word

    def get_neighbors(self, line, requested: list):
        """Get tuples of requested line neighbors."""

        linel = len(line)
        neighbors = []
        for n in requested:
            neighbors.append(line[n] if n <= linel and n >= 0 else False)
        return neighbors

    def ambiguous_digit(self, line, i, most, count):
        """Return appropriate tag for ambiguous digit."""

        pos, tag, word = self.unpack_tk_tuple(line[i])

        if not word.isdigit():
            return False

        nl = self.get_neighbors(line=line, requested=[i - 2])[0]

        return nl[1] if nl else "lyric"

    def ambiguous_to_most(self, most, **kwargs):
        """If the line has a higher number of one tag, assign ambiguous to that."""

        return most if most else False

    def ambiguous_to_header(self, line, **kwargs):
        """Conditions to assign ambiguous to header."""

        # TODO: nothing seems to trigger this, investigate...
        logging.info("ambiguous_to_header in WordFactory")
        word = line[i][2]

        return "header" if word == "I" or word.isdigit() else False

    def reassign_header_precedence(self, line, **kwargs):
        """If line begins with a header, everything should be a header except transposibles."""

        # TODO: review the logic here...
        # logging.info(f'reassign_header_precedence: line[0][1]: {line[1][1]}')
        return "header" if line[1][1] == "header" else False

    def reassign_most_precedence(self, line, i, most, count):
        """Reassign to most, if most is a significant value."""

        pos, tag, word = self.unpack_tk_tuple(line[i])
        return most if tag != most and count > 2 else False

    def flag_ambiguous(self, word):
        """Return True if word type can not be determined with certainty out of
        context. For example, 'A' (Chord, header, or lyric) 'Am' (Chord or lyric),
        'I' (lyric or header), or numbers (header, lyric, or nashville number)."""

        return word in self.ambiguous or word.isdigit()

    def flag_typos(self, match):
        """Flag a partial transposible match as a typo to hopefully be
        auto-corrected in the context of the line."""

        if not match:
            return None

        # list the typos, as multiple will probably require a different correction.
        typos = []

        # types o' typo
        typos.append("bracket") if bool(match[2]) != bool(match[5]) else None
        typos.append("slash") if bool(match[7]) != bool(match[8]) else None

        return typos

    def match_keychange(self, match: re.regex.Match):
        """Keychange must have both brackets, valid root,
        no qualities or only qualities 'm' or '-'"""

        return (
            match[2]
            and self._match_chromatics(match[3])
            and self._match_keymode(match[4])
            and match[5]
        )

    def match_chord_tk(self, match: re.regex.Match):
        """Match chord for tk ingestion. Doesn't match weird outliers like
        '(C' or 'C/'"""

        # reject non-matches, slash chords, keys, typos
        if not match or match[2] or match[5] or match[6]:
            return False

        # if chord, check qualities for validity
        if match[3]:
            if not match[4]:
                return True
            quals = assign(match[4])
            return self.recursive_qual_checker(quals)

        return False

    def _match_chord(self, match: re.regex.Match) -> bool:
        """Evaluate transposible_ids regex match for chordiness."""
        if not match:

            return False

        if match[3]:
            quals = assign(match[4])

            return self.recursive_qual_checker(quals)

        return False

    def _match_keymode(self, part):
        """Return True for valid key mode (minor or nothing)."""
        return not part or self._match_minor(part)

    def _match_minor(self, part):
        """Return True if part represents minor quality."""
        return part == "m" or part == "-"

    def _match_chromatics(self, part):
        """Return True if part is a valid chromatic note."""
        return part in ids.chromatics

    def _match_slash_chord(self, match=re.regex.Match) -> bool:
        """Return True if res.id_transposible match[6] exists,
        which should indicate a valid slash chord."""
        return bool(match[6])

    def _match_whitespace(self, word=str) -> bool:
        """Return True if string contains whitespace."""
        # TODO: should probably make this only return True if
        # entire string is whitespace. Could be problems else.
        return " " in word

    def _match_newline(self, word=str) -> bool:
        """Return True if string starts with newline char."""
        return word == "\n"

    def is_header(self, word=str) -> bool:
        """Will only match header after filtering chords."""
        # TODO: false matches for numbers in lyrics like '96 tears'
        return (
            word.isupper() and word != "I" or word.isdigit() or word in ids.header_chars
        )
        # or word.isdigit and word != 'I'
        # return bool(re.match(id_header, word)) and word != 'I'
        # return word.isupper() and word != 'I' or word.isdigit()

    def _match_barline(self, word=str) -> bool:
        return word == "/" or word == "|"

    def _match_a_or_am(self, word=str) -> bool:
        return word == "A" or word == "Am"

    def _a_or_am_is_chord(self, slices, slice_count, i=int) -> bool:
        """Look at neighbor of 'A' or 'Am' to determine if it is a chord."""

        # TODO: proper nouns beginning with A-G will throw false positives.
        # Also possible issue with bar lines
        # TODO: make sure there % aren't messing things up.
        n1 = slices[i + 1 % slice_count]
        n2 = slices[i + 2 % slice_count]

        return (
            True if n1 == "\n" or n2 in "\n/" or self.recursive_chord_id(n2) else False
        )

    def recursive_qual_checker(self, quals):
        """Used to confirm qualities are valid. Only pass the qualities part
        of a chord regex match."""

        # TODO: As you're splitting off these quals you could probably make
        # a list for ingestion by ChordQualities class.

        # TODO: This is very similar to recursive_qual_id below, albeit
        # not tied into recursive_chord_id. Maybe combinable???

        # base case. if quals have been filtered down to nothing, all parts
        # passed the check and qualities are therefore valid.
        if not quals:
            return True

        # check that quals begin with quality, filter it out, check again.
        for q in ids.qualities:
            if quals.startswith(q):
                split = quals.split(q)[-1]
                return self.recursive_qual_checker(split)

        return False

    def recursive_chord_id(self, chord, slash_flag=False):
        """This and the following method will break apart a string
        and return True if it is a chord. Doesn't account for A/Am
        ambiguities, however. Currently using regex instead but this
        is possibly more efficient."""

        logging.info("used recursive_chord_id in WordFactory")

        if not chord and not slash_flag:

            return True

        elif not chord and slash_flag:

            logging.info("recursive_chord_id: chord candidate ended with slash :/")
            return False

        for t in ids.diatonics:

            if chord.startswith(t):

                chord = chord.split(t)[-1]
                for a in ids.accidentals:
                    chord = chord.split(a)[-1] if chord.startswith(a) else chord
                return (
                    False
                    if chord
                    else True
                    if slash_flag
                    else self.recursive_qual_id(chord)
                )

        return False

    def recursive_qual_id(self, chord):
        """Companion method to recursive_chord_id for checking qualities."""

        # Base case
        if not chord:
            return True

        # Strip slash
        if chord.startswith("/"):
            chord = chord.split("/")[-1]
            return self.recursive_chord_id(chord, slash_flag=True)

        # Strip a quality
        for q in ids.qualities:
            if chord.startswith(q):
                chord = chord.split(q)[-1]
                return self.recursive_qual_id(chord)

        return False
