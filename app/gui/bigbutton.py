import tkinter as tk 

class PromptButton(tk.Frame):
	"""Class for the button that runs the teleprompter."""

	def __init__(self, parent, *args, **kwargs):
		"""Class for the big context sensitive button. Currently always prompts
		whatever is previewed, will eventually react to context."""
		tk.Frame.__init__(self, parent.frame,
			# highlightbackground='grey',
			# highlightthickness=10,
			borderwidth= 5,
			relief='raised'
			)

		self.app = parent
		self.settings = self.app.settings

		# big button
		self.button = tk.Button(
			self,
			font=self.settings.fonts.button,
			text='PROMPT',
			border=0,
			relief='groove',
			width=1, height=1,
			activeforeground='pink',
			command=self.click)
		self.button.pack(fill='both', expand=True)


	def click(self):
		"""What to do when clicked."""
		
		editing = self.settings.editor.enabled
		running = self.settings.scroll.running

		# TODO: rename on_edit_mode to be more informative
		# this disables editing
		self.app.menu.on_edit_mode() if editing.get() else None

		# stop anything that's running
		running.set(False)

		# load cue, focus monitor
		self.app.tools.loader.load_cued_to_live()
		self.app.monitor.focus_set()