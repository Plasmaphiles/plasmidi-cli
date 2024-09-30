import base64
from collections import Counter

def serialize_chord(chord: str) -> bytes:
	tones = ('A','A#','B','C','C#','D','D#','E','F','F#','G','G#')
	result = bytes()

	for note in chord.split('+'):
		if note != ' ':
			tone, octave, volume = note.split('/')
			note_byte = len(tones) * int(octave) + tones.index(tone)
			result += bytes([note_byte, int(volume)])
		else:
			result += bytes([255])

	return result

def compress(sequence: list) -> str:
	result = bytes()

	if len(sequence):
		n1 = [i.split('+') for i in sequence[0].split('|')[0].split('&')]
	else:
		n1 = []

	track_count = len(n1)
	chords = [len(i) for i in n1]
	event_count = len(sequence)

	#First 4 bytes of data are the number of tracks
	result += track_count.to_bytes(4, byteorder = 'little', signed = False)
	for chord in chords:
		#1 byte for each track indicates the number of notes the track may have at a time
		result += chord.to_bytes(1, byteorder = 'little', signed = False)
	#Next 4 bytes after that are the number of 'note' events
	result += event_count.to_bytes(4, byteorder = 'little', signed = False)

	all_notes = {}

	for event in sequence:
		track, delay = event.split('|')

		for chord in track.split('&'):
			if chord == ' ':
				result += bytes([254])
			else:
				group = serialize_chord(chord)
				all_notes[group] = all_notes[group] + 1 if group in all_notes else 1
				result += group

		#3 bytes at the end of each line represent the delay
		delay = delay.replace('.', '')
		if len(delay) % 2:
			delay = '0' + delay
		result += bytes([int(delay[i:i+2]) for i in range(0, len(delay), 2)])


	# AFTER SERIALIZING, Compress a little more!

	#Make table of 64 most common chords (if they occur more than 3 times ever)
	common_groups = []
	curr_ct = 0
	for key, value in reversed(sorted(all_notes.items(), key=lambda item: item[1])):
		if curr_ct >= 126: break
		if value < 4: continue
		common_groups += [key]
		result = result.replace(key, bytes([128 + curr_ct]))
		curr_ct += 1

	#Generate table of common chords and put at the beginning
	compressed_result = bytes([len(common_groups)])
	for i in common_groups:
		compressed_result += bytes([len(i)]) + i
	compressed_result += result

	return base64.b85encode(compressed_result).decode('utf-8')