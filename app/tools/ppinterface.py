import plistlib
import base64
import pandoc
import os

# writing some stuff to interface with presentation prompter

# first I'm going to reconstruct the properties list that pp applies to its rtf documents.
# this will eventually allow me to export setlists to PP with bookmarks, and even
# potentially preserve yview or scroll speed since those are stored in the plist

# defining some basic stuff I see in these plist files

# PP plist files all contain this. not sure what it is but i'm including it.
RAW_TOKEN = "YnBsaXN0MDDUAQIDBAUGFxhYJHZlcnNpb25YJG9iamVjdHNZJGFy" + \
		"Y2hpdmVyVCR0b3ASAAGGoKQHCA8QVSRudWxs0wkKCwwNDlRuYW1l" + \
		"VHR5cGVWJGNsYXNzgAIQAIADUNIREhMUWiRjbGFzc25hbWVYJGNs" + \
		"YXNzZXNaUFBCb29rbWFya6IVFlpQUEJvb2ttYXJrWE5TT2JqZWN0" + \
		"XxAPTlNLZXllZEFyY2hpdmVy0RkaVHJvb3SAAQgRGiMtMjc8QklO" + \
		"U1pcXmBhZnF6hYiTnK6xtgAAAAAAAAEBAAAAAAAAABsAAAAAAAAA" + \
		"AAAAAAAAAAC4"

# need to decode the token and re-encode to get it in plist file correctly.
TOKEN = base64.b64decode(RAW_TOKEN)

# TODO: dataclasses?
class PPPropertyList:
	"""Struct replicating pp plist hierarchy in python."""

	def __init__(self, *args, **kwargs):
		self.bookmarks = PPBookmarks()
		self.extendedMetadata = PPExtendedMetadata()
		self.speed = 5.9999999999999973

	def get(self):
		"""Return the dict to make the plist file."""
		return {
		"appBuildNumber" : 722,
		"appVersion" : "5.8.1",
		"bookmarks" : self.bookmarks.get(),
		"extendedMetadata": self.extendedMetadata.get(),
		"fileFormatNumber": 5,
		"scrollbarPosition": 0.0,
		"selectedRanges": ["{0, 0}"],
		"speed": self.speed,
		"systemVersion": "10.12.5",
		"windowFrame": "{{80, 87}, {1360, 790}}"
		}


class PPBookmarks:
	"""Struct replicating the pp bookmark dict in Properties.plist"""

	def __init__(self, *args, **kwargs):
		# store locations as list of ints. int is the absolute character
		# value of of the bookmark location. 
		self._locations = kwargs.get('locations') if kwargs.get('locations') else [1, 2]

	@property 
	def data(self):
		"""I have no idea what this is but it is in any .plist file
		with bookmarks."""
		# TODO: not sure if this needs to be explicitly formatted a certain way...
		return bytes(TOKEN)

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
		# array (in python just a list) of strings
		self.bookmarkNames = []

	def get(self):
		return {
		"attachmentNames": self.attachmentNames,
		"bookmarkNames": self.bookmarkNames
		}


# TESTING BELOW
package = "TEST_PACKAGE.ppdocument"
content = package + "/Content.rtfd"

def make_pp_package():
	make_pp_outer_package()
	make_content_wrapper()

def make_pp_outer_package():
	if not os.path.exists(package):
	    os.mkdir(package)	

def make_content_wrapper():
	if not os.path.exists(content):
	    os.mkdir(content)

def dump_test_props():
	file = package + "/Properties.plist"
	props = PPPropertyList()
	with open(file, 'wb') as fp:
		plistlib.dump(props.get(), fp)

def dump_test_str():
	file = content + "/TXT.rtf"
	text = "Proof of concept, exporting to rtf from string"
	doc = pandoc.read(text)
	pandoc.write(doc=doc, file=file)

def dump_test_pkg():
	file = "PKG_TEST.ppdocument"
	with open(file, 'w') as f:
		pass


def main():
	make_pp_package()
	dump_test_props()
	dump_test_str()

if __name__ == "__main__":
	main()

"""
plistlib: https://docs.python.org/3/library/plistlib.html
pandoc: https://boisgera.github.io/pandoc
apple document packages: https://developer.apple.com/library/archive/documentation/CoreFoundation/Conceptual/CFBundles/DocumentPackages/DocumentPackages.html
"""
