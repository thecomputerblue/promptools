# export active song or entire setlist to .txt file.
import logging

from tools.apppointers import AppPointers

class TxtExporter(AppPointers):
	def __init__(self, app):
		AppPointers.__init__(self, app)

		# lines between consecutive docs on an export
		self.lines_between = 5

	def get_text(self, song):
		if not song:
			return 
		logging.info(song.plain_text)
		return song.plain_text

	def export_one_song(self, song):
		out = song.plain_text
		logging.info(out)

	def export_many_songs(self, songs: list):
		out = ""

		# TODO: song metadata to control spacing behavior. ie. song has its own
		# property that indicates how many spaces should be added at the end...
		for song in songs:
			logging.info(song.tk_tuples)
			out += song.plain_text
			out += self.lines_between * "\n"
		logging.info(out)