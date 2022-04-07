# little tap tempo calc to be used later to filter library by tempo!
import time

from tools.apppointers import AppPointers

# helpers
def diffs(times):
	"""Return a list of the differences between adjacent times.'"""
	if len(times) < 2:
		return
	d = []
	for i in range(len(times)-2):
		d.append(times[i+1]-times[i])
	return d

def avg(diffs):
	return sum(diffs) / len(diffs)

def seconds_to_tempo(s):
	return 60/s

def s_to_ms(s):
	return 1000*s

def ms_to_s(ms):
	return ms/1000

def limit(t, tmin, tmax):
	while t > tmax:
		t = t/2
	while t < tmin:
		t = t*2
	return t


class TapTempo(AppPointers):
	"""Simple tap tempo calculator by me. Takes average of time between
	a taps and converts to BPM as float. App can truncate to appropriate
	digits."""

	def __init__(self, app):
		AppPointers.__init__(self, app)

		# track last several taps
		self._queue = []

		# number of taps needed to guess tempo
		self.guess_at = 3
		
		# max number of taps used in tempo calc, 0 is unlimited
		self.window = 6

		# after self.clear_ms milliseconds, clear the taps buffer
		self.reset_ms = 1500

		# outer tempo ranges. readings over max halved until they're in tempo range.
		self.tmin = 40
		self.tmax = 200

		# shown tempo
		self._tempo = None

		# Assign callbacks here to trigger app update when tempo changes
		self.callbacks = []

	def tap(self):
		"""Add a tap to the taps."""

		self.add_to_queue(time.time())
		self.try_update_tempo()
		self.schedule_reset()

	def add_to_queue(self, time):
		self._queue.append(time)
		self._queue = self._queue[-self.window:]

	def try_update_tempo(self):
		if len(self._queue) >= self.guess_at:
			self.tempo = seconds_to_tempo(avg(diffs(self._queue)))

	@property
	def tempo(self):
		return self._tempo

	@tempo.setter 
	def tempo(self, new):
		self._tempo = self.limit(new) 
		self.do_callbacks()

	def do_callbacks(self):
		if not self.callbacks:
			return
		[c() for c in self.callbacks]

	def schedule_reset(self):
		# schedule try_reset with tkinter
		self.app.gui.after(self.reset_ms, self.try_reset)

	def try_reset(self):
		if not self._queue:
			return
		if time.time() - self._queue[-1] > ms_to_s(self.reset_ms):
			self._queue = []

	def limit(self, t):
		"""Limit tempo range so if someone taps double or half time it reads
		correctly."""
		return limit(t, self.tmin, self.tmax)