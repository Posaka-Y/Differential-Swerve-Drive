"""Verify exported connectivity, independently fixed connector/pin contracts and preserved sheets."""
import runpy,json,collections,hashlib
from pathlib import Path
g=runpy.run_path(str(Path(__file__).with_name('generate-central-placement.py')));f,c=g['first'],g['children']
root=g['ROOT'];out=root/'output/kicad-check/central-nonpower-wiring-2026-09-29';base=root/'hardware/central-board-placement'
def readnets(path):
 t=g['parse'](path.read_text(encoding='utf-8-sig'));nets={};parts={}
 for n in c(f(t,'nets'),'net'):
  name=json.loads(f(n,'name')[1]);nets[name]={(json.loads(f(p,'ref')[1]),json.loads(f(p,'pin')[1])) for p in c(n,'node')}
 for n in c(f(t,'components'),'comp'):parts[json.loads(n[1][1])]=n
 return nets,parts
nets,parts=readnets(out/'after.net');before,bparts=readnets(out/'before.net');pn={r+'.'+p:n for n,ps in nets.items() for r,p in ps}
for pin,n in json.loads((out/'expected-pins.json').read_text()).items():
 a=pn.get(pin,'')
 assert (not a or a.startswith('unconnected-')) if n is None else (a==n or a.endswith('/'+n)),(pin,n,a)
for p in json.loads((root/'tools/kicad/central-teensy-pinmap.json').read_text())['pins']:
 a=pn.get('J210.'+str(p['pad']),'')
 assert (not a or a.startswith('unconnected-')) if p['unused'] else a==p['signal'],(p,a)
def check(ref,names):
 for i,n in enumerate(names,1):assert pn[ref+'.'+str(i)].split('/')[-1]==n,(ref,i,n,pn.get(ref+'.'+str(i)))
check('J401',['ESTOP_LOOP_OUT','ESTOP_LOOP_RETURN','ESTOP_LED_24V','GND_CTRL_LED'])
check('J402',['ESTOP_LOOP_RETURN','COIL_NEG'])
check('J403',['+24V_CTRL_IN','GND_24V_RETURN'])
check('JP505',['+3V3_TEENSY','VCC_GPIO_EXT','+5V_EXP'])
for r,a,b in [('J507','IO20_A6','IO21_A7'),('J508','IO24_A10','IO25_A11'),('J509','IO26_A12','IO27_A13'),('J510','IO40_A16','IO41_A17')]:check(r,['VCC_GPIO_EXT','GND_CTRL',a+'_EXT',b+'_EXT'])
for r,d in [('R211','D211'),('R212','D212'),('R213','D213')]:
 assert pn[d+'.1']=='GND_CTRL';assert pn[d+'.2'] in (pn[r+'.1'],pn[r+'.2'])
for d,col in [('D211','KGKT'),('D212','KRKT'),('D213','KGKT')]:assert col in json.loads(f(parts[d],'value')[1])
assert pn['U401.3']=='GND_CTRL' and pn['U401.4']=='ESTOP_LOOP_OK_N'
assert pn['D401.1']==pn['U401.1'] and pn['D401.2']==pn['U401.2']
assert pn['Q401.1']==pn['R415.1'] and pn['Q401.2'].endswith('/GND_24V_RETURN') and pn['Q401.3'].endswith('/COIL_NEG')
assert len({pn[p] for p in ['J210.15','J210.48','J401.1','J401.2','J401.3','J401.4','J403.2','J210.1']})==8,'Unexpected rail or return short'
assert set(bparts)<=set(parts),'Previously placed component lost'
hashes={};preserved_refs=set()
for p in base.glob('*.kicad_sch'):
 if p.name.startswith(('S02A','S03')):
  assert p.read_bytes()==(out/'before/central-board-placement'/p.name).read_bytes()
  hashes[p.name]=hashlib.sha256(p.read_bytes()).hexdigest()
  t=g['parse'](p.read_text(encoding='utf-8-sig'))
  preserved_refs.update(json.loads(next(z for z in c(s,'property') if json.loads(z[1])=='Reference')[2]) for s in c(t,'symbol'))
def groups(ns):return {frozenset((r,p) for r,p in ps if r in preserved_refs) for ps in ns.values()}-{frozenset()}
assert groups(nets)==groups(before),'Power/CAN connectivity changed'
summary={'pin_expectations':len(json.loads((out/'expected-pins.json').read_text())),'teensy_pads':48,'power_can_hashes':hashes,'preserved_power_can_connectivity':True,'component_count':len(parts),'remaining_TBD':['F401','F402','X401','X402','J401','J402','J403','SW211'],'result':'PASS'}
(out/'audit.json').write_text(json.dumps(summary,indent=2)+'\n',encoding='utf-8');print(json.dumps(summary,indent=2))
