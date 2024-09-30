import mido
from . import exceptions
from .note import Note
from .output_event import OutputEvent, many_outputs
from . import instrument
import re

class Song:
	def __init__(self, midi: mido.MidiFile):
		self.midi = midi
		try:
			self.tempo = self.__find_meta('set_tempo').tempo
		except exceptions.MetaNotFound:
			self.tempo = 1000
		self.ticks_per_beat = self.midi.ticks_per_beat
		self.total_ticks = 0
		self.tracks = []
		self.triggers = []
		self.result = []

	def __find_instrument(self, track: mido.MidiTrack) -> mido.Message:
		for msg in track:
			try:
				if not msg.is_meta and msg.channel == 9:
					return 9
			except AttributeError:
				pass

			if msg.type == 'program_change':
				return msg.program
		raise exceptions.MessageNotFound('program_change')

	def __find_meta(self, type: str) -> mido.Message:
		for track in self.midi.tracks:
			for msg in track:
				if msg.is_meta and msg.type == type:
					return msg
		raise exceptions.MetaNotFound(type)

	"""
	Read all midi data, breaking out notes into non-overlapping tracks
	Returns self so chaining operations is possible.
	"""
	def read(self, split_chords: bool = True) -> object:
		all_tracks = []
		self.instruments = {}
		for track_num, track in enumerate(self.midi.tracks):
			current_time = 0

			try:
				instr_id = self.__find_instrument(track)
				instr_name = instrument.to_plasma(instr_id)
			except exceptions.MessageNotFound:
				instr_name = 'Keys'

			name = track.name if track.name != '' else 'UNDEF'
			tracks = [{
				'name': f'{track_num}!{name}',
				'overflow': False,
				'notes': [],
			}]

			open_notes = []
			for msg in track:
				if msg.is_meta: continue
				current_time += msg.time

				if (msg.type == 'note_on' and msg.velocity == 0) or msg.type == 'note_off':
					if split_chords:
						#Find previous "on" note of the same value and remove it from the active list.
						note = Note(msg.note, msg.velocity, current_time)
						index = open_notes.index(note)
						if index >= 0:
							orig_note = open_notes.pop(index)
							orig_note.stop = current_time

							#Break out any chords into separate tracks
							while len(tracks) < orig_note.overflow + 1:
								name = track.name if track.name != '' else 'UNDEF'
								tracks += [{
									'name': f'{track_num}!{name}',
									'overflow': True,
									'notes': [],
								}]
							tracks[orig_note.overflow]['notes'] += [orig_note]
				elif msg.type == 'note_on':
					#Add new note to the active list.
					note = Note(msg.note, msg.velocity, current_time)
					note.auto_detect_overflow(open_notes)
					if split_chords:
						open_notes += [note]
					else:
						tracks[0]['notes'] += [note]

			#Take care of any notes that were turned on but not off; Just mark them as off now.
			for note in open_notes:
				#Break out any chords into separate tracks
				while len(tracks) < note.overflow + 1:
					name = track.name if track.name != '' else 'UNDEF'
					tracks += [{
						'name': f'{track_num}!{name}',
						'overflow': True,
						'notes': [],
					}]
				tracks[note.overflow]['notes'] += [note]

			self.total_ticks = max(self.total_ticks, current_time)

			these_tracks = [i for i in tracks if len(i['notes'])]
			if len(these_tracks):
				all_tracks += these_tracks
				self.instruments[track_num] = instr_name

		self.tracks = all_tracks
		return self

	"""
	Condense all overflow tracks into the parent track with all notes that start at the same time being on the same element.
	Returns self so chaining operations is possible.
	"""
	def condense(self) -> object:
		events = {}
		overflows = {}
		track_nums = {}
		for track_num, track in enumerate(self.tracks):
			if track['name'] not in overflows:
				overflows[track['name']] = 1
				track_nums[track['name']] = track_num
			else:
				overflows[track['name']] += 1

		for track_number, track in enumerate(self.tracks):
			if track['name'] not in events:
				events[track['name']] = {}
			for note in track['notes']:
				if note.start not in events[track['name']]:
					events[track['name']][note.start] = [None] * overflows[track['name']]
				events[track['name']][note.start][track_number - track_nums[track['name']]] = note

		#Make sure all instruments have the events on the same beats.
		times = set()
		for instrument in events:
			times = times | set(events[instrument].keys())

		for instrument in events:
			for timestamp in times - set(events[instrument].keys()):
				events[instrument][timestamp] = []

		self.triggers = {}
		for instrument in events:
			#Dummy note to make sure all instruments start at the correct time.
			first_notes_index = next(iter(events[instrument].keys()))
			triggers = [{
				'time': 0,
				'notes': [None] * len(events[instrument][first_notes_index]),
			}]
			for key in sorted(events[instrument].keys()):
				triggers += [{
					'time': key,
					'notes': events[instrument][key],
				}]
			self.triggers[instrument] = triggers

		return self

	"""
	Calculate the delay between all triggers, relative to the previous one.
	Returns self so chaining operations is possible.
	"""
	def relate(self) -> object:
		result = {}
		prev_time = 0

		for instrument in self.triggers:
			result[instrument] = []
			for trigger in self.triggers[instrument]:
				if len(result[instrument]):
					result[instrument][-1].delay = mido.tick2second(trigger['time'] - prev_time, self.ticks_per_beat, self.tempo)

				result[instrument] += [OutputEvent(trigger['notes'])]
				prev_time = trigger['time']

		self.result = result
		return self

	def output(self) -> dict:
		#Make a master track with all the instruments together
		master_out = {
			'num': -1,
			'name': 'ALL',
			'notes': [],
			'instruments': [self.instruments[i] for i in self.instruments],
		}

		try:
			note_count = len( self.result[ next(iter(self.result.keys())) ] )
		except StopIteration:
			note_count = 0

		for i in range(note_count):
			master_out['notes'] += [ many_outputs([self.result[instrument][i] for instrument in self.result]) ]

		#Get all the other tracks separately
		out = []
		for instrument in self.result:
			num, name = instrument.split('!', 1)
			out += [{
				'num': int(num),
				'name': re.sub(r'[^\x01-\x80]+', '', name),
				'notes': [str(i) for i in self.result[instrument]],
				'instruments': [self.instruments[int(num)]],
			}]

		out += [master_out]
		return out

	def process(self, split_chords: bool = True) -> object:
		self.read(split_chords).condense().relate()
		return self.output()