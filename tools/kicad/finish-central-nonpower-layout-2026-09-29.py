"""Grid alignment and field layout for the nonpower wiring migration."""
import runpy,json
from pathlib import Path
g=runpy.run_path(str(Path(__file__).with_name('generate-central-placement.py')))
f,c,q=g['first'],g['children'],g['q'];base=g['ROOT']/'hardware/central-board-placement'
snap=lambda v:str(round(round(float(v)/1.27)*1.27,4))
for name in ('S04_safety-1','S05_io-1'):
 p=base/(name+'.kicad_sch');t=g['parse'](p.read_text())
 for s in c(t,'symbol'):
  at=f(s,'at');x,y,a=map(float,at[1:]);pr={json.loads(z[1]):z for z in c(s,'property')};ref=json.loads(pr['Reference'][2])
  if ref[0] in ('R','C','F','D'):
   vertical=(a%180==0) if ref[0] in ('R','C','F') else (a%180!=0)
   for k,dy in [('Reference',-1.27),('Value',1.27)]:
    z=pr[k];f(z,'at')[1:]=list(map(str,(x+5.08,y+dy,0 if vertical else a))) if vertical else list(map(str,(x,y+(-7.62 if k=='Reference' else -5.08),a)))
    fx=g['effects'](1.1)
    if vertical:fx.append(['justify','left'])
    z[z.index(f(z,'effects'))]=fx
  if ref=='U402':
   for k,dy in [('Reference',-3.81),('Value',-1.27)]:f(pr[k],'at')[1:]=list(map(str,(x+17.78,y+dy,0)));f(pr[k],'effects').append(['justify','left'])
  if ref=='JP505':
   # Keep selector clear of the bottom-right title block.
   dx,dy=-210,-160
   at[1]=str(x+dx);at[2]=str(y+dy)
   for z in c(s,'property'):
    zt=f(z,'at');zt[1]=str(float(zt[1])+dx);zt[2]=str(float(zt[2])+dy)
   for n in t:
    if not isinstance(n,list) or n[0] not in ('wire','label','global_label'):continue
    points=[z for z in g['walk'](n) if z[0] in ('at','xy')]
    # Selector stubs are the only connections in this box.
    if points and all(470<float(z[1])<491 and 379<float(z[2])<396 for z in points if z[0]!='at' or len(z)>2):
     for z in points:z[1]=str(float(z[1])+dx);z[2]=str(float(z[2])+dy)
 for n in list(t):
  if not isinstance(n,list) or n[0] not in ('symbol','wire','junction','label','global_label','no_connect'):continue
  if n[0]=='label' and json.loads(n[1])=='GND_CTRL':
   n[0]='global_label';n.insert(2,['shape','bidirectional']);at=f(n,'at');n.append(g['prop']('Intersheetrefs','${INTERSHEET_REFS}',at[1],at[2],hide=True))
  if name.startswith('S04') and n[0]=='global_label' and json.loads(n[1])=='GND_CTRL' and abs(float(f(n,'at')[1])-350)<.1 and float(f(n,'at')[2])<200:
   f(n,'at')[3]='0';f(f(n,'effects'),'justify')[1]='left'
  for z in g['walk'](n):
   if z[0] in ('at','xy'):z[1]=snap(z[1]);z[2]=snap(z[2])
 p.write_text(g['dump'](t)+'\n',encoding='utf-8')
print('Aligned to 1.27 mm grid, corrected field orientation, moved GPIO selector.')
