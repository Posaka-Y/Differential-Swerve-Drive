"""Repair saved central power wiring while preserving the user's placement."""
import copy, hashlib, importlib.util, json, math, re, shutil, uuid
from pathlib import Path

spec=importlib.util.spec_from_file_location('g',Path(__file__).with_name('generate-central-placement.py'))
g=importlib.util.module_from_spec(spec);spec.loader.exec_module(g)
root=g.ROOT/'hardware/central-board-placement'
out=g.ROOT/'output/kicad-check/central-power-fix-2026-09-26'
a_path=root/'S02A_power_input-1.kicad_sch';b_path=root/'S02B_star_teensy-1.kicad_sch'
a=g.parse(a_path.read_text(encoding='utf-8-sig'));b=g.parse(b_path.read_text(encoding='utf-8-sig'))
assert not g.children(b,'wire'), 'Old placement is now wired; inspect before deduplication'
for p in [a_path,b_path,root/'CentralPlacement.kicad_sym']:
    assert p.read_bytes()==(out/'before'/p.name).read_bytes(), 'File changed since snapshot'
def props(s):return {json.loads(p[1]):p for p in g.children(s,'property')}
def ref(s):return json.loads(props(s)['Reference'][2])
def find(r):return next(s for s in g.children(a,'symbol') if ref(s)==r)
def setprop(s,k,v):props(s)[k][2]=g.q(v)
def point(r,n):
    s=find(r);lib=next(x for x in g.children(g.first(a,'lib_symbols'),'symbol') if x[1]==g.first(s,'lib_id')[1])
    p=next(x for x in g.walk(lib) if x[0]=='pin' and json.loads(g.first(x,'number')[1])==str(n))
    x,y=map(float,g.first(p,'at')[1:3]);mirror=g.first(s,'mirror')
    at=g.first(s,'at');angle=math.radians(float(at[3]));c=math.cos(angle);ss=math.sin(angle)
    dx=x*c-y*ss;dy=-x*ss-y*c
    if mirror:
        if mirror[1]=='y':dx=-dx
        else:dy=-dy
    return (round(float(at[1])+dx,4),round(float(at[2])+dy,4))
def ident(text):return g.q(str(uuid.uuid5(uuid.NAMESPACE_URL,'central-power-fix/'+text)))
def label(tree,name,xy,angle=0):
    tree.append(['global_label',g.q(name),['shape','input'],['at',str(xy[0]),str(xy[1]),str(angle)],g.effects(),['uuid',ident(f'{name}/{xy}/{angle}')],g.prop('Intersheetrefs','${INTERSHEET_REFS}',xy[0],xy[1],hide=True)])
def wire(p,q):
    a.append(['wire',['pts',['xy',str(p[0]),str(p[1])],['xy',str(q[0]),str(q[1])]],['stroke',['width','0'],['type','default']],['uuid',ident(f'wire/{p}/{q}')]])
custom_path=root/'CentralPlacement.kicad_sym';custom=g.parse(custom_path.read_text(encoding='utf-8-sig'))
def library_add(symbol,short):
    libnode=copy.deepcopy(symbol);libnode[1]=g.q(short)
    custom[:]=[n for n in custom if not(isinstance(n,list) and n[0]=='symbol' and n[1]==libnode[1])]
    custom.append(libnode)
def rename_def(symbol,libid):
    old=json.loads(symbol[1]).split(':')[-1];short=libid.split(':')[-1];symbol[1]=g.q(libid)
    for n in g.children(symbol,'symbol'):n[1]=g.q(json.loads(n[1]).replace(old+'_',short+'_',1))

# Repair a project-local copy of the downloaded land pattern, never the global library.
fp_source=Path('C:/Users/ttiro/Documents/KiCad/SamacSys/SamacSys_Parts.pretty/TPS259470LRPWR.kicad_mod')
shutil.copy2(fp_source,out/'before/TPS259470LRPWR.kicad_mod')
fp=g.parse(fp_source.read_text(encoding='utf-8-sig'));fp[1]=g.q('TPS25947_RPW_10Pin')
mapping={11:10,12:1,13:4,14:7}
for pad in g.children(fp,'pad'):
    number=int(json.loads(pad[1]));pad[1]=g.q(mapping.get(number,number))
