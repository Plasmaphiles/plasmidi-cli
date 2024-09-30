input_text = V1
CHUNK_SIZE = 200

if input_text == '' then return end

--Lookup table for base85 characters
local B85_CHARS = '0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz!#$%&()*+-;<=>?@^_`{|}~'
local B85_LKUP = {}
local i
for i=1, #B85_CHARS do
	B85_LKUP[B85_CHARS:sub(i,i)] = i - 1
end

--returns an iterator to get bytes off the stream one by one
function b85decode(text)
	--convert an integer into 4 bytes
	local int2bytes = function(integer)
		local i
		local result = {}
		for i = 1, 4 do
			result[i] = integer % 256
			integer = math.floor(integer / 256)
		end
		return result
	end

	--main iterator: returns one byte at a time
	return function(replace_groups)
		if i_b85 <= #text and b == 0 then
			local k
			local integer = 0
			for k = 0, 4 do
				if i_b85+k <= #text then
					local chr = text:sub(i_b85+k, i_b85+k)
					integer = integer * 85 + B85_LKUP[chr]
				else
					integer = integer * 85
				end
			end
			i_b85 = i_b85 + 5
			bytes = int2bytes(integer)
			b = #bytes
		end

		if b > 0 then
			local byte = bytes[b]

			--If a 'most common group' indicating byte was found, replace the byte with the appropriate group
			if replace_groups ~= nil and replace_groups[byte] ~= nil then
				local rp_byte
				local j
				for j, rp_byte in pairs(replace_groups[byte]) do
					table.insert(bytes, b, rp_byte)
				end
				b = b + #replace_groups[byte] - 1
				byte = bytes[b]
			end
			b = b - 1
			return byte
		end
	end
end

--convert a list of bytes to an integer
function bytes2int(bytes)
	local integer = 0
	local byte
	local offset = 1
	for _, byte in pairs(bytes) do
		integer = integer + (byte * offset)
		offset = offset * 256
	end
	return integer
end

--Pretty-print arbitrary data
function pretty_print(data, indent)
	if indent == nil then indent = 0 end

	local key
	local value
	local i

	if type(data) == 'table' then
		pretty_print('{', indent)
		for key, value in pairs(data) do
			pretty_print(value, indent + 1)
		end
		pretty_print('}', indent)
	else
		print(('  '):rep(indent) .. data)
	end
end

--Read a specific number of bytes from the stream
function read(stream, byte_count, replace_groups)
	local i
	local result = {}
	for i=1, byte_count do
		table.insert(result, stream(replace_groups))
	end
	return result
end

function join(array, delim)
	local key
	local value
	local result = ''
	for key, value in pairs(array) do
		if key ~= 1 then result = result .. delim end
		result = result .. value
	end
	return result
end

function split(text, delim)
	local result = {}
	local value
	for value in text:gmatch('[^'..delim..']+') do
		table.insert(result, value)
	end
	return result
end

function split_nums(text, delim)
	local result = {}
	local value
	for value in text:gmatch('[^'..delim..']+') do
		table.insert(result, tonumber(value))
	end
	return result
end

