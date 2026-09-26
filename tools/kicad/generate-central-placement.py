"""Create an isolated, unwired central-board symbol-placement project.

Run with KiCad's bundled Python. Input is central-placement-parts.json.
This intentionally creates no PCB, nets, labels, power symbols or NC flags.
"""
import argparse
import copy
import json
import math
import re
import uuid
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
STD = Path('C:/Program Files/KiCad/10.0/share/kicad/symbols')
NAME = 'central-board-placement'

def q(v):
    return json.dumps(str(v), ensure_ascii=False)

def uid(v):
    return str(uuid.uuid5(uuid.NAMESPACE_URL, NAME + '/' + v))

def parse(text):
    stack = []
    root = None
    for t in re.findall(r'"(?:\\.|[^"\\])*"|[()]|[^\s()]+', text):
        if t == '(':
            a = []
            if stack: stack[-1].append(a)
            else: root = a
            stack.append(a)
        elif t == ')': stack.pop()
        else: stack[-1].append(t)
    return root

def children(n, key):
    return [a for a in n if isinstance(a, list) and a and a[0] == key]

def first(n, key):
    return next(iter(children(n, key)), None)

def dump(n):
    if not isinstance(n, list): return n
    return '(' + ' '.join(('\n' if isinstance(a, list) else '') + dump(a) for a in n) + ')'

def walk(n):
    if isinstance(n, list):
        yield n
        for a in n: yield from walk(a)

def effects(size=1.27, hide=False):
    return ['effects', ['font', ['size', str(size), str(size)]]] + ([['hide', 'yes']] if hide else [])

def prop(key, value, x=0, y=0, hide=False):
    return ['property', q(key), q(value), ['at', str(x), str(y), '0'], effects(hide=hide)]

def text(value, x, y, size=1.27):
    return ['text', q(value), ['at', str(x), str(y), '0'], effects(size), ['uuid', q(uid(f'text/{value}/{x}/{y}'))]]

class Libraries:
    def __init__(self): self.cache = {}; self.custom = {}
    def get(self, libid):
        if libid in self.custom: return copy.deepcopy(self.custom[libid])
        lib, name = libid.split(':', 1)
        if lib not in self.cache:
            path = ROOT / 'hardware/lib/DifferentialSwerve.kicad_sym' if lib == 'DifferentialSwerve' else STD / (lib + '.kicad_sym')
            self.cache[lib] = {json.loads(s[1]): s for s in children(parse(path.read_text(encoding='utf-8-sig')), 'symbol')}
        node = copy.deepcopy(self.cache[lib][name])
        ext = first(node, 'extends')
        if ext:
            base = self.get(lib + ':' + json.loads(ext[1]))
            ownprops = {p[1] for p in children(node, 'property')}
            node.remove(ext)
            for a in base[2:]:
                if not isinstance(a, list): continue
                if a[0] == 'property' and a[1] not in ownprops: node.append(a)
                elif a[0] == 'symbol': node.append(a)
                elif a[0] != 'property' and not first(node, a[0]): node.append(a)
        node[1] = q(libid)
        for s in children(node, 'symbol'):
            old = json.loads(s[1]); suffix = re.search(r'(_\d+_\d+)$', old).group(1)
            s[1] = q(name + suffix)
        return node

    def add_custom(self, part):
        libid = part['lib_id']; short = libid.split(':')[1]
        pins = part['custom_pins']; half = math.ceil(len(pins) / 2)
        h = max(10.16, (half + 1) * 2.54 / 2)
        n = ['symbol', q(libid), ['pin_names', ['offset', '1.016']], ['in_bom', 'yes'], ['on_board', 'yes'],
             prop('Reference', 'U'), prop('Value', part['value']),
             ['symbol', q(short + '_0_1'), ['rectangle', ['start', '-17.78', str(h)], ['end', '17.78', str(-h)], ['stroke', ['width', '0.254'], ['type', 'default']], ['fill', ['type', 'background']]]]]
        unit = ['symbol', q(short + '_1_1')]
        for i, p in enumerate(pins):
            left = i < half; j = i if left else i-half
            y = (half - 1) * 1.27 - j * 2.54
            unit.append(['pin', p.get('type', 'passive'), 'line', ['at', '-22.86' if left else '22.86', str(y), '0' if left else '180'], ['length', '5.08'], ['name', q(p['name']), effects()], ['number', q(p['number']), effects()]])
        n.append(unit); self.custom[libid] = n

