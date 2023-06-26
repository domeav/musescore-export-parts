#!/usr/bin/env python

import sys
import json
import base64
import subprocess
import argparse
import re

# Inspired from https://musescore.org/en/node/287888

parser = argparse.ArgumentParser(
    description="create PDF parts for C, Bb, Eb instruments"
)
parser.add_argument("musescore_file", type=str)
args = parser.parse_args()

MUSE_APP = "/home/dom/Apps/MuseScore-3.6.2.548021370-x86_64.AppImage"

keys = ("C", "Bb", "Eb")
CLEF_TABLE = ['15mb', '8vb', '', '8va', '15ma']


print("\n### Creating output folders")
subprocess.run(["mkdir", "-p", *keys])

print("\n### Transposing conductors...")
for key in keys:
    if key == "C":
        subprocess.run(["cp", args.musescore_file, "C/tmp_conductor.mscz"], capture_output=False)
        continue
    elif key == "Bb":
        transposeConfig = '{"mode": "by_interval", "direction": "up", "transposeInterval": 4, "transposeKeySignatures": true}'
    elif key == "Eb":
        transposeConfig = '{"mode": "by_interval", "direction": "down", "transposeInterval": 7, "transposeKeySignatures": true}'
    else:
        raise Exception(f"Unknown key [{key}]?!?")
    out = subprocess.run(
        [MUSE_APP, args.musescore_file, "--score-transpose", transposeConfig],
        capture_output=True,
    )    
    content = json.loads(out.stdout)["mscz"]
    with open(f"{key}/tmp_conductor.mscz", "wb") as outfile:
        outfile.write(base64.b64decode(content))

print("\n### Generating conductors scores...")
for key in keys:
    subprocess.run(
        [MUSE_APP, f"{key}/tmp_conductor.mscz", "-o", f"{key}/conductor.pdf"],
        capture_output=False,
   )

def _generate_pdf(contents, target_file, key):
    'Generate normal and pocket pdfs from in-memory mscx'
    with open(f"tmp.mscx", "w") as outfile:
            outfile.write(mscx_contents)
    subprocess.run(
        [MUSE_APP, "tmp.mscx", "-o", f'{target_file}.pdf', "-p", f"tag_{key}.qml"],
        capture_output=False,
    )
    # pocket version
    pocket_mscx = re.sub('<Spatium>[^<]+</Spatium>', '<Spatium>2.9</Spatium>', mscx_contents)
    with open(f"tmp.mscx", "w") as outfile:
            outfile.write(pocket_mscx)
    subprocess.run(
        [MUSE_APP, "tmp.mscx", "-o", f'{target_file}_pocket.pdf', "-p", f"tag_{key}.qml"],
        capture_output=False,
    )

    
print("Fetching parts...")
for key in keys:
    out = subprocess.run(
        [MUSE_APP, f"{key}/tmp_conductor.mscz", "--score-parts"], capture_output=True
    )
    print(out.stderr.decode("utf-8"))
    result = json.loads(out.stdout)
    for part, content in zip(result["parts"], result["partsBin"]):
        part = part.replace(" ", "_")
        with open(f"{key}/tmp_{part}.mscz", "wb") as outfile:
            outfile.write(base64.b64decode(content))
        out = subprocess.run(
            ["unzip", "-p", f"{key}/tmp_{part}.mscz", "*.msc*"], capture_output=True
        )
        mscx_contents = out.stdout.decode("utf-8")
        m = re.search('<transposingClefType>([^<]+)</transposingClefType>', mscx_contents)
        if m:
            clef, qualifier = m.group(1)[0], m.group(1)[1:]
        elif part.lower().startswith('bass'):
            clef = 'F'
        else:
            clef = 'G'
        clef_qualifier_index = CLEF_TABLE.index(clef[1:])
        _generate_pdf(mscx_contents, f"{key}/{part}_{clef}", key)
        # switch clef
        if clef == 'F':
            transposing_clef = 'G'
            target_qualifier_index = -2 if key == 'Eb' else -1
            target_qualifier_index += clef_qualifier_index
        elif clef == 'G':
            transposing_clef = 'F'
            target_qualifier_index = clef_qualifier_index + 1
        if "transposingClefType" in mscx_contents:
            mscx_contents = mscx_contents.replace(
                f"<transposingClefType>{clef}{qualifier}</transposingClefType>",
                f"<transposingClefType>{transposing_clef}{CLEF_TABLE[target_qualifier_index]}</transposingClefType>")
        else:
            mscx_contents = mscx_contents.replace(
                "<voice>",
                f"<voice><Clef><concertClefType>{clef}</concertClefType><transposingClefType>{transposing_clef}{CLEF_TABLE[target_qualifier_index]}</transposingClefType></Clef>",
                1)
        _generate_pdf(mscx_contents, f"{key}/{part}_{transposing_clef}", key)


for key in keys:
    subprocess.run(f"rm {key}/tmp_*", shell=True)
subprocess.run(f"rm tmp.mscx", shell=True)
