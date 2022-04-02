import weakref
import logging
import gc 

from tools.apppointers import AppPointers

class Cache(AppPointers):
	"""Class for caching. For now just using to track and batch-process
	all active songs in the program (ie. if a DB entry is deleted, anything
	currently in memory needs its references to that updated so when you save
	back to DB there isn't any accidental overwriting. Expand later as needed."""

	def __init__(self, app):
		AppPointers.__init__(self, app)

		self.songs = []

		# probably don't need this as all setlists are stored in the same place
		# self.setlists = []

	def add_song(self, song):
		"""Add a weakref to the song in the song list."""

		# TODO: you can add a callback after the comma, which will run
		# when the object is about to be finalized. see:
		# https://docs.python.org/3/library/weakref.html
		self.songs.append(weakref.ref(song, ))
		# logging.info(f"added song {song} to cache")
		self.cleanup()

	def cleanup(self):
		"""Run gc, cleanup list references."""
		gc.collect()
		self.songs = [ref for ref in self.songs if ref() != None]

	def remove_song(self, song):
		"""Manually remove song from cache (they should be removed
		automatically by gc due to using weak references, but that
		isn't consistently happening. TODO: investigate^)"""

		songs.pop(song) if song in songs \
		else self.raise_exception(f'{song.name} not found in cache!!!')

	def raise_exception(self, exception):
		"""Raise an exception if something goes wrong here."""
		raise Exception(exception)