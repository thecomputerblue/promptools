import plistlib as pll
import struct

def rawbytes(s):
    """Convert a string to raw bytes without encoding"""
    outlist = []
    for cp in s:
        num = ord(cp)
        if num < 255:
            outlist.append(struct.pack('B', num))
        elif num < 65535:
            outlist.append(struct.pack('>H', num))
        else:
            b = (num & 0xFF0000) >> 16
            H = num & 0xFFFF
            outlist.append(struct.pack('>bH', b, H))
    return b''.join(outlist)

# writing some stuff to interface with presentation prompter

# first I'm going to reconstruct the properties list that pp applies to its rtf documents.
# this will eventually allow me to export setlists to PP with bookmarks, and even
# potentially preserve yview or scroll speed since those are stored in the plist

# defining some basic stuff I see in these plist files

# probably don't need this if i use plistlib but leaving fo rnow
HEADER = \
"""<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">"""

def token():
	def raw():
		return \
		"YnBsaXN0MDDUAQIDBAUGFxhYJHZlcnNpb25YJG9iamVjdHNZJGFy" + \
		"Y2hpdmVyVCR0b3ASAAGGoKQHCA8QVSRudWxs0wkKCwwNDlRuYW1l" + \
		"VHR5cGVWJGNsYXNzgAIQAIADUNIREhMUWiRjbGFzc25hbWVYJGNs" + \
		"YXNzZXNaUFBCb29rbWFya6IVFlpQUEJvb2ttYXJrWE5TT2JqZWN0" + \
		"XxAPTlNLZXllZEFyY2hpdmVy0RkaVHJvb3SAAQgRGiMtMjc8QklO" + \
		"U1pcXmBhZnF6hYiTnK6xtgAAAAAAAAEBAAAAAAAAABsAAAAAAAAA" + \
		"AAAAAAAAAAC4"
	return rawbytes(raw())

# TODO: dataclasses?
class PPPropertyList:
	"""Struct replicating pp plist hierarchy in python."""

	def __init__(self):
		self.data = {
	"appBuildNumber" : 722,
	"appVersion" : "5.8.1",
	"bookmarks" : PPBookmarks().get(),
	"extendedMetadata": PPExtendedMetadata().get(),
	"fileFormatNumber": 5,
	"scrollbarPosition": 0.0,
	"selectedRanges": ["{0, 0}"],
	"speed": 5.9999999999999973,
	"systemVersion": "10.12.5",
	"windowFrame": "{{80, 87}, {1360, 790}}"
	}

	def get(self):
		return self.data

class PPBookmarks:
	"""Struct replicating the pp bookmark dict in Properties.plist"""

	def __init__(self):
		# store locations as list of ints. int is the absolute character
		# value of of the bookmark location. 
		self._locations = [1, 2, 3]

	@property 
	def data(self):
		"""I have no idea what this is but it is in any .plist file
		with bookmarks."""
		# TODO: not sure if this needs to be explicitly formatted a certain way...
		return token()

	@property
	def locations(self):
		return ', '.join(str(l) for l in self._locations)

	def get(self):
		"""Returns the PP Bookmark format, which is a dict inside an
		array for some unknown reason..."""
		return [{
		"data": self.data,
		"locations" : self.locations,
		}]

class PPExtendedMetadata:
	def __init__(self):
		# leave empty, think inline images would go in here
		self.attachmentNames = []
		# array of strings
		self.bookmarkNames = []

	def get(self):
		return {
		"attachmentNames": self.attachmentNames,
		"bookmarkNames": self.bookmarkNames
		}

bookmarks = PPBookmarks()
extended_metadata = PPExtendedMetadata()


file = "testdump"

def main():
	props = PPPropertyList()
	with open(file, 'wb') as fp:
		pll.dump(props.get(), fp)

main()

"""
plistlib documentation; https://docs.python.org/3/library/plistlib.html
"""
