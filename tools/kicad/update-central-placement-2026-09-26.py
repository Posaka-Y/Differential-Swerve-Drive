"""Apply the documented September 26 additions without regenerating user placement."""
import copy
import importlib.util
import json
import re
import shutil
from pathlib import Path

spec = importlib.util.spec_from_file_location('g', Path(__file__).with_name('generate-central-placement.py'))
g = importlib.util.module_from_spec(spec)
spec.loader.exec_module(g)
dest = g.ROOT / 'hardware/central-board-placement'
backup = g.ROOT / 'output/kicad-check/central-placement-2026-09-26/before'
backup.mkdir(parents=True, exist_ok=True)

def spans(raw):
    depth = 0
    start = None
    for m in re.finditer(r'"(?:\\.|[^"\\])*"|[()]|[^\s()]+', raw):
        if m[0] == '(':
            if depth == 1: start = m.start()
            depth += 1
        elif m[0] == ')':
            depth -= 1
            if depth == 1: yield start, m.end(), g.parse(raw[start:m.end()])

inventory_path = g.ROOT / 'tools/kicad/central-placement-parts.json'
inventory = json.loads(inventory_path.read_text(encoding='utf-8-sig'))
parts = {p['ref']: p for s in inventory['sheets'] for p in s['parts']}
added = []
u = copy.deepcopy(parts['U101'])
u.update(ref='U102', value='TPS259470ARPWR', lib_id='CentralPlacement:TPS259470ARPWR', datasheet='https://www.ti.com/lit/ds/symlink/tps25947.pdf', note='USB eFuse auto-retry. IN5=TEENSY_VUSB; OUT6=+5V_SYS; EN1=R108/R109; OVLO2=R110/R111 (+5V_RAW priority); FLT4=R112/TP106/Teensy pad11 (proposal); DVDT7=C108; GND8=GND_CTRL; ILM9=R107; AUXOFF3/ITIMER10=NC when wired. RPW footprint remains unresolved.')
added.append(u)
for ref, value, note in [
    ('R107','3.32k 1%','USB_EFUSE_ILM to GND_CTRL; ILIM 0.85/1.007/1.15A'),
    ('R108','232k 1%','TEENSY_VUSB to USB_EFUSE_EN'),
    ('R109','100k 1%','USB_EFUSE_EN to GND_CTRL'),
    ('R110','100k 1%','+5V_RAW to USB_EFUSE_OVLO; external 5V priority'),
    ('R111','37.4k 1%','USB_EFUSE_OVLO to GND_CTRL'),
    ('R112','10k','+3V3_TEENSY to PWR_USB_FAULT_N; never pull up to 5V'),
]:
    p = copy.deepcopy(parts['R101']); p.update(ref=ref,value=value,note=note); added.append(p)
for ref,value,note in [('C106','1uF','TEENSY_VUSB to GND_CTRL; U102 IN local bypass'),('C107','1uF','+5V_SYS to GND_CTRL; U102 OUT local bypass'),('C108','10nF','USB_EFUSE_DVDT to GND_CTRL; ~25ms ramp')]:
    p=copy.deepcopy(parts['C105' if ref=='C108' else 'C102']);p.update(ref=ref,value=value,note=note);added.append(p)
p=copy.deepcopy(parts['TP105']);p.update(ref='TP106',value='PWR_USB_FAULT_N',note='U102 FLT4; Teensy pad11/pin9 assignment is proposed');added.append(p)
jp=dict(ref='JP505',value='GPIO VCC 3V3/5V select',lib_id='Connector_Generic:Conn_01x03',footprint='Connector_PinHeader_2.54mm:PinHeader_1x03_P2.54mm_Vertical',note='1=+3V3_TEENSY; 2=VCC_GPIO_EXT to J507 pin1; 3=+5V_EXP (F206). One shunt: 1-2 default 3V3, 2-3 5V. IO stays 3.3V ONLY; actual header/shunt MPN pending.',status='provisional')
parts['J507']['note']='Pin1=VCC_GPIO_EXT (JP505 shared 3V3/5V selection); pin2=GND_CTRL; pin3..10=IO20/21/24/25/26/27/40/41_EXT. IO 3.3V ONLY; U505/U506 pin5 stays +3V3_TEENSY. Pin order proposal.'
parts['J210']['note']+='; pad11/pin9=PWR_USB_FAULT_N (2026-09-26 proposal), pad36/pin14 remains NC'

