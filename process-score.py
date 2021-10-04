#!/usr/bin/env python

import sys
import json
import base64
import subprocess
import argparse

# Inspired from https://musescore.org/en/node/287888

parser = argparse.ArgumentParser(
    description="create PDF parts for C, Bb, Eb instruments"
)
parser.add_argument("musescore_file", type=str)
args = parser.parse_args()

MUSE_APP = "/home/dom/Apps/MuseScore-3.6.2.548021370-x86_64.AppImage"

keys = ("C", "Bb", "Eb")

print("Creating output folders")
subprocess.run(["mkdir", "-p", *keys])

print("Executing MuseScore...")
out = subprocess.run(
    [MUSE_APP, args.musescore_file, "--score-parts"], capture_output=True
)
print(out.stderr.decode("utf-8"))
result = json.loads(out.stdout)
for part, content in zip(result["parts"], result["partsBin"]):

    part = part.replace(" ", "_")
    filepath_C_mscz = f"C/tmp_{part}_C.mscz"
    with open(filepath_C_mscz, "wb") as outfile:
        print("Writing", filepath_C_mscz)
        outfile.write(base64.b64decode(content))

    for key in keys:
        if key == "C":
            filepath_mscz = filepath_C_mscz
        else:
            if key == "Bb":
                transposeConfig = '{"mode": "by_interval", "direction": "up", "transposeInterval": 4, "transposeKeySignatures": true}'
            elif key == "Eb":
                transposeConfig = '{"mode": "by_interval", "direction": "down", "transposeInterval": 7, "transposeKeySignatures": true}'
            else:
                raise Exception(f"Unknown key [{key}]?!?")
            out = subprocess.run(
                [MUSE_APP, filepath_C_mscz, "--score-transpose", transposeConfig],
                capture_output=True,
            )
            content = json.loads(out.stdout)["mscz"]
            filepath_mscz = f"{key}/tmp_{part}_{key}.mscz"
            with open(filepath_mscz, "wb") as outfile:
                print("Writing", filepath_mscz)
                outfile.write(base64.b64decode(content))

        # direct PDF
        filepath_direct = f"{key}/{part}_{key}.pdf"
        subprocess.run(
            [MUSE_APP, filepath_mscz, "-o", filepath_direct, "-p", f"tag_{key}.qml"],
            capture_output=False,
        )

        if part.lower().startswith("bass"):
            # treble Clef, for people who can't read bass key
            filepath_trebleClef = f"{key}/tmp_{part}_{key}_trebleClef.mscx"
            out = subprocess.run(
                ["unzip", "-p", filepath_mscz, "*.msc*"], capture_output=True
            )
            treble_file = out.stdout.decode("utf-8")
            if key == "Eb":
                transposingClefType = "G15mb"
            else:
                transposingClefType = "G8vb"
            if "transposingClefType" in treble_file:
                treble_file = treble_file.replace(
                    "<transposingClefType>F</transposingClefType>",
                    f"<transposingClefType>{transposingClefType}</transposingClefType>",
                )
            else:
                treble_file = treble_file.replace(
                    "<voice>",
                    f"<voice><Clef><concertClefType>F</concertClefType><transposingClefType>{transposingClefType}</transposingClefType></Clef>",
                    1,
                )
            with open(filepath_trebleClef, "w") as outfile:
                print("Writing", filepath_trebleClef)
                outfile.write(treble_file)
            filepath_trebleClef_pdf = f"{key}/{part}_{key}_trebleClef.pdf"
            subprocess.run(
                [
                    MUSE_APP,
                    filepath_trebleClef,
                    "-o",
                    filepath_trebleClef_pdf,
                    f"tag_{key}.qml",
                ],
                capture_output=False,
            )

        else:
            # bass Clef, for trombone
            filepath_bassClef = f"{key}/tmp_{part}_{key}_bassClef.mscx"
            out = subprocess.run(
                ["unzip", "-p", filepath_mscz, "*.msc*"], capture_output=True
            )
            bass_file = out.stdout.decode("utf-8")
            if "transposingClefType" in bass_file:
                bass_file = bass_file.replace(
                    "<transposingClefType>G</transposingClefType>",
                    f"<transposingClefType>F15ma</transposingClefType>",
                )
            else:
                bass_file = bass_file.replace(
                    "<voice>",
                    f"<voice><Clef><concertClefType>G</concertClefType><transposingClefType>F15ma</transposingClefType></Clef>",
                    1,
                )
            with open(filepath_bassClef, "w") as outfile:
                print("Writing", filepath_bassClef)
                outfile.write(bass_file)
            filepath_bassClef_pdf = f"{key}/{part}_{key}_bassClef.pdf"
            subprocess.run(
                [
                    MUSE_APP,
                    filepath_bassClef,
                    "-o",
                    filepath_bassClef_pdf,
                    f"tag_{key}.qml",
                ],
                capture_output=False,
            )

    for key in keys:
        subprocess.run(f"rm {key}/tmp_*", shell=True)