function read_event()
	tracks = {}
	for track_num = 1, TRACK_COUNT do
		notes = {}

		note_num = 1
		while note_num <= CHORDS[track_num] do
			b1 = stream(COMMON_GROUPS)

			if b1 == 254 then --No events for this chord, just 1 byte for this
				table.insert(notes, ' ')
				note_num = CHORDS[track_num] + 1
			elseif b1 == 255 then --Null note, just 1 byte for this note
				table.insert(notes, ' ')
				note_num = note_num + 1
			else --Any regular note consists of 2 bytes
				tone = tones[(b1 % #tones) + 1]
				octave = math.floor(b1 / #tones)
				volume = stream(COMMON_GROUPS)
				table.insert(notes, string.format('%s/%d/%s', tone, octave, volume))
				note_num = note_num + 1
			end
		end

		table.insert(tracks, join(notes, '+'))
	end

	d_bytes = read(stream, 3, COMMON_GROUPS)
	delay = d_bytes[1]..'.'..d_bytes[2]..d_bytes[3]

	return join({join(tracks, '&'), delay}, '|')
end

function INIT_STATE()
	--Default values for global vars, these get changed later when the state is loaded
	ALL_NOTES = {}
	EVENT_COUNT = 0
	EVENT_START = 1
	i_b85 = 1
	b = 0
	bytes = {}
	CHORDS = {}
	COMMON_GROUPS = {}
end


function SAVE_STATE()
	local context = {
		join(ALL_NOTES, '@'),
		tostring(EVENT_COUNT),
		tostring(EVENT_START),
		tostring(TRACK_COUNT),
		tostring(i_b85),
		tostring(b),
		join(bytes, ','),
		join(CHORDS, ',')
	}

	local key
	local value
	local grp = {}
	for key, value in pairs(COMMON_GROUPS) do
		table.insert(grp, string.format('%s|%s', key, join(value,',')))
	end
	table.insert(context, join(grp, '@'))
	return context
end

function LOAD_STATE(context)
	ALL_NOTES = split(context[1], '@')
	EVENT_COUNT = tonumber(context[2])
	EVENT_START = tonumber(context[3])
	TRACK_COUNT = tonumber(context[4])
	i_b85 = tonumber(context[5])
	b = tonumber(context[6])
	bytes = split_nums(context[7], ',')
	CHORDS = split_nums(context[8], ',')

	COMMON_GROUPS = {}
	local _
	local value
	for _, value in pairs(split(context[9], '@')) do
		local items = split(value, '|')
		COMMON_GROUPS[tonumber(items[1])] = split_nums(items[2], ',')
	end
end

function BEGIN()
	INIT_STATE()

	--[[Open byte stream for decoded data]]
	stream = b85decode(input_text)

	--[[Read table of most common byte groups]]
	COMMON_GROUPS = {}
	group_ct = stream() --first byte is num of groups (max 126)
	for i=128, 128 + group_ct - 1 do
		group_sz = stream() --number of bytes in group
		COMMON_GROUPS[i] = read(stream, group_sz)
	end

	--[[Track count]]
	TRACK_COUNT = bytes2int(read(stream, 4, COMMON_GROUPS))
	--[[List of note count on each track]]
	CHORDS = read(stream, TRACK_COUNT, COMMON_GROUPS)
	--[[Number of 'note' events]]
	EVENT_COUNT = bytes2int(read(stream, 4, COMMON_GROUPS))
	EVENT_START = 1

	print(('<color=#D6C156>Received %dB of compressed PlasMIDI data.</color>'):format(#input_text))
	print('  Track count = ' .. TRACK_COUNT)
	print('  Chord size of each track = ['..join(CHORDS, ', ')..']')
	print('  Note event count = ' .. EVENT_COUNT)
	print('Decompressing data...')

	tones = {'A','A#','B','C','C#','D','D#','E','F','F#','G','G#'}

	ALL_NOTES = {}

	output_array(SAVE_STATE(), 2) --Continue processing later
end

function CONTINUE()
	INIT_STATE()
	LOAD_STATE(V2)

	if ALL_NOTES == nil then ALL_NOTES = {} end

	evt_end = math.min(EVENT_COUNT, EVENT_START + CHUNK_SIZE)
	for _=EVENT_START, evt_end do
		table.insert(ALL_NOTES, read_event())
	end
	EVENT_START = evt_end + 1

	print(('%d%%'):format(math.floor(evt_end * 100 / EVENT_COUNT)))

	if evt_end >= EVENT_COUNT then
		print('Done.')
		output_array(ALL_NOTES, 1) --Done processing
	else
		output_array(SAVE_STATE(), 2) --Continue processing later
	end
end

BEGIN()