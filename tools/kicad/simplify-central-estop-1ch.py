"""One-off change of the manually edited placement project to one E-stop channel."""
from pathlib import Path
import copy, importlib.util, json, shutil, uuid

spec = importlib.util.spec_from_file_location('g', Path(__file__).with_name('generate-central-placement.py'))
g = importlib.util.module_from_spec(spec); spec.loader.exec_module(g)
root = g.ROOT
project = root / 'hardware/central-board-placement'
out = root / 'output/kicad-check/central-estop-1ch-2026-09-26'
backup = out / 'before'; backup.mkdir(parents=True, exist_ok=True)
removed = {f'R{i}' for i in range(403,409)} | {'R410','R411','R412','D402','D403','D404','TP402','TP403','TP404','TP405'}
def props(s): return {json.loads(p[1]):p for p in g.children(s,'property')}
def ref(s): return json.loads(props(s)['Reference'][2])
def save(p,a): p.write_text(g.dump(a)+'\n',encoding='utf-8')
path = project/'S04_safety-1.kicad_sch'
original = path.read_bytes(); a=g.parse(original.decode('utf-8-sig'))
assert not g.children(a,'wire'), 'User has wired this sheet; review before changing'
assert sum(ref(s)=='U401' for s in g.children(a,'symbol'))==4, 'Already simplified'
for p in [*project.glob('*.kicad_sch'),root/'tools/kicad/central-placement-parts.json',project/'placement-manifest.json']:
    shutil.copy2(p,backup/p.name)
libs=g.Libraries()
opt=libs.get('Isolator:LTV-817S'); conn=libs.get('Connector_Generic:Conn_01x04')
cache=g.first(a,'lib_symbols')
cache[:]=[x for x in cache if not (isinstance(x,list) and x[0]=='symbol' and json.loads(x[1]) in ['Isolator:LTV-847S','Connector_Generic:Conn_01x06'])]
cache.extend([opt,conn])
deleted_positions=[]
for s in list(g.children(a,'symbol')):
    r=ref(s)
    if r in removed or (r=='U401' and g.first(s,'unit')[1]!='1'):
        deleted_positions.append(tuple(float(x) for x in g.first(s,'at')[1:3]));a.remove(s);continue
    if r=='U401':
        g.first(s,'lib_id')[1]=g.q('Isolator:LTV-817S')
        props(s)['Value'][2]=g.q('LTV-817S')
        props(s)['Footprint'][2]=g.q('Package_DIP:SMDIP-4_W9.53mm')
        for pin in g.children(s,'pin'):
            pin[1]=g.q({'16':'4','15':'3'}.get(json.loads(pin[1]),json.loads(pin[1])))
        for p in g.children(s,'property'):
            if json.loads(p[1]) in ['Placement_Note','Placement_Status']:
                p[2]=g.q('Loop monitoring only; A1 K2 E3 C4; footprint candidate, confirm purchased part')
    if r=='J401':
        g.first(s,'lib_id')[1]=g.q('Connector_Generic:Conn_01x04')
        props(s)['Value'][2]=g.q('TBD 4pin ESTOP_CTRL')
        props(s)['Footprint'][2]=g.q('')
        for pin in list(g.children(s,'pin')):
            if int(json.loads(pin[1]))>4:s.remove(pin)
        for p in g.children(s,'property'):
            if json.loads(p[1])=='Placement_Note':p[2]=g.q('1=LOOP_OUT 2=LOOP_RETURN 3=LED_24V 4=GND_CTRL_LED; connector MPN pending')
for t in list(g.children(a,'text')):
    at=g.first(t,'at');x,y=map(float,at[1:3]);v=json.loads(t[1])
    if v in ['REVIEW','Footprint TBD'] and any(abs(x-px)<12 and abs(y-py)<18 for px,py in deleted_positions):a.remove(t)
a.append(g.text('E-stop: ONE loop-monitor channel (U401 LTV-817S). No individual button / spare inputs.\nJ401: 1 LOOP_OUT, 2 LOOP_RETURN, 3 LED_24V, 4 GND_CTRL_LED. J402: coil +/- only.\nHard NC series interruption remains; monitoring is diagnostic only. Parts remain unwired.',55,300,1.6))
assert path.read_bytes()==original, 'Changed since read'
save(path,a)
# Keep the old per-button GPIO assignments reserved instead of using them for new functions.
for p in [project/'S02B_star_teensy-1.kicad_sch',project/'CentralPlacement.kicad_sym']:
    txt=p.read_text(encoding='utf-8-sig')
    txt=txt.replace('ESTOP1_AUX_OK_N','RESERVED_ESTOP1').replace('ESTOP2_AUX_OK_N','RESERVED_ESTOP2')
    p.write_text(txt,encoding='utf-8')
parts_path=root/'tools/kicad/central-placement-parts.json'
data=json.loads(parts_path.read_text(encoding='utf-8-sig'))
manifest=json.loads((project/'placement-manifest.json').read_text(encoding='utf-8-sig'))
for group in data['sheets']:
    group['parts']=[p for p in group['parts'] if p['ref'] not in removed]
    for p in group['parts']:
        if p['ref']=='U401':p.update(value='LTV-817S',lib_id='Isolator:LTV-817S',footprint='Package_DIP:SMDIP-4_W9.53mm',units=[1],note='Loop only; A1 K2 E3 C4; confirm footprint against purchased part')
        if p['ref']=='J401':p.update(value='TBD 4pin ESTOP_CTRL',lib_id='Connector_Generic:Conn_01x04',footprint='',status='unresolved',note='1=LOOP_OUT 2=LOOP_RETURN 3=LED_24V 4=GND_CTRL_LED; MPN pending')
manifest=[p for p in manifest if p['ref'] not in removed]
byref={p['ref']:p for group in data['sheets'] for p in group['parts']}
for p in manifest:
    if p['ref'] in ['U401','J401']:
        for k in ['value','lib_id','footprint','note']:p[k]=byref[p['ref']][k]
for p,obj in [(parts_path,data),(project/'placement-manifest.json',manifest)]:p.write_text(json.dumps(obj,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print('Removed',len(removed),'physical parts; retained U401 single unit and 4-pin J401')
