#!/usr/bin/env python3


import argparse
from MuseScoreWrapper import MuseScoreWrapper
import os
import concurrent.futures


# Inspired from https://musescore.org/en/node/287888

parser = argparse.ArgumentParser(
    description="create PDF parts for C, Bb, Eb instruments"
)
parser.add_argument("musescore_file", type=str)
args = parser.parse_args()

conductors = {}
conductors["C"] = MuseScoreWrapper(args.musescore_file, clef=None, key="C")
conductors["Bb"] = conductors["C"].transpose("Bb")
conductors["Eb"] = conductors["C"].transpose("Eb")
with concurrent.futures.ThreadPoolExecutor(max_workers=8) as executor:
    for key in conductors.keys():
        try:
            os.mkdir(key)
        except FileExistsError:
            pass
        conductors[key].set_title(conductors[key].title + f" ({key})")
        parts = conductors[key].generate_parts()
        for part, msw in parts.items():
            executor.submit(msw.generate_pdf, f"{key}/{part[0]}_{part[1]}.pdf")
        executor.submit(conductors[key].generate_pdf, f"{key}/conductor.pdf")