assert {int(json.loads(p[1])) for p in g.children(fp,'pad')}==set(range(1,11))
fp_dest=g.ROOT/'hardware/lib/DifferentialSwerve.pretty/TPS25947_RPW_10Pin.kicad_mod'
fp_dest.write_text(g.dump(fp)+'\n',encoding='utf-8')
footprint='DifferentialSwerve:TPS25947_RPW_10Pin'
ic=find('IC1');oldlib=next(s for s in g.children(g.first(a,'lib_symbols'),'symbol') if s[1]==g.first(ic,'lib_id')[1])
extra_points={point('IC1',n) for n in range(11,15)}
newlib=copy.deepcopy(oldlib);libid='CentralPlacement:TPS259470LRPWR_10Pin';rename_def(newlib,libid)
names=['EN/UVLO','OVLO','AUXOFF','FLT','IN','OUT','dVdt','GND','ILM','ITIMER']
for sub in g.children(newlib,'symbol'):
    sub[:]=[n for n in sub if not(isinstance(n,list) and n[0]=='pin' and int(json.loads(g.first(n,'number')[1]))>10)]
for pin in (n for n in g.walk(newlib) if n[0]=='pin'):
    number=int(json.loads(g.first(pin,'number')[1]));g.first(pin,'name')[1]=g.q(names[number-1])
    pin[1]='input' if number in [1,2] else 'open_collector' if number in [3,4] else 'power_in' if number in [5,8] else 'passive'
g.first(a,'lib_symbols').append(newlib);library_add(newlib,'TPS259470LRPWR_10Pin')
g.first(ic,'lib_id')[1]=g.q(libid);setprop(ic,'Reference','U101');setprop(ic,'Footprint',footprint)
for n in g.walk(g.first(ic,'instances')):
    if n[0]=='reference':n[1]=g.q('U101')
ic[:]=[n for n in ic if not(isinstance(n,list) and n[0]=='pin' and int(json.loads(n[1]))>10)]
a[:]=[n for n in a if not(isinstance(n,list) and n[0]=='no_connect' and tuple(map(float,g.first(n,'at')[1:3])) in extra_points)]
u102lib=next(s for s in g.children(g.first(a,'lib_symbols'),'symbol') if s[1]==g.first(find('U102'),'lib_id')[1])
for p in (n for n in g.walk(u102lib) if n[0]=='pin'):
    if json.loads(g.first(p,'number')[1])=='6':p[1]='passive'  # ORing power path; flagged supply below.
library_add(u102lib,'TPS259470ARPWR');setprop(find('U102'),'Footprint',footprint)

# R104 belongs at OVLO; the R103 upper end belongs at EN.
bad={(226.06,55.88),(226.06,60.96)}
a[:]=[n for n in a if not(isinstance(n,list) and n[0]=='wire' and {tuple(map(float,x[1:3])) for x in g.children(g.first(n,'pts'),'xy')}==bad)]
for r,n,net in [('U101',1,'EFUSE_EN'),('R103',1,'EFUSE_EN'),('U101',2,'EFUSE_OVLO'),('R104',2,'EFUSE_OVLO'),('U101',5,'+5V_RAW'),('U102',5,'TEENSY_VUSB'),('J102',1,'TEENSY_VUSB'),('U102',6,'+5V_SYS'),('U102',1,'USB_EFUSE_EN'),('R108',2,'USB_EFUSE_EN'),('R110',1,'+5V_RAW'),('R112',2,'+3V3_TEENSY'),('R107',1,'GND_CTRL'),('C107',1,'GND_CTRL'),('U102',4,'PWR_USB_FAULT_N')]:label(a,net,point(r,n))
# Add intended NC to USB unused pins only.
for n in [3,10]:
    xy=point('U102',n)
    if not any(tuple(map(float,g.first(c,'at')[1:3]))==xy for c in g.children(a,'no_connect')):a.append(['no_connect',['at',str(xy[0]),str(xy[1])],['uuid',ident(f'U102-NC-{n}')]])