def bounds(symbol, unit=1):
    pts = []
    for sub in children(symbol, 'symbol'):
        if int(re.search(r'_(\d+)_\d+$', json.loads(sub[1])).group(1)) not in (0,unit): continue
        for n in walk(sub):
            if n and n[0] in ('at', 'xy', 'start', 'end', 'center') and len(n) >= 3:
                try: pts.append((float(n[1]), -float(n[2])))
                except ValueError: pass
    return (min(x for x,y in pts), min(y for x,y in pts), max(x for x,y in pts), max(y for x,y in pts)) if pts else (-5,-5,5,5)

def base_sheet(key, title):
    return ['kicad_sch', ['version', '20250114'], ['generator', q('eeschema')], ['uuid', q(uid(key))], ['paper', q('A3')],
            ['title_block', ['title', q(title)], ['date', q('2026-09-23')], ['rev', q('PLACEMENT ONLY')], ['company', q('Differential Swerve')], ['comment', '1', q('Unwired draft - not for fabrication')]], ['lib_symbols']]

def main():
    ap = argparse.ArgumentParser(); ap.add_argument('--parts', type=Path, default=ROOT/'tools/kicad/central-placement-parts.json'); ap.add_argument('--output', type=Path, default=ROOT/'hardware'/NAME); args = ap.parse_args()
    dest = args.output.resolve()
    if dest != (ROOT/'hardware'/NAME).resolve(): raise ValueError('Output restricted to isolated placement project')
    inventory = json.loads(args.parts.read_text(encoding='utf-8-sig')); libs = Libraries()
    allparts = [p for s in inventory['sheets'] for p in s['parts']]
    refs = [p['ref'] for p in allparts]
    assert len(refs) == len(set(refs)), 'Duplicate references'
    for p in allparts:
        if p.get('custom_pins'): libs.add_custom(p)
    pages = []
    for group in inventory['sheets']:
        batch = []; x=20; y=40; rowheight=0; index=1
        large=len(group['parts'])>25
        limitx=574 if large else 400
        limity=380 if large else 262
        expanded=[]
        for p in group['parts']:
            symbol=libs.get(p['lib_id'])
            units=max([1]+[int(re.search(r'_(\d+)_\d+$', json.loads(s[1])).group(1)) for s in children(symbol,'symbol')])
            for unit in range(1, units+1): expanded.append(dict(p,unit=unit))
        for p in expanded:
            symbol = libs.get(p['lib_id']); box = bounds(symbol,p['unit'])
            w=max(76 if large else 72, box[2]-box[0]+28); h=max(40, box[3]-box[1]+24)
            if x+w > limitx: x=20; y+=rowheight; rowheight=0
            if y+h > limity: raise ValueError(f"Layout exceeds page: {group['id']} / {p['ref']}")
            px=round((x+w/2-(box[0]+box[2])/2)/1.27)*1.27
            py=round((y+15-box[1])/1.27)*1.27
            batch.append((p, symbol, round(px,4), round(py,4), box))
            x+=w; rowheight=max(rowheight,h)
        if batch: pages.append((group,index,batch))
    dest.mkdir(parents=True, exist_ok=True)
    root = base_sheet('root', 'Central board - symbol placement index'); rootid=uid('root')
    root.append(text('CENTRAL BOARD / UNWIRED COMPONENT PLACEMENT', 205, 20, 2.54))
    root.append(text('Open a sheet to wire the components. Footprints marked TBD remain unassigned.',205,28))
    report=[]
    for page,(group,index,batch) in enumerate(pages,2):
        key=f"{group['id']}-{index}"; filename=key+'.kicad_sch'; title=f"{group['title']} ({index})"; sid=uid('sheet/'+key)
        tree=base_sheet(key,title)
        if len(group['parts'])>25: first(tree,'paper')[1]=q('A2')
        tree.append(text(title,205,18,2.0)); tree.append(text('PLACEMENT ONLY - all pins intentionally unwired; see notes in symbol properties.',205,26))
        ls=first(tree,'lib_symbols'); seen=set()
        for p,s,x,y,b in batch:
            if p['lib_id'] not in seen: ls.append(s); seen.add(p['lib_id'])
            instance=['symbol',['lib_id',q(p['lib_id'])],['at',str(x),str(y),'0'],['unit',str(p['unit'])],['in_bom','yes'],['on_board','yes'],['dnp','no'],['uuid',q(uid('part/'+p['ref']+'/'+str(p['unit'])))],
                      prop('Reference',p['ref'],x,y+b[1]-7),prop('Value',p['value'],x,y+b[1]-3),prop('Footprint',p.get('footprint',''),hide=True),prop('Datasheet',p.get('datasheet',''),hide=True),prop('Placement note',p.get('note',''),hide=True),
                      ['instances',['project',q(NAME),['path',q('/'+rootid+'/'+sid),['reference',q(p['ref'])],['unit',str(p['unit'])]]]]]
            tree.append(instance)
            if not p.get('footprint'): tree.append(text('Footprint TBD',x,y+b[3]+5,1.0))
            if p.get('status') not in ('documented',):
                tree.append(text('REVIEW',x,y+b[3]+(9 if not p.get('footprint') else 5),1.0))
            report.append({'ref':p['ref'],'value':p['value'],'lib_id':p['lib_id'],'sheet':filename,'footprint':p.get('footprint',''),'note':p.get('note','')})
        if group['id']=='S02B_star_teensy':
            tree.append(text('UNRESOLVED: COMM LED - GPIO / implementation / reference pending.',285,365,1.27))
        if group['id']=='S04_safety':
            tree.append(text('UNRESOLVED: D4xx coil clamp - topology / polarity / rating / part pending.',285,355,1.27))
            tree.append(text('UNRESOLVED: LED branch protection - F402 / rating / part pending.',285,362,1.27))
        (dest/filename).write_text(dump(tree)+'\n',encoding='utf-8')
        ix=page-2; sx=25+(ix%3)*125; sy=45+(ix//3)*42
        root.append(['sheet',['at',str(sx),str(sy)],['size','110','24'],['stroke',['width','0.1524'],['type','solid']],['fill',['color','0','0','0','0']],['uuid',q(sid)],prop('Sheetname',title,sx+55,sy-3),prop('Sheetfile',filename,sx+55,sy+27),['instances',['project',q(NAME),['path',q('/'+rootid),['page',q(page)]]]]])
        root.append(text(f"{len(batch)} parts",sx+55,sy+12))
    root.append(['sheet_instances',['path',q('/'),['page',q('1')]]])
    (dest/(NAME+'.kicad_sch')).write_text(dump(root)+'\n',encoding='utf-8')
    project=dest/(NAME+'.kicad_pro')
    if not project.exists(): project.write_text(json.dumps({'meta':{'filename':project.name,'version':1}},indent=2)+'\n',encoding='utf-8')
    if libs.custom:
        custom=['kicad_symbol_lib',['version','20211014'],['generator','kicad_symbol_editor']]
        for libid,s in libs.custom.items():
            s=copy.deepcopy(s); s[1]=q(libid.split(':')[1]); custom.append(s)
        (dest/'CentralPlacement.kicad_sym').write_text(dump(custom)+'\n',encoding='utf-8')
    (dest/'sym-lib-table').write_text('(sym_lib_table\n(lib (name "DifferentialSwerve")(type "KiCad")(uri "${KIPRJMOD}/../lib/DifferentialSwerve.kicad_sym")(options "")(descr ""))\n(lib (name "CentralPlacement")(type "KiCad")(uri "${KIPRJMOD}/CentralPlacement.kicad_sym")(options "")(descr "")))\n',encoding='utf-8')
    (dest/'fp-lib-table').write_text('(fp_lib_table (lib (name "DifferentialSwerve")(type "KiCad")(uri "${KIPRJMOD}/../lib/DifferentialSwerve.pretty")(options "")(descr "")))\n',encoding='utf-8')
    forbidden={'wire','bus','label','global_label','hierarchical_label','no_connect','junction'}
    active={NAME+'.kicad_sch'}|{f"{group['id']}-{index}.kicad_sch" for group,index,batch in pages}
    for file in dest.glob('*.kicad_sch'):
        if file.name not in active:
            # Remove only our obsolete auto-split files inside the isolated output.
            if re.fullmatch(r'S\d+[A-Za-z0-9_]*-\d+\.kicad_sch',file.name): file.unlink()
            continue
        assert not [n for n in children(parse(file.read_text(encoding='utf-8')), 'wire')]
        assert not any(n[0] in forbidden for n in parse(file.read_text(encoding='utf-8')) if isinstance(n,list))
    (dest/'placement-manifest.json').write_text(json.dumps({'parts':report,'sheet_count':len(pages)+1,'symbol_count':len(refs),'connection_items':0},ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print(f'Generated {len(refs)} symbols on {len(pages)} child sheets in {dest}')

if __name__ == '__main__': main()
