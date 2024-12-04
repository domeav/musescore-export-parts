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
    "Eb": '{"mode": "by_interval", "direction": "down", "transposeInterval": 7, "transposeKeySignatures": true}',
}


class MuseScoreWrapper:
    # clef must be None for conductor scores
    def __init__(self, mscz_path, clef, key):
        self.clef = clef
        self.key = key
        if mscz_path:
            self.tmp_dir = TemporaryDirectory(delete=True)
            self.tmp_path = Path(self.tmp_dir.name)
            with zipfile.ZipFile(mscz_path, "r") as mscz:
                mscx_filenames = [f for f in mscz.namelist() if f.endswith(".mscx")]
                mscz.extractall(self.tmp_path)
        assert len(mscx_filenames) == 1
        self.mscx_name = mscx_filenames[0]
        self.mscx_path = self.tmp_path / self.mscx_name
        self.mscx = ET.parse(self.mscx_path)
        self.title = self.mscx.find("./Score/Staff/VBox/Text/text").text
        self._sanitize()

    def _sanitize(self):
        for part in self.mscx.findall("./Score/Part"):
            partName = part.find("./Instrument/longName").text
            part.find("./trackName").text = partName
            part.find("./Instrument/trackName").text = partName
        self.mscx.write(self.mscx_path)

    def _generate_mscz(self, tmp_out):
        out_path = Path(tmp_out.name)
        tmp_filename = str(uuid.uuid4())
        shutil.make_archive(out_path / tmp_filename, "zip", self.tmp_path)
        shutil.move(out_path / f"{tmp_filename}.zip", out_path / f"{tmp_filename}.mscz")
        return out_path / f"{tmp_filename}.mscz"

    def generate_pdf(self, pdf_path):
        print(f"Generating {pdf_path}")
        tmp_out = TemporaryDirectory(delete=True)
        mscz_path = self._generate_mscz(tmp_out)
        subprocess.run([MUSE_APP, mscz_path, "-o", pdf_path], capture_output=True)

    def set_title(self, title):
        self.mscx.find("./Score/Staff/VBox/Text/text").text = title
        self.mscx.write(self.mscx_path)
        self.title = title

    def transpose(self, key):
        tmp_out = TemporaryDirectory(delete=True)
        mscz_path = self._generate_mscz(tmp_out)
        out = subprocess.run(
            [MUSE_APP, mscz_path, "--score-transpose", TRANSPOSITIONS[key]],
            capture_output=True,
        )
        content = base64.b64decode(json.loads(out.stdout)["mscz"])
        return MuseScoreWrapper(io.BytesIO(content), clef=self.clef, key=key)

    def _switch_clef(self):
        CLEF_TABLE = ["15mb", "8vb", "", "8va", "15ma"]
        if not self.clef:
            raise ValueException
        target_clef = "F" if self.clef == "G" else "G"
        if target_clef == "G":
            clef_qualifier_index = 1
        elif target_clef == "F":
            clef_qualifier_index = -2 if self.key == "Eb" else -1
        tmp_out = TemporaryDirectory(delete=True)
        mscz_path = self._generate_mscz(tmp_out)
        switched_part = MuseScoreWrapper(mscz_path, clef=target_clef, key=self.key)
        clefInfo = switched_part.mscx.find("./Score/Staff/Measure/voice/Clef")
        parent = switched_part.mscx.find("./Score/Staff/Measure/voice")
        if clefInfo:
            parent.remove(clefInfo)
        parent.insert(
            0,
            ET.XML(
                f"""
        <Clef>
            <concertClefType>{target_clef}</concertClefType>
            <transposingClefType>{target_clef}{CLEF_TABLE[clef_qualifier_index]}</transposingClefType>
            <isHeader>1</isHeader>
        </Clef>
        """
            ),
        )
        switched_part.mscx.write(switched_part.mscx_path)
        return switched_part

    def generate_parts(self):
        print(f"Generating parts for {self.title}")
        tmp_out = TemporaryDirectory(delete=True)
        mscz_path = self._generate_mscz(tmp_out)
        out = subprocess.run(
            [MUSE_APP, mscz_path, "--score-parts"], capture_output=True
        )
        result = json.loads(out.stdout)
        parts = {}
        for part, content in zip(result["parts"], result["partsBin"]):
            part = part.replace(" ", "_")
            clef = ("G", "F")
            if part.lower().startswith("bass"):
                clef = ("F", "G")
            parts[(part, clef[0])] = MuseScoreWrapper(
                io.BytesIO(base64.b64decode(content)), clef=clef[0], key=self.key
            )
            parts[(part, clef[1])] = parts[(part, clef[0])]._switch_clef()
        return parts
