class Helper:
	"""Manages flow of messages to helper gui. Point all helper pushes here,
	when I switch from tkinter I can then just update this class to interface
	with new gui package."""

	def __init__(self, app):
		self.app = app 
		self.stack = []

	def popup(self, msg, dur=3000):
		self.app.helper.popup(msg, dur)

	def set(self, msg):
		self.app.helper.set(msg)

	# TODO: move dur to settings