libs=g.Libraries();libs.add_custom(u)
for sheet_id, additions in [('S02A_power_input',added),('S05_io',[jp]),('S02B_star_teensy',[])]:
    path=dest/(sheet_id+'-1.kicad_sch');raw=path.read_text(encoding='utf-8-sig');tree=g.parse(raw)
    assert not any(g.children(tree,k) for k in ['wire','label','global_label','junction','no_connect']), 'Wiring started; inspect before applying'
    refs={json.loads(next(p for p in g.children(s,'property') if json.loads(p[1])=='Reference')[2]) for s in g.children(tree,'symbol')}
    assert not refs.intersection(p['ref'] for p in additions), 'Already applied'
    if not (backup/path.name).exists():shutil.copy2(path,backup/path.name)
    edits=[]
    for a,b,n in spans(raw):
        if n[0]=='paper' and sheet_id=='S02A_power_input': edits.append((a,b,'(paper "A2")'))
        if n[0]=='lib_symbols':
            newlibs={p['lib_id']:libs.get(p['lib_id']) for p in additions if not any(json.loads(s[1])==p['lib_id'] for s in g.children(n,'symbol'))}
            if newlibs:edits.append((b-1,b-1,'\n'+'\n'.join(g.dump(s) for s in newlibs.values())+'\n'))
        if n[0]=='symbol':
            props={json.loads(p[1]):p for p in g.children(n,'property')};ref=json.loads(props['Reference'][2])
            if ref in ['J507','J210']:
                old=props['Placement note'];old[2]=g.q(parts[ref]['note']);edits.append((a,b,g.dump(n)))
    new=[]
    rootid=g.first(g.parse((dest/'central-board-placement.kicad_sch').read_text(encoding='utf-8-sig')),'uuid')[1]
    # Reuse the existing instance path; keep the user's hierarchy UUIDs.
    inst=g.first(g.children(tree,'symbol')[0],'instances')
    pathnode=next(n for n in g.walk(inst) if n and n[0]=='path')
    for i,p in enumerate(additions):
        x,y=(55.88+(i%6)*76.2,275.59+(i//6)*50.8) if sheet_id=='S02A_power_input' else (134.62,320.04)
        s=libs.get(p['lib_id']);box=g.bounds(s)
        new.append(['symbol',['lib_id',g.q(p['lib_id'])],['at',str(x),str(y),'0'],['unit','1'],['in_bom','yes'],['on_board','yes'],['dnp','no'],['uuid',g.q(g.uid('part/'+p['ref']+'/1'))],g.prop('Reference',p['ref'],x,y+box[1]-7),g.prop('Value',p['value'],x,y+box[1]-3),g.prop('Footprint',p['footprint'],hide=True),g.prop('Datasheet',p.get('datasheet',''),hide=True),g.prop('Placement note',p['note'],hide=True),['instances',['project',g.q(g.NAME),['path',pathnode[1],['reference',g.q(p['ref'])],['unit','1']]]]])
    if sheet_id=='S02A_power_input':
        new.extend([g.text('2026-09-26 ADDITION: USB eFuse -> +5V_SYS; external +5V_RAW priority. Wiring not yet created.',280,252,1.27),g.text('U102 RPW footprint TBD. PWR_USB_FAULT_N -> Teensy pad11/pin9 is a proposed assignment.',280,365,1.27)])
    if sheet_id=='S05_io':new.append(g.text('JP505: 1=3V3 / 2=GPIO VCC / 3=5V_EXP. Default shunt 1-2. IO 3.3V ONLY.',300,345,1.27))
    if new:edits.append((raw.rfind(')'),raw.rfind(')'),'\n'+'\n'.join(g.dump(n) for n in new)+'\n'))
    for a,b,value in sorted(edits,reverse=True):raw=raw[:a]+value+raw[b:]
    path.write_text(raw,encoding='utf-8')
    for sheet in inventory['sheets']:
        if sheet['id']==sheet_id:sheet['parts'].extend(additions)

shutil.copy2(inventory_path,backup/inventory_path.name)
inventory_path.write_text(json.dumps(inventory,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
custom_path=dest/'CentralPlacement.kicad_sym';shutil.copy2(custom_path,backup/custom_path.name)
raw=custom_path.read_text(encoding='utf-8-sig');node=libs.get(u['lib_id']);node[1]=g.q('TPS259470ARPWR')
raw=raw[:raw.rfind(')')]+'\n'+g.dump(node)+'\n'+raw[raw.rfind(')'):];custom_path.write_text(raw,encoding='utf-8')
manifest=[]
for path in dest.glob('*.kicad_sch'):
    for s in g.children(g.parse(path.read_text(encoding='utf-8-sig')),'symbol'):
        p={json.loads(n[1]):json.loads(n[2]) for n in g.children(s,'property')}
        manifest.append(dict(ref=p['Reference'],value=p['Value'],lib_id=json.loads(g.first(s,'lib_id')[1]),sheet=path.name,footprint=p.get('Footprint',''),note=p.get('Placement note','')))
(dest/'placement-manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print('Added 12 physical parts; existing placement retained. Backup:',backup)
