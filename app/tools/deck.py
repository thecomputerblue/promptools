import logging

class SongDeck:
	"""Implements an observer pattern so frames of the app
	update correctly when a param is loaded to live, unloaded,
	or cued."""

	# TODO: track play history through here, and use
	# it for more comprehensive triggers.

	def __init__(self, app):
		self.app = app
		self.callbacks = {}

		self._cued = None
		self._live = None
		self._previous = None

		# refresh function assigned when a song is cued from pool / setlist 
		self.refresh = None

	def add_callback(self, param, callback, *args, **kwargs):
		"""Add an observer & callback to the param dict."""

		if not param in self.callbacks:
			self.callbacks[param] = {}

		if not callback in self.callbacks[param]:
			self.callbacks[param][callback] = {}

		# TODO: needlessly nested, probably
		self.callbacks[param][callback]['args'] = args
		self.callbacks[param][callback]['kwargs'] = kwargs

	def push(self, *args):
		"""Callback to any frames called in args."""

		for k,v in self.callbacks.items():
			if k in args:
				self.do_calls(v)

	def do_calls(self, calls):
		"""Execute a list of callbacks without args."""

		if not calls:
			return

		for k,v in calls.items():
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

	@property
	def live(self):
		return self._live

	@live.setter
	def live(self, new):
		self.previous = self._live
		self._live = new
		self.push("live")

	@property
	def previous(self):
		return self._previous

	@previous.setter
	def previous(self, new):
		self._previous = new
		self.push("previous")
	

	
