note = V1
instrument = V2
center_octave = V3

if note == ' ' then return end

function split(text, delim)
	local result = {}
	local value
	for value in text:gmatch('[^'..delim..']+') do
		table.insert(result, value)
	end
	return result[1], result[2], result[3]
end

tone, octave, volume = split(note, '/')
if instrument == 'Drum' then
	tones = {['A']=0, ['A#']=1, ['B']=2, ['C']=3, ['C#']=4, ['D']=5, ['D#']=6, ['E']=7, ['F']=8, ['F#']=9, ['G']=10, ['G#']=11 }
	tone_num = (12 * tonumber(octave)) + tones[tone]
	instrs = {
		[35]='Kick', [36]='Kick',
		[38]='Snare', [40]='Snare',
		[42]='HH', [46]='HH', [51]='HH', [52]='HH', [53]='HH', [54]='HH', [55]='HH', [59]='HH',
		[49]='Crash', [57]='Crash',
		[48]='Tom1', [50]='Tom1', [60]='Tom1', [62]='Tom1', [63]='Tom1', [65]='Tom1', [67]='Tom1',
		[41]='Tom2', [43]='Tom2', [45]='Tom2', [47]='Tom2', [61]='Tom2', [64]='Tom2', [66]='Tom2', [68]='Tom2'
	}

	if instrs[tone_num] == nil then tone = 'Kick' else tone = instrs[tone_num] end
end

sound = instrument .. '/' .. tone
octave = ((tonumber(octave) - center_octave + 1) % 3) - 1 --Fit the octave into one of (-1, 0, 1)
volume = tonumber(volume)

output(sound, 1)
output(volume, 2)
output(octave, 3)