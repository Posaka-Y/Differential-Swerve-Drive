"""Replace X401 with the user-selected SMBJ33CA, preserving all other nets."""
import copy,json,runpy,hashlib
from pathlib import Path
g=runpy.run_path(str(Path(__file__).with_name('generate-central-placement.py')))
f,c,q=g['first'],g['children'],g['q'];base=g['ROOT']/'hardware/central-board-placement';out=g['ROOT']/'output/kicad-check/central-clamp-2026-09-29'
p=base/'S04_safety-1.kicad_sch';before=(out/'before'/p.name).read_bytes();assert p.read_bytes()==before,'Saved drawing changed since backup'
hashes={str(z.relative_to(base)):hashlib.sha256(z.read_bytes()).hexdigest() for z in base.glob('*.kicad_sch') if z!=p}
t=g['parse'](before.decode('utf-8-sig'))
def props(s):return {json.loads(z[1]):z for z in c(s,'property')}
assert not any(json.loads(props(s)['Reference'][2])=='D405' for s in c(t,'symbol'))
s=next(s for s in c(t,'symbol') if json.loads(props(s)['Reference'][2])=='X401')
x,y,a=map(float,f(s,'at')[1:]);assert a==0
for z in g['walk'](s):
 if z[0]=='reference' and z[1]==q('X401'):z[1]=q('D405')
f(s,'lib_id')[1]=q('Device:D_TVS')
cache=f(t,'lib_symbols');cache[:]=[z for z in cache if not(isinstance(z,list) and z[0]=='symbol' and z[1]==q('CentralPlacement:CoilClamp_TBD'))]
if not any(z[1]==q('Device:D_TVS') for z in c(cache,'symbol')):cache.append(g['Libraries']().get('Device:D_TVS'))
values={'Reference':'D405','Value':'SMBJ33CA','Footprint':'Diode_SMD:D_SMB','Datasheet':'https://www.aosmd.com/sites/default/files/res/datasheets/SMBJ33CA.pdf','Manufacturer':'Alpha & Omega Semiconductor','MPN':'SMBJ33CA','Description':'33V bidirectional TVS, SMB / DO-214AA, across contactor coil','Design status':'Selected 2026-09-29; release time and transient/energy validation pending','Placement note':'Near J402; short wide traces across COIL_POS / COIL_NEG. Check with actual harness.'}
for k,v in values.items():
 pr=props(s).get(k)
 if pr:pr[2]=q(v)
 else:pr=g['prop'](k,v,x,y,hide=True);s.append(pr)
 if k in ('Reference','Value'):
  f(pr,'at')[1:]=[str(x),str(round(y+(-7.62 if k=='Reference' else -5.08),4)),'0'];pr[pr.index(f(pr,'effects'))]=g['effects'](1.27)
 else:pr[pr.index(f(pr,'effects'))]=g['effects'](hide=True)
# Original custom box pins were +/-22.86 mm; TVS pins are +/-3.81 mm.
for sign in (-1,1):
 old=(round(x+sign*22.86,4),y);new=(round(x+sign*3.81,4),y);count=0
 for w in c(t,'wire'):
  for pt in c(f(w,'pts'),'xy'):
   if tuple(map(float,pt[1:]))==old:pt[1:]=list(map(str,new));count+=1
 assert count==1,(old,count)
for z in c(t,'text'):
 val=json.loads(z[1])
 if val.startswith('X401: clamp topology'):z[1]=q('D405: SMBJ33CA / BIDIRECTIONAL / 33 V\nRelease time and surge energy: bench verification pending')
 elif val.startswith('Unresolved:'):z[1]=q('Unresolved: J401/J402/J403 selection; F401/F402; X402 return connection.\nD405 selected; release time / transient validation pending. Not for fabrication.')
p.write_text(g['dump'](t)+'\n',encoding='utf-8')
for path in [g['ROOT']/'tools/kicad/central-placement-parts.json',base/'placement-manifest.json']:
 data=json.loads(path.read_text(encoding='utf-8-sig'));parts=data if isinstance(data,list) else [p for sh in data['sheets'] for p in sh['parts']]
 item=next(p for p in parts if p['ref']=='X401');item.update(ref='D405',value='SMBJ33CA',lib_id='Device:D_TVS',footprint='Diode_SMD:D_SMB',manufacturer=values['Manufacturer'],mpn='SMBJ33CA',datasheet=values['Datasheet'],status='selected; bench validation pending',note=values['Placement note'])
 item.pop('custom_pins',None);item.pop('custom_layout',None)
 path.write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
assert hashes=={str(z.relative_to(base)):hashlib.sha256(z.read_bytes()).hexdigest() for z in base.glob('*.kicad_sch') if z!=p}
(out/'unchanged-sheets.json').write_text(json.dumps(hashes,indent=2)+'\n')
print('X401 -> D405 AOS SMBJ33CA / Device:D_TVS / Diode_SMD:D_SMB. Other sheets unchanged.')
