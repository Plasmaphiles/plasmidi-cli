# PlasMIDI

PlasMIDI lets you convert MIDI files to a format that's easy to parse in Plasma.

Created by SenorCluckens and Leonardo1123.

## Requirements
The only requirements are Python 3 and the `mido` module. You can install it with pip, e.g. `python3 -m pip install mido`. You can totally do a virtual env or whatever, but that's up to you. Just know Mido is required.

## File Structure
All the Python code is in the `convert` and `compress` directories, and `plasmidi.py`.

The Lua code for the PlasMIDI jukebox device is in the `lua` directory. It's not necessary to run the python script, but is included in case you want to fiddle around with it.

## Getting Started

To get started, you can display the help text for the script, which will show all the options aviailable to you.
```
python3 plasmidi.py --help
```

Once you're ready to convert a MIDI file, choose your input and (optional) output, and what track(s) and field(s) you want to output. If you don't select a track, all tracks will go to the output. Likewise with fields. If no output file is chosen, the output will just print to the screen.

**Note:** The output is *always* a valid JSON-encoded object of the form:
```json
[
	{
		"num" = 1,
		"name" = "MIDI Track Name",
		"notes" = [
			"note1",
			"note2",
			...
		],
		"instruments" = [
			"Keys",
			"Pads",
			...
		],
		"notes_compressed" = "Some base85-encoded string"
	},
	{ ... },
	{ ... },
	etc...
]
```

In most cases, you will only want the final track with all of the instruments combined. In that case, just append `--track ALL` to the command. Additionally, I find that I usually only want the instruments and compressed notes. In that case, just append `--field instruments notes_compressed` to the command. This will look like the following:

```
python3 plasmidi.py YOUR_MIDI_FILE.mid --track ALL --field notes_compressed instruments
```

## Copying output to Plasma
Copying data to Plasma is very simple: just copy and paste the field contents into the respective fields in the PlasMIDI jukebox!
- `"notes" = [ ... ]`: copy everything in the brackets, including the brackets themselves.
- `"instruments = [ ... ]`: copy everything in the brackets, including the brackets themselves.
- `"notes_compressed = "..."`: copy everything in the quotes, **NOT including** the quotes themselves.
- `"num" = ...`: not needed.
- `"name" = ...`: not needed.

**Note:** while you *can* copy both the notes and notes_compressed fields into the same jukebox, this is redundant and unneccessary; the jukebox will favor compressed notes over uncompressed and will not use both at the same time.

## Which field do I use? "notes" versus "notes_compressed"
Both of these fields contain the exact same data, but the compressed notes are in a format that is easier to just paste into Plasma devices. As your MIDI songs get very long, using the uncompressed notes can make Plasma lag a LOT when you paste them into a device! Compare that to the compressed notes, which don't lag at all when you paste them. The one (very minor) tradeoff of using the compressed notes is that the jukebox has to decompress it before being able to play the song, which may take a few game cycles depending on how much data there is. Happily, that's still not noticeable from a human perspective.

I highly recommend using the compressed notes, and just ignoring the uncompressed ones... unless you want to poke around at the data format! in which case have at it :)

---

## Thank You!

Thanks for the continued attention to this little project! This was a lot of fun to put together. We're both thrilled that people still use it, and love seeing creations that implement and build upon it.

Feel free to remix and reuse any of the code in this project as you see fit!
