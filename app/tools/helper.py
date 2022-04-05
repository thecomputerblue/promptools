import logging

from tools.apppointers import AppPointers

class Helper(AppPointers):
	"""Manages flow of messages to helper gui. Point all helper pushes here,
	when I switch from tkinter I can then just update this class to interface
	with new gui package."""

	def __init__(self, app):
		AppPointers.__init__(self, app)

		# TODO: stack
		# self.stack = []

	def popup(self, msg, dur=3000):
		self.gui.helpbox.popup(msg, dur)

	def set(self, msg):
		self.gui.helpbox.set(msg)

	# TODO: move dur to settings