# The lower branch is the Teensy protected branch; D101 uses the same net.
f207=find('F207');f207pos=tuple(map(float,g.first(f207,'at')[1:3]))
remove_segments=[{(243.84,115.57),(237.49,115.57)}]
a.remove(f207)
a[:]=[n for n in a if not(isinstance(n,list) and n[0]=='wire' and {tuple(map(float,x[1:3])) for x in g.children(g.first(n,'pts'),'xy')} in remove_segments)]
setprop(find('F205'),'Value','1206L075/16WR');label(a,'+5V_TEENSY_F',point('D101',2));label(a,'+5V_TEENSY_F',point('F205',1));label(a,'+5V_EXP',(298.45,353.06))
# Remove the now-redundant dangling extension of the Teensy branch.
for n in list(g.children(a,'wire')):
    xy={tuple(map(float,x[1:3])) for x in g.children(g.first(n,'pts'),'xy')}
    if xy=={(269.24,309.88),(298.45,309.88)}:a.remove(n)

# Name supplies consistently and make intended sheet-to-sheet power connections explicit.
groundlib=copy.deepcopy(next(s for s in g.children(g.first(a,'lib_symbols'),'symbol') if s[1]==g.q('power:GND')))
rename_def(groundlib,'CentralPlacement:GND_CTRL')
for p in g.children(groundlib,'property'):
    if json.loads(p[1])=='Value':p[2]=g.q('GND_CTRL')
for pin in (n for n in g.walk(groundlib) if n[0]=='pin'):g.first(pin,'name')[1]=g.q('GND_CTRL')
g.first(a,'lib_symbols').append(groundlib);library_add(groundlib,'GND_CTRL')
for s in g.children(a,'symbol'):
    if g.first(s,'lib_id')[1]==g.q('power:GND'):g.first(s,'lib_id')[1]=g.q('CentralPlacement:GND_CTRL');setprop(s,'Value','GND_CTRL')
for old in list(g.children(a,'label')):
    name=json.loads(old[1]);name='+3V3_TEENSY' if name=='3.3V_TEENSY' else name
    label(a,name,tuple(map(float,g.first(old,'at')[1:3])),float(g.first(old,'at')[3]));a.remove(old)
# Preserve existing active circuit, remove only unwired duplicate placement copies.
duplicate={f'{prefix}{n}' for prefix in ['F','R','D'] for n in range(201,207)}|{f'J{n}' for n in range(201,205)}|{'TP211','TP212','TP213'}
b[:]=[n for n in b if not(isinstance(n,list) and n[0]=='symbol' and ref(n) in duplicate)]
# Create flag sources on supplied rails, without relaxing any ERC rule.
libs=g.Libraries();flaglib=libs.get('power:PWR_FLAG');g.first(a,'lib_symbols').append(flaglib)
instancepath=next(n[1] for n in g.walk(g.first(find('J101'),'instances')) if n[0]=='path')
for number,(net,xy) in enumerate([('+5V_RAW',(340.36,48.26)),('+5V_SYS',(340.36,60.96)),('GND_CTRL',(340.36,73.66))],901):
    label(a,net,xy)
    a.append(['symbol',['lib_id',g.q('power:PWR_FLAG')],['at',str(xy[0]),str(xy[1]),'0'],['unit','1'],['in_bom','yes'],['on_board','yes'],['dnp','no'],['uuid',ident(f'flag{number}')],g.prop('Reference',f'#FLG{number}',xy[0],xy[1],hide=True),g.prop('Value','PWR_FLAG',xy[0],xy[1]-4),g.prop('Footprint','',hide=True),g.prop('Datasheet','',hide=True),['instances',['project',g.q(g.NAME),['path',instancepath,['reference',g.q(f'#FLG{number}')],['unit','1']]]]])
note=g.text('POWER WIRING UPDATED 2026-09-26: U101/U102 RPW 10-pin; +5V_SYS ORing; F205 feeds D101 and D205.',285,25,1.27);a.append(note)
for path,tree in [(a_path,a),(b_path,b),(custom_path,custom)]:path.write_text(g.dump(tree)+'\n',encoding='utf-8')
print('Power repairs saved. User positions retained; old unwired duplicate branches removed.')
