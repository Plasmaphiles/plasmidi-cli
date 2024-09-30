__all__ = ['Note']


class Note:
	def __init__(self, value: int, volume: int, start: int):
		tones = ('A','A#','B','C','C#','D','D#','E','F','F#','G','G#')
		self.value = value
		self.volume = int(volume * 100 / 127) #convert to percent range
		self.start = start
		self.stop = -1
		self.overflow = 0
		self.tone = tones[(value - 21) % len(tones)]
		self.octave = max(0, (value - 21 + 9) // len(tones))

	def __eq__(self, other: object) -> bool:
		return self.value == other.value

	def __str__(self) -> str:
		return f'{self.overflow}: {self.tone}{self.octave}\t{self.start}-{self.stop}'

	def overlaps(self, other: object) -> bool:
		return self.start <= other.start + 10

	def auto_detect_overflow(self, others: list) -> None:
		for other in reversed(others):
			if self.overlaps(other):
				self.overflow = max(self.overflow, other.overflow + 1)