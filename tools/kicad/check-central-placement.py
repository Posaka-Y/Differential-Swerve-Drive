"""Read-only audit of the generated placement and KiCad-exported netlist."""
import importlib.util
import argparse
import json
import re
from collections import Counter
from pathlib import Path

SPEC=importlib.util.spec_from_file_location('placement',Path(__file__).with_name('generate-central-placement.py'))
g=importlib.util.module_from_spec(SPEC); SPEC.loader.exec_module(g)
ap=argparse.ArgumentParser()
ap.add_argument('--output',type=Path,default=g.ROOT/'output/kicad-check/central-placement')
ap.add_argument('--erc-name',default='placement-erc.rpt')
args=ap.parse_args()
out=args.output
dest=g.ROOT/'hardware/central-board-placement'
inventory=json.loads((g.ROOT/'tools/kicad/central-placement-parts.json').read_text(encoding='utf-8-sig'))
parts={p['ref']:p for s in inventory['sheets'] for p in s['parts']}
net=g.parse((out/'placement.net').read_text(encoding='utf-8-sig'))
components=g.children(g.first(net,'components'),'comp')
assert {json.loads(g.first(c,'ref')[1]) for c in components} == set(parts)
assert len(components)==len(parts)
shared=[]
for n in g.children(g.first(net,'nets'),'net'):
    if len(g.children(n,'node'))>1: shared.append(n)
assert not shared, 'Unexpected connected component pins'
trees=[g.parse(p.read_text(encoding='utf-8-sig')) for p in dest.glob('*.kicad_sch')]
symbols=[s for t in trees for s in g.children(t,'symbol')]
assert len(symbols)==len(parts)+3  # U401 has four units.
unitpairs=[]
for s in symbols:
    props={json.loads(p[1]):json.loads(p[2]) for p in g.children(s,'property')}
    unitpairs.append((props['Reference'],g.first(s,'unit')[1]))
assert len(unitpairs)==len(set(unitpairs))
assert sorted(u for ref,u in unitpairs if ref=='U401')==['1','2','3','4']
custom=g.parse((dest/'CentralPlacement.kicad_sym').read_text(encoding='utf-8-sig'))
customs={json.loads(s[1]):s for s in g.children(custom,'symbol')}
for p in parts.values():
    if not p.get('custom_pins'): continue
    s=customs[p['lib_id'].split(':')[1]]
    pins={json.loads(g.first(n,'number')[1]):json.loads(g.first(n,'name')[1]) for n in g.walk(s) if n and n[0]=='pin'}
    assert pins=={str(p['number']):p['name'] for p in p['custom_pins']}
teensy=parts['J210']
mapping=json.loads((g.ROOT/'tools/kicad/central-teensy-pinmap.json').read_text(encoding='utf-8-sig'))
assert {int(p['number']) for p in teensy['custom_pins']}=={p['pad'] for p in mapping['pins']}
# Check graphical order independently from the electrical number/name mapping.
socket=customs['Teensy41_Socket']
socketpins=[n for n in g.walk(socket) if n and n[0]=='pin']
left=sorted((n for n in socketpins if float(g.first(n,'at')[1])<0),key=lambda n:-float(g.first(n,'at')[2]))
right=sorted((n for n in socketpins if float(g.first(n,'at')[1])>0),key=lambda n:-float(g.first(n,'at')[2]))
assert [int(json.loads(g.first(n,'number')[1])) for n in left]==list(range(1,25))
assert [int(json.loads(g.first(n,'number')[1])) for n in right]==list(range(48,24,-1))
embedded=next(s for t in trees for s in g.children(g.first(t,'lib_symbols'),'symbol') if json.loads(s[1])=='CentralPlacement:Teensy41_Socket')
def pin_geometry(symbol):
    return {json.loads(g.first(n,'number')[1]): (json.loads(g.first(n,'name')[1]),tuple(g.first(n,'at')[1:]))
            for n in g.walk(symbol) if n and n[0]=='pin'}
assert pin_geometry(embedded)==pin_geometry(socket), 'Cached Teensy pin geometry differs from library'
fp=g.parse((g.ROOT/'hardware/lib/DifferentialSwerve.pretty/Teensy41_Socket_2x24.kicad_mod').read_text(encoding='utf-8-sig'))
assert {int(json.loads(p[1])) for p in g.children(fp,'pad')}==set(range(1,49))
missing=[]
for ref,p in parts.items():
    if not p.get('footprint'): continue
    lib,name=p['footprint'].split(':')
    folder=g.ROOT/'hardware/lib/DifferentialSwerve.pretty' if lib=='DifferentialSwerve' else g.STD.parent/'footprints'/(lib+'.pretty')
    if not (folder/(name+'.kicad_mod')).exists(): missing.append((ref,p['footprint']))
assert not missing, missing
erc=Counter(re.findall(r'^\[([^]]+)\]',(out/args.erc_name).read_text(encoding='utf-8-sig'),re.M))
assert set(erc) <= {'pin_not_connected','pin_not_driven','power_pin_not_driven'},erc
report={'physical_parts':len(parts),'symbol_units':len(symbols),'schematic_sheets':len(trees),'shared_nets':0,'duplicate_reference_unit_pairs':0,'custom_pinmaps':'match input inventory','teensy_pad_set':'1..48 matches dedicated footprint','assigned_footprints':'all exist','erc_expected_only':dict(erc)}
(out/'placement-audit.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
print(json.dumps(report,indent=2))
