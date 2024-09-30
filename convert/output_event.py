class OutputEvent:
	def __init__(self, notes: list):
		self.notes = notes
		self.delay = 0

	def __str__(self) -> str:
		n = self.out_notes()
		return f'{"+".join(n) if len(n) else " "}|{self.delay:.4f}'

	def out_notes(self) -> list:
		return [' ' if note is None else f'{note.tone}/{note.octave}/{note.volume}' for note in self.notes]


def many_outputs(outputs: list) -> str:
	delay = outputs[0].delay
	return '&'.join(['+'.join(i.out_notes()) if len(i.notes) else ' ' for i in outputs]) + f'|{delay:.4f}'