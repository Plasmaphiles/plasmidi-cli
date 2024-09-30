#!/usr/bin/env python3

import mido
import sys
import json
import argparse
from convert import Song
from compress import compress

#Verify that command-line arguments are valid.
#If this fails, main() will not run.
def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        prog = 'PlasMIDI',
        description = 'Convert a MIDI file to a format that\'s easy to parse in Plasma.',
    )
    parser.add_argument('input', help = 'The input file. Must be a valid MIDI file.')
    parser.add_argument('output', nargs='?', help = 'The output file. If not specified, prints to stdout. Output is always a valid JSON string.')
    parser.add_argument('--track', nargs='*', action = 'store', default = [], help = 'The number or name of the track(s) to output. "-1" or "ALL" is all tracks combined into a single track. If not specified, all tracks are output separately.')
    parser.add_argument('--field', nargs='*', choices = ['num', 'name', 'notes', 'instruments', 'notes_compressed'], help = 'The field to output. If not specified, all fields are included.')

    args = parser.parse_args()

    return args

def main(args: argparse.Namespace) -> None:
    midi = mido.MidiFile(args.input)
    song = Song(midi)
    notes = song.process()

    #Keep only the tracks that the user has specified that they want.
    if len(args.track):
        tmp = []
        for track in notes:
            if str(track['num']) in args.track or track['name'] in args.track:
                tmp += [track]
        notes = tmp

    #Only generate compressed output if we need to. If user doesn't want it, don't bother.
    if args.field is None or 'notes_compressed' in args.field:
        for i, _ in enumerate(notes):
            notes[i]['notes_compressed'] = compress(notes[i]['notes'])

    #Keep only the fields that the user has specified that they want.
    if args.field is not None:
        for track in notes:
            for field in [i for i in track]:
                if field not in args.field:
                    del track[field]

    #Send result to output
    output_text = json.dumps(notes, indent = 2)
    if args.output is None:
        print(output_text)
    else:
        with open(args.output, 'w') as fp:
            fp.write(output_text)

if __name__ == '__main__':
    main(parse_args())
