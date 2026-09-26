from pathlib import Path
import hashlib
import json
import zipfile

base = Path(__file__).resolve().parent
fab = base / 'fab'
archive = base / 'odometry-v2-2026-09-25-NOT_RELEASED.zip'
files = {p.name: p.read_bytes() for p in fab.iterdir() if p.is_file()}
assert len(files) == 14, sorted(files)
with zipfile.ZipFile(archive, 'x', zipfile.ZIP_DEFLATED) as z:
    for name in sorted(files):
        z.writestr(name, files[name])

with zipfile.ZipFile(archive) as z:
    assert set(z.namelist()) == set(files)
    assert all(z.read(name) == content for name, content in files.items())

job = json.loads(files['Oddom board-job.gbrjob'])
assert job['GeneralSpecs']['LayerNumber'] == 4
gerbers = {name for name in files if name.endswith(('.gtl', '.g1', '.g2', '.gbl', '.gtp', '.gbp', '.gts', '.gbs', '.gto', '.gbo', '.gm1'))}
assert {row['Path'] for row in job['FilesAttributes']} == gerbers
assert b'%TF.FileFunction,Profile,NP*%' in files['Oddom board-Edge_Cuts.gm1']
assert b'M02*' in files['Oddom board-Edge_Cuts.gm1']
assert b'TF.FileFunction,Plated,1,4,PTH' in files['Oddom board-PTH.drl']
assert b'TF.FileFunction,NonPlated,1,4,NPTH' in files['Oddom board-NPTH.drl']
assert set(files) == gerbers | {'Oddom board-job.gbrjob', 'Oddom board-PTH.drl', 'Oddom board-NPTH.drl'}
print('Archive files:', len(files))
print('Gerbers:', len(gerbers))
print('Job board size:', job['GeneralSpecs']['Size'])
print('Archive SHA256:', hashlib.sha256(archive.read_bytes()).hexdigest())
