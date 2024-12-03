#!/usr/bin/env python3


import argparse
from MuseScoreWrapper import MuseScoreWrapper
import os


# Inspired from https://musescore.org/en/node/287888

parser = argparse.ArgumentParser(
    description="create PDF parts for C, Bb, Eb instruments"
)
parser.add_argument("musescore_file", type=str)
args = parser.parse_args()

conductors = {}
conductors['C'] = MuseScoreWrapper(args.musescore_file)
conductors['Bb'] = conductors['C'].transpose('Bb')
conductors['Eb'] = conductors['C'].transpose('Eb')
for key in conductors:
    os.mkdir(key)
    conductors[key].set_title(conductors[key].title + f' ({key})')
    conductors[key].generate_pdf(f'{key}/conductor.pdf')
