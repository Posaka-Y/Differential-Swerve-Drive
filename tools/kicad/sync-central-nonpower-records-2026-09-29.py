"""Synchronize the saved drawing index and inventory without regenerating sheets."""
import runpy,json,copy,re
from pathlib import Path
g=runpy.run_path(str(Path(__file__).with_name('generate-central-placement.py')));f,c,q=g['first'],g['children'],g['q'];root=g['ROOT'];base=root/'hardware/central-board-placement';out=root/'output/kicad-check/central-nonpower-wiring-2026-09-29'
# Final small legibility fixes; electrical nodes retained.
p=base/'S04_safety-1.kicad_sch';t=g['parse'](p.read_text())
for n in c(t,'label'):
 if json.loads(n[1])=='MONITOR_SERIES':n[1]=q('MON_R')
for s in c(t,'symbol'):
 pr={json.loads(a[1]):a for a in c(s,'property')};ref=json.loads(pr['Reference'][2]);x,y,a=map(float,f(s,'at')[1:])
 if ref=='U402':
  for k,dy in [('Reference',-10.16),('Value',-7.62)]:f(pr[k],'at')[1:]=list(map(str,(x+17.78,y+dy,0)))
 if ref=='Q401':
  for k,dy in [('Reference',-7.62),('Value',-5.08)]:f(pr[k],'at')[1:]=list(map(str,(x+10.16,y+dy,0)));f(pr[k],'effects').append(['justify','left'])
 if ref=='D401':
  for k in ('Reference','Value'):f(pr[k],'at')[3]='90'
 if ref in ('X401','X402'):
  s.append(g['prop']('Design status','TBD functional placeholder; no selected device or conductive return connection',hide=True))
p.write_text(g['dump'](t)+'\n',encoding='utf-8')
expected=json.loads((out/'expected-pins.json').read_text());expected={k:('MON_R' if v=='MONITOR_SERIES' else v) for k,v in expected.items()};(out/'expected-pins.json').write_text(json.dumps(expected,indent=2)+'\n')

inventorypath=root/'tools/kicad/central-placement-parts.json';inventory=json.loads(inventorypath.read_text(encoding='utf-8-sig'));manifest=[];counts={}
for group in inventory['sheets']:
 p=base/(group['id']+'-1.kicad_sch')
 if not p.exists():continue
 t=g['parse'](p.read_text(encoding='utf-8-sig'));old={a['ref']:a for a in group['parts']};new=[]
 for s in c(t,'symbol'):
  pr={json.loads(a[1]):json.loads(a[2]) for a in c(s,'property')};ref=pr['Reference']
  if ref.startswith('#'):continue
  part=copy.deepcopy(old.get(ref,{}));part.update(ref=ref,value=pr['Value'],lib_id=json.loads(f(s,'lib_id')[1]),footprint=pr.get('Footprint',''))
  if ref in ('J507','J508','J509','J510'):part['note']='GPIO 4pin port; common JP505 VCC; 3.3V signals only; wired 2026-09-29'
  if ref in ('F402','X401','X402','J401'):part.update(status='TBD',note=pr.get('Design status','Rating / part / footprint TBD'))
  if ref in ('X401','X402'):
   lib=next(a for a in c(f(t,'lib_symbols'),'symbol') if a[1]==f(s,'lib_id')[1])
   part['custom_pins']=[{'number':json.loads(f(n,'number')[1]),'name':json.loads(f(n,'name')[1]),'type':n[1]} for n in g['walk'](lib) if n[0]=='pin']
  new.append(part);manifest.append({k:part.get(k,'') for k in ('ref','value','lib_id','footprint','note')}|{'sheet':p.name})
 group['parts']=new;counts[p.name]=len(new)
inventory['scope']='Saved schematic inventory as of 2026-09-29. Nonpower wired; safety TBDs explicit. NEVER regenerate saved power/CAN/manual sheets with placement generator.'
inventorypath.write_text(json.dumps(inventory,ensure_ascii=False,indent=2)+'\n',encoding='utf-8');(base/'placement-manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')

p=base/'central-board-placement.kicad_sch';t=g['parse'](p.read_text(encoding='utf-8-sig'))
t[:]=[n for n in t if not(isinstance(n,list) and n[0]=='text' and re.fullmatch(r'\d+ parts',json.loads(n[1])))]
for n in c(t,'text'):
 val=json.loads(n[1])
 if val=='CENTRAL BOARD / UNWIRED COMPONENT PLACEMENT':n[1]=q('CENTRAL BOARD / CIRCUIT DESIGN')
 elif val.startswith('Open a sheet to wire'):n[1]=q('Nonpower wiring added 2026-09-29. Safety TBD parts / return connection remain unresolved.')
 elif val.startswith('ARM: GUI'):n[1]=q('ARM: GUI over USB + SW211 -> shared Teensy safety gate.\nE-stop release does not re-arm. A new RUN request is required after ARM.\nSee S02B / S04. Firmware integration is separate from this schematic.')
tb=f(t,'title_block');f(tb,'title')[1]=q('Central board - circuit index');f(tb,'rev')[1]=q('WIRED DRAFT');f(tb,'date')[1]=q('2026-09-29')
for n in c(tb,'comment'):n[2]=q('Safety TBDs remain. Not for fabrication.')
p.write_text(g['dump'](t)+'\n',encoding='utf-8')
print(json.dumps(counts,indent=2));print('Inventory / manifest parts:',len(manifest))
