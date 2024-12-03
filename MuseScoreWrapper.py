from tempfile import TemporaryDirectory
from pathlib import Path
import shutil
import subprocess
import zipfile
import xml.etree.ElementTree as ET
import base64
import json
import io
import uuid

MUSE_APP = "/home/dom/Apps/MuseScore-Studio-Nightly-latest-master-x86_64.AppImage"

TRANSPOSITIONS = {
    "C": None,
    "Bb": '{"mode": "by_interval", "direction": "up", "transposeInterval": 4, "transposeKeySignatures": true}',
    "Eb": '{"mode": "by_interval", "direction": "down", "transposeInterval": 7, "transposeKeySignatures": true}'
}

CLEF_TABLE = ['15mb', '8vb', '', '8va', '15ma']


class MuseScoreWrapper():
    def __init__(self, mscz_path):
        if mscz_path:
            self.tmp_dir = TemporaryDirectory(delete=True)
            self.tmp_path = Path(self.tmp_dir.name)
            with zipfile.ZipFile(mscz_path, 'r') as mscz:
                mscx_filenames = [f for f in mscz.namelist() if f.endswith('.mscx')]
                mscz.extractall(self.tmp_path)
        assert(len(mscx_filenames) == 1)
        self.mscx_name = mscx_filenames[0]
        self.mscx_path = self.tmp_path / self.mscx_name
        self.mscx = ET.parse(self.mscx_path)
        self.title = self.mscx.find('./Score/Staff/VBox/Text/text').text
        self._sanitize()

    def _sanitize(self):
        for part in self.mscx.findall('./Score/Part'):
            partName = part.find('./Instrument/longName').text
            part.find('./trackName').text = partName
            part.find('./Instrument/trackName').text = partName
        self.mscx.write(self.mscx_path)
    def _generate_mscz(self, tmp_out):
        out_path = Path(tmp_out.name)
        tmp_filename = str(uuid.uuid4())
        shutil.make_archive(out_path / tmp_filename, 'zip', self.tmp_path)
        shutil.move(out_path / f'{tmp_filename}.zip', out_path / f'{tmp_filename}.mscz')
        return out_path / f'{tmp_filename}.mscz'
    def generate_pdf(self, pdf_path):
        tmp_out = TemporaryDirectory(delete=True)
        mscz_path = self._generate_mscz(tmp_out)
        subprocess.run(
            [MUSE_APP, mscz_path, "-o", pdf_path],
            capture_output=False
        )
    def set_title(self, title):
        self.mscx.find('./Score/Staff/VBox/Text/text').text = title
        self.mscx.write(self.mscx_path)
    def transpose(self, key):
        tmp_out = TemporaryDirectory(delete=True)
        mscz_path = self._generate_mscz(tmp_out)
        out = subprocess.run(
            [MUSE_APP,
             mscz_path,
             "--score-transpose",
             TRANSPOSITIONS[key]],
            capture_output=True,
        )
        content = base64.b64decode(json.loads(out.stdout)["mscz"])
        return MuseScoreWrapper(io.BytesIO(content))
        

