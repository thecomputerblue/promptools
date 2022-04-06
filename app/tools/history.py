# snapshot every song that was loaded to live in a session so one can roll back
from copy import deepcopy
import logging

from tools.apppointers import AppPointers

class SongHistory(AppPointers):
	"""Stores a list of songs by copying song objects. Implemented so that
	when the live song changes, the old one is copied into this objects
	song list. This gives the app a 'snapshot' of the song in whatever state
	it was in before it was unloaded, so it can be recovered if needed."""

	def __init__(self, app):
		AppPointers.__init__(self, app)
		self._songs = []
		self.callbacks = []
		# max length of history. delete older songs
		self.song_limit = 20

	@property
	def songs(self):
		return self._songs
	
	def add(self, song):
		if not song:
			return
		# TODO: song method to refresh timestamps, which can then be accessed
		# by the history viewer.
		dup = deepcopy(song)
		dup.modified_stamp()
		self._songs.append(dup)
		self._limit()
		self.log_names()

	def _limit(self):
		"""Limit song list."""
		if len(self.songs) > self.song_limit:
			self._songs = self._songs[-self.song_limit:]

	def do_callbacks(self):
		if not self.callbacks:
			return
		[c() for c in self.callbacks]

	def log_names(self):
		if not self.songs:
			return
		logging.info("SONG HISTORY IS:")
		for song in self.songs:
			logging.info(song.name)

	def fetch(self, i):
		print(i)
		return deepcopy(self.songs[int(i)])
