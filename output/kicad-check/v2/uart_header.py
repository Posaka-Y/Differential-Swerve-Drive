from pathlib import Path
import re
import uuid

sym_library = Path(r'C:/Program Files/KiCad/10.0/share/kicad/symbols/Connector_Generic.kicad_sym').read_text(encoding='utf-8')
footprint = 'Connector_PinHeader_2.54mm:PinHeader_1x03_P2.54mm_Vertical'

boards = [
    dict(path=Path('hardware/unit-board-v2/unit-board.kicad_sch'), project='unit-board',
         sheet='902d1696-b686-472b-a104-e0c03f0522c9', y=170.18,
         tp={'TP901': (106.68,167.64,173.99), 'TP902': (132.08,167.64,173.99), 'TP903': (157.48,167.64,173.99)},
         tx='DBG_TX', rx='DBG_RX', note_y=150.495),
    dict(path=Path('hardware/odometry-board-v2/Oddom board.kicad_sch'), project='Oddom board',
         sheet='fb6eb458-0fd8-4f13-9fe8-a6967e1b6388', y=175.26,
         tp={'TP901': (124.46,173.99,179.07), 'TP902': (144.78,173.99,179.07), 'TP903': (109.22,173.99,179.07)},
         tx='USART2_TX', rx='USART2_RX', note_y=160.02),
]

def uid(): return str(uuid.uuid4())

def balanced(src, start):
    depth=0; quoted=escaped=False
    for i in range(start,len(src)):
        c=src[i]
        if quoted:
            if escaped: escaped=False
            elif c=='\\': escaped=True
            elif c=='"': quoted=False
        elif c=='"': quoted=True
        elif c=='(': depth+=1
        elif c==')':
            depth-=1
            if depth==0:return src[start:i+1],i+1
    raise ValueError('unbalanced')

def form_at(src,prefix): return balanced(src,src.index(prefix))[0]

def top_forms(src):
    depth=0; quoted=escaped=False; start=0
    for i,c in enumerate(src):
        if quoted:
            if escaped: escaped=False
            elif c=='\\': escaped=True
            elif c=='"': quoted=False
            continue
        if c=='"': quoted=True; continue
        if c=='(':
            if depth==1:start=i
            depth+=1
        elif c==')':
            depth-=1
            if depth==1:yield src[start:i+1]

def xy(x,y):
    return f'{x:.2f}'.rstrip('0').rstrip('.'),f'{y:.2f}'.rstrip('0').rstrip('.')

def wire(x1,y1,x2,y2):
    x1,y1=xy(x1,y1);x2,y2=xy(x2,y2)
    return f'(wire (pts (xy {x1} {y1}) (xy {x2} {y2})) (stroke (width 0) (type default)) (uuid "{uid()}"))'

def label(name,x,y,global_kind=True):
    x,y=xy(x,y)
    if global_kind:
        return f'(global_label "{name}" (shape input) (at {x} {y} 0) (effects (font (size 1 1)) (justify left)) (uuid "{uid()}"))'
    return f'(label "{name}" (at {x} {y} 0) (effects (font (size 1 1)) (justify left bottom)) (uuid "{uid()}"))'

lib=form_at(sym_library,'(symbol "Conn_01x03"').replace('(symbol "Conn_01x03"','(symbol "Connector_Generic:Conn_01x03"',1)

for b in boards:
    s=b['path'].read_text(encoding='utf-8')
    assert '(symbol "Connector_Generic:Conn_01x03"' not in s
    libs=form_at(s,'(lib_symbols')
    s=s.replace(libs,libs[:-1]+'\n'+lib+'\n)',1)
    remove=[]; found=set(); wires=set(); labels=set(); notes=0
    for f in top_forms(s):
        if f.startswith('(symbol'):
            m=re.search(r'\(property "Reference" "(TP90[123])"',f)
            if m: remove.append(f);found.add(m.group(1))
        elif f.startswith('(wire'):
            pts=re.findall(r'\(xy ([\d.]+) ([\d.]+)\)',f)
            for ref,(x,y0,y1) in b['tp'].items():
                if set(pts)=={xy(x,y0),xy(x,y1)}:
                    remove.append(f);wires.add(ref)
        elif f.startswith(('(label','(global_label')):
            at=re.search(r'\(at ([\d.]+) ([\d.]+) 0\)',f)
            if at:
                for ref,(x,_,y1) in b['tp'].items():
                    if (at.group(1),at.group(2))==xy(x,y1):
                        remove.append(f);labels.add(ref)
        elif f.startswith('(text') and 'test pads (MCU TX / RX)' in f:
            remove.append(f);notes+=1
    assert found==set(b['tp']) and wires==found and labels==found and notes==1,(b['path'],found,wires,labels,notes)
    for f in remove: s=s.replace(f,'',1)
    x=116.84;y=b['y'];x2=x+5.08;x3=134.62
    ref_y=y-10.16;value_y=y-7.62
    new=['\n'.join([
        f'(symbol (lib_id "Connector_Generic:Conn_01x03") (at {x} {y} 0) (mirror y) (unit 1) (in_bom yes) (on_board yes) (dnp no) (uuid "{uid()}")',
        f' (property "Reference" "J9" (at {x+1.27} {ref_y:.2f} 0) (effects (font (size 1.27 1.27))))',
        f' (property "Value" "UART_3V3_1x03" (at {x+1.27} {value_y:.2f} 0) (effects (font (size 1 1))))',
        f' (property "Footprint" "{footprint}" (at {x} {y} 0) (effects (font (size 1 1)) (hide yes)))',
        f' (instances (project "{b["project"]}" (path "/{b["sheet"]}" (reference "J9") (unit 1)))))'])]
    for pin,net in [(1,'GND'),(2,b['tx']),(3,b['rx'])]:
        py=round(y+(pin-2)*2.54,2)
        new += [wire(x2,py,x3,py),label(net,x3,py,b['project']!='unit-board')]
    new.append(f'(text "UART J9: 1 GND / 2 MCU TX / 3 MCU RX; 3.3V logic, no power" (at 104.14 {b["note_y"]} 0) (effects (font (size 1.1 1.1)) (justify left)) (uuid "{uid()}"))')
    s=s.rstrip()[:-1]+'\n'+'\n'.join(new)+'\n)\n'
    b['path'].write_text(s,encoding='utf-8')
    print(b['path'],'removed',len(remove),'TP objects; added J9')
