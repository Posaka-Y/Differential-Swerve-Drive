"""Add GPIO purpose labels to the saved drawing, preserving all existing placement/wires."""
import copy, json, runpy, uuid
from pathlib import Path
g=runpy.run_path(str(Path(__file__).with_name('generate-central-placement.py')))
root=g['ROOT']; ch=g['children']; first=g['first']; q=g['q']
p=root/'hardware/central-board-placement/S02B_star_teensy-1.kicad_sch'
backup=root/'output/kicad-check/central-readable-2026-09-29/before/central-board-placement'/p.name
assert p.read_bytes()==backup.read_bytes(), 'Source changed since snapshot'
t=g['parse'](p.read_text(encoding='utf-8-sig')); original=copy.deepcopy(t)
def props(s):return {json.loads(n[1]):json.loads(n[2]) for n in ch(s,'property')}
s=next(s for s in ch(t,'symbol') if props(s)['Reference']=='J210')
lib=next(l for l in ch(first(t,'lib_symbols'),'symbol') if l[1]==first(s,'lib_id')[1])
at=first(s,'at'); assert at[3]=='0' and not first(s,'mirror')
points={int(json.loads(first(n,'number')[1])):(round(float(at[1])+float(first(n,'at')[1]),4),round(float(at[2])-float(first(n,'at')[2]),4)) for n in g['walk'](lib) if n[0]=='pin'}
pinpath=root/'tools/kicad/central-teensy-pinmap.json'; mapping=json.loads(pinpath.read_text(encoding='utf-8-sig'))
for pin in mapping['pins']:
    if pin['pad'] in (6,7):pin.update(signal='NC',unused=True,electrical_type='no_connect',status='reserved')
mapping['source_policy']='Rev.1 48pad table plus ADR 2026-09-26. GPIO4/5 reserved after removal of individual E-stop monitoring. GPIO9 USB fault remains proposed.'
def ident(key):return q(str(uuid.uuid5(uuid.NAMESPACE_URL,'central-gpio-labels-2026-09-29/'+key)))
for n in ch(t,'global_label'):
    if json.loads(n[1])=='READ_SW_N':n[1]=q('REARM_SW_N')
added=[]
for pin in mapping['pins']:
    pad=pin['pad'];x,y=points[pad];left=pad<=24; angle=180 if left else 0
    labels=[n for n in ch(t,'global_label') if tuple(map(float,first(n,'at')[1:3]))==(x,y)]
    if pin['unused']:
        assert not labels
        t.append(['no_connect',['at',str(x),str(y)],['uuid',ident(f'nc-{pad}')]])
        # Unused pins must never be tied together by a common RESERVED/NC net.
        tx=x-4 if left else x+4
        text=g['text'](f'GPIO{pin["teensy_pin"]} RESERVED / NC',tx,y,.9)
        first(text,'effects').append(['justify','right' if left else 'left'])
        t.append(text)
    else:
        shape='output' if pin['electrical_type']=='output' else 'bidirectional' if pin['electrical_type']=='bidirectional' else 'input'
        if labels:
            assert len(labels)==1 and json.loads(labels[0][1])==pin['signal'], (pad,labels,pin)
            first(labels[0],'shape')[1]=shape
            continue
        # Use the pin endpoint, avoiding other components and existing wiring.
        fx=g['effects'](1.0); fx.append(['justify','right' if left else 'left'])
        t.append(['global_label',q(pin['signal']),['shape',shape],['at',str(x),str(y),str(angle)],fx,['uuid',ident(f'label-{pad}')],g['prop']('Intersheetrefs','${INTERSHEET_REFS}',x,y,hide=True)])
        added.append((pad,pin['signal']))
t.append(g['text']('GPIO PURPOSE LABELS | socket pad numbers differ from GPIO numbers\nGPIO4/5: reserved (individual E-stop monitor removed)\nGPIO9 / pad11: USB fault allocation PROPOSED\nOther RESERVED / NC pins are intentionally unconnected',281,243,1.27))
assert ch(t,'symbol')==ch(original,'symbol')
assert ch(t,'wire')==ch(original,'wire')
assert ch(t,'junction')==ch(original,'junction')
p.write_text(g['dump'](t)+'\n',encoding='utf-8')
pinpath.write_text(json.dumps(mapping,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print(json.dumps({'added_labels':added,'unused_pads':[p['pad'] for p in mapping['pins'] if p['unused']],'preserved':'all symbols, wires, junctions'},ensure_ascii=False))
