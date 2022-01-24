# ids holds dicts / tuples used by the transposer to choose and assign
# correct permutations to transposible elements.
        
# These characters should always be identified as headers.
header_chars = ('*', ':')

# Used in transposition functions to retrieve the version of a note
# with the appropriate accidental for the current key.
# Use [-1] returns flat, [0] returns sharp. Looks like a keyboard! =D
NOTE_ID_ACCIDENTALS = {
    0:  ('C'),
    1:  ('C#', 'Db'),
    2:  ('D'),
    3:  ('D#', 'Eb'),
    4:  ('E'),
    5:  ('F'),
    6:  ('F#', 'Gb'),
    7:  ('G'),
    8:  ('G#', 'Ab'),
    9:  ('A'),
    10: ('A#', 'Bb'),
    11: ('B')
    }

# NOTE_IDS used to calculate transposition distances. This is less clever
# than poking through NOTE_ID_ACCIDENTALS but easier to read inline IMO.
# Notice inclusion of 'B#', 'Cb', 'E#', 'Fb' enharmonics, which are not
# typically used in practice.
# TODO: throw a warning when an atypical enharmonic is used.

NOTE_IDS = {
    'C':    0,
    'C#':   1,
    'Db':   1,
    'D':    2,
    'D#':   3,
    'Eb':   3,
    'E':    4,
    'Fb':   4,
    'E#':   5,
    'F':    5,
    'F#':   6,
    'Gb':   6,
    'G':    7,
    'G#':   8,
    'Ab':   8,
    'A':    9,
    'A#':   10,
    'Bb':   10,
    'B':    11,
    'Cb':   11,
    'B#':   0
    }


# Major keys with these NOTE_IDS use flats.
FLAT_MAJ_IDS = (0,  1,  3,  5,  8 , 10)
#               C   Db  Eb  F   Ab  Bb

# Minor keys with these NOTE_IDS use flats. 
FLAT_MIN_IDS = (0,  2,  5,  7,  9,  10)
#               Cm  Dm  Fm  Gm  Am  Bbm

# CHORD INGREDIENTS

# Diatonic notes of the piano
diatonics = ('C', 'D', 'E', 'F', 'G', 'A', 'B')

# Includes enharmonics that aren't used in practice (E#, Fb, B#, Cb)
chromatics = (  'Cb', 'C',  'C#', 'Db', 'D',  'D#', 'Eb',
                'E',  'E#', 'Fb', 'F',  'F#', 'Gb', 'G',
                'G#', 'Ab', 'A',  'A#', 'Bb', 'B',  'B#'
            )

# [0] = natural, [1] = sharp, [-1] = flat
accidentals = (' ', '#', 'b') 

# These ingredients make up the chords qualities (color).
qualities = (
    'add', 'aug', 'dim', 'Maj', 'maj', 'm', 'sus',
    '0', '1', '2', '3', '4', '5', '6', '7', '8', '9',
    '-', '+', '°', 'Δ', 
    '(', ')', '.', # <---See note below.
    )
    # The last row characters are not used in trad chord naming conventions,
    # however, I use them inline to show phrasing (brackets) or to
    # indicate a staccato / stab (.). Of course this would allow some garbage
    # to get through and be identified as chords but shouldn't be a problem
    # with reasonable attention to formatting.


# Nashville numbers tuples. Calling NASH_M...S[i] returns a representation
# for the chord that is i steps from the root of the current key. Slightly
# different representations from each tuple.
# TODO: learn more about this style of notation, not sure these are all
# actually used in practice or fomatted correctly? They return correct
# numbers but maybe not what players are used to seeing...
NASH_MAJ_FLATS = (  '1', 'b2', '2', 'b3', '3', '4',
                    'b5', '5', 'b6', '6', 'b7', '7'
                    )
NASH_MAJ_SHARPS = ( '1', '#1', '2', '#2', '3', '4',
                    '#4', '5', '#5', '6', '#6', '7'
                    )
# Includes #6 instead of b7, #7 instead of b1 as per general practice.
NASH_MIN_FLATS = (  '1', 'b2', '2', '3', 'b4', '4',
                    'b5', '5', '6', '#6', '7', '#7'
                    )
NASH_MIN_SHARPS = ( '1', 'b2', '2', '3', '#3', '4',
                    '#4', '5', '6', '#6', '7', '#7'
                    )

# tags of transposible elements
transposibles = ('key', 'chord', 'slashchord', 'slash')

def nashville_subs(quals):
    """If quals have an appropriate Nashville substitution, return that sub."""
    # TODO: incomplete fn!!! This will replace Chord._replace_m_with_dash
    # also prombably move this func
    # TODO: implement
    if quals == 'm' or quals == '-':
        return '-'
    elif quals == 'maj7' or quals == 'Maj7':
        return 'Δ'
    elif quals == '7':
        return '^7' # TODO: superscript formatting!!
    elif quals == 'dim':
        return '°'
    elif quals == 'dim7':
        return '°7'
    elif quals == 'augmin7':
        return '+^7' # TODO: superscript formatting!
    elif quals.lower() == 'augmaj7':
        return '+Δ'
    return quals

# TODO: Roman numerals...
    