# file for all the regexes
import regex as re 

# Split contents of doc while preserving whitespace.
id_slices = re.compile(r'([*:]|\S+|\n)')

# Identifies transposible elements. Will also pick up a few outliers
# such as the words 'A' and 'Am' and any word beginning uppercase A-G.
# These are flagged and evaluated in context.
# TODOS:
#	- If I embed qualities at the beginning of [4] will there be
# 	a performance improvement?
# 	- Can probably expand this to catch other useful patterns (ie.
#	 file end notes)
#	- Currently using a mix of regex and my own methods for ID. Look at
#	performance and choose most efficient combo.

id_transposible = re.compile(r'''(
	(\()?					# 2 left bracket
	([A-G][b#]?)			# 3 root
	([A-Za-z0-9'.\-]*)		# 4 qualities
	(\))?					# 5 right bracket
	((\/)([A-G][b#]?))?		# 7 slash # 8 bass
	)''', re.VERBOSE)