#!/usr/bin/env python

import sys
import json
import base64
import subprocess
import argparse

# Inspired from https://musescore.org/en/node/287888

parser = argparse.ArgumentParser(description="create PDF parts for C, Bb, Eb instruments")
parser.add_argument('musescore_file', type=str)
args = parser.parse_args()

MUSE_APP = '/home/dom/Apps/MuseScore-3.6.2.548021370-x86_64.AppImage'

print('Creating output folders')
subprocess.run(['mkdir', '-p', 'C', 'Bb', 'Eb'])

print('Executing MuseScore...')
out = subprocess.run([MUSE_APP, args.musescore_file, '--score-parts'], capture_output=True)
print(out.stderr.decode('utf-8'))
result = json.loads(out.stdout)
for part, content in zip(result['parts'], result['partsBin']):
    # C
    filepath_C = f"C/{ part.replace(' ', '_') }_C.mscz"
    with open(filepath_C, 'wb') as outfile:
        print('Writing', filepath_C)
        outfile.write(base64.b64decode(content))
    filepath_C_pdf = f"C/{ part.replace(' ', '_') }_C.pdf"
    subprocess.run([MUSE_APP, filepath_C, '-o', filepath_C_pdf], capture_output=False)    

    # Bb
    transposeConfig = '{"mode": "by_interval", "direction": "up", "transposeInterval": 4, "transposeKeySignatures": true}'
    out = subprocess.run([MUSE_APP, filepath_C, '--score-transpose', transposeConfig], capture_output=True)
    content = json.loads(out.stdout)['mscz']
    filepath_Bb = f"Bb/{ part.replace(' ', '_') }_Bb.mscz"
    with open(filepath_Bb, 'wb') as outfile:
        print('Writing', filepath_Bb)
        outfile.write(base64.b64decode(content))
    filepath_Bb_pdf = f"Bb/{ part.replace(' ', '_') }_Bb.pdf"
    subprocess.run([MUSE_APP, filepath_Bb, '-o', filepath_Bb_pdf, '-p', 'tag_Bb.qml'], capture_output=False)

    # Eb
    transposeConfig = '{"mode": "by_interval", "direction": "down", "transposeInterval": 7, "transposeKeySignatures": true}'
    out = subprocess.run([MUSE_APP, filepath_C, '--score-transpose', transposeConfig], capture_output=True)
    content = json.loads(out.stdout)['mscz']
    filepath_Eb = f"Eb/{ part.replace(' ', '_') }_Eb.mscz"
    with open(filepath_Eb, 'wb') as outfile:
        print('Writing', filepath_Eb)
        outfile.write(base64.b64decode(content))
    filepath_Eb_pdf = f"Eb/{ part.replace(' ', '_') }_Eb.pdf"
    subprocess.run([MUSE_APP, filepath_Eb, '-o', filepath_Eb_pdf, '-p', 'tag_Eb.qml'], capture_output=False)
    
    subprocess.run(['rm', filepath_C, filepath_Bb, filepath_Eb])
