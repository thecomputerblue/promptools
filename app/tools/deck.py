import logging

from tools.apppointers import AppPointers
from tools.history import SongHistory

class SongDeck(AppPointers):
	"""Implements an observer pattern so frames of the app
	update correctly when a param is loaded to live, unloaded,
	or cued."""

	# TODO: track play history through here, and use
	# it for more comprehensive triggers.

	def __init__(self, app):
		AppPointers.__init__(self, app)
		
		self.callbacks = {}

		self._cued = None
		self._live = None
		self._previous = None
		self._focused = None
		
		self.history = SongHistory(app)

		# refresh function assigned when a song is cued from pool / setlist 
		self.refresh = None

	def add_callback(self, param, callback, *args, **kwargs):
		"""Add an observer & callback to the param dict."""
		# TODO: this is... not really working. *args and **kwargs mainly
		# simplify based on what is actually needed in this context...

		if not param in self.callbacks:
			self.callbacks[param] = {}

		if not callback in self.callbacks[param]:
			self.callbacks[param][callback] = {}

		# TODO: needlessly nested, probably
		self.callbacks[param][callback]['args'] = args
		self.callbacks[param][callback]['kwargs'] = kwargs

	def push(self, *args):
		"""Callback to any frames called in args."""

		for k, v in self.callbacks.items():
			if k in args:
				logging.info(f'callback push: {k}')
				self.do_callbacks(callbacks=v)

	def do_callbacks(self, callbacks):
		"""Unpack and execute callbacks"""

		if not callbacks:
			return

		for k, v in callbacks.items():
			args = v.get('args')
			kwargs = v.get('kwargs')
			k(*args, **kwargs)

	def remove_callback(self, param, callback):
		"""Remove a callback reference."""

		if param in self.callbacks and callback in self.callbacks[param]:
			self.callbacks[param].remove(callback)

	@property
	def cued(self):
		return self._cued

	@cued.setter
	def cued(self, new):
		self._cued = new
		self.push("cued")
		self.focused = new

	@property
	def live(self):
		return self._live

	@live.setter
	def live(self, new):
		self.previous = self._live
		self.history.add(self._live)
		self._live = new
		self.push("live")

	@property
	def previous(self):
		return self._previous

	@previous.setter
	def previous(self, new):
		self._previous = new
		self.push("previous")

	@property
	def focused(self):
		"""Track the song in focus (info exposed in song detail)"""
		logging.info('got focused from deck')
		return self._focused

	@focused.setter
	def focused(self, new):
		"""Trigger focus callbacks."""
		self._focused = new 
		self.push("focused")

	def new(self):
		"""Push new song to live."""
		logging.info('generated new song')
		self.live = self.app.tools.factory.new_song()
		self.focused = self.live
