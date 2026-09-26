from pathlib import Path
import re
import uuid

source = Path('hardware/odometry-board-v2/Oddom board.kicad_sch')
drive = Path('hardware/unit-board-v2/unit-board.kicad_sch')
s = source.read_text(encoding='utf-8')
d = drive.read_text(encoding='utf-8')
project = 'Oddom board'
sheet = 'fb6eb458-0fd8-4f13-9fe8-a6967e1b6388'

def balanced(src, start):
    depth = 0
    quoted = escaped = False
    for i in range(start, len(src)):
        c = src[i]
        if quoted:
            if escaped: escaped = False
            elif c == '\\': escaped = True
            elif c == '"': quoted = False
        elif c == '"': quoted = True
        elif c == '(':
            depth += 1
        elif c == ')':
            depth -= 1
            if depth == 0: return src[start:i+1], i+1
    raise ValueError('unbalanced form')

def form_at(src, prefix):
    i = src.index(prefix)
    return balanced(src, i)[0]

def uid(): return str(uuid.uuid4())

# Bring in the exact symbols used by drive V2; no library search or pin-order guesswork.
libs = form_at(s, '(lib_symbols')
for name in ('Connector_Generic:Conn_02x05_Odd_Even', 'Connector:TestPoint'):
    if f'(symbol "{name}"' not in libs:
        libs = libs[:-1] + '\n' + form_at(d, f'(symbol "{name}"') + '\n)'
s = s.replace(form_at(s, '(lib_symbols'), libs, 1)

# Remove the old GH6 symbol, its six attached labels/GND symbol, and its old frame.
remove = []
depth = 0; quoted = escaped = False; start = 0
for i, c in enumerate(s):
    if quoted:
        if escaped: escaped = False
        elif c == '\\': escaped = True
        elif c == '"': quoted = False
        continue
    if c == '"': quoted = True; continue
    if c == '(':
        if depth == 1: start = i
        depth += 1
    elif c == ')':
        depth -= 1
        if depth == 1:
            f = s[start:i+1]
            if (f.startswith('(symbol') and ('(property "Reference" "J8"' in f or '(property "Reference" "#PWR043"' in f)) or \
               (f.startswith('(global_label') and re.search(r'\(at 86\.36 (147\.32|149\.86|152\.4|154\.94|157\.48|160\.02) 0\)', f)) or \
               (f.startswith('(rectangle') and '9dfa57ae-f9a8-4bac-a938-e04ad512fabc' in f):
                remove.append(f)
assert len(remove) == 8, [x[:80] for x in remove]
for f in remove: s = s.replace(f, '', 1)

# PB3/U1 pin55 (F405 SWO) was marked NC. It is the only old NC changed.
nc = re.search(r'\(no_connect\s+\(at 179\.07 116\.84\)\s+\(uuid "[^"]+"\)\s*\)', s)
assert nc
s = s.replace(nc.group(), '', 1)

def wire(x1,y1,x2,y2):
    return f'(wire (pts (xy {x1} {y1}) (xy {x2} {y2})) (stroke (width 0) (type default)) (uuid "{uid()}"))'
def label(name,x,y):
    return f'(global_label "{name}" (shape input) (at {x} {y} 0) (effects (font (size 1 1)) (justify left)) (uuid "{uid()}"))'
def tp(ref, value, x):
    return '\n'.join([
      f'(symbol (lib_id "Connector:TestPoint") (at {x} 170.18 0) (unit 1) (in_bom yes) (on_board yes) (dnp no) (uuid "{uid()}")',
      f' (property "Reference" "{ref}" (at {x+1.27} 160.02 0) (effects (font (size 1.27 1.27))))',
      f' (property "Value" "{value}" (at {x+1.27} 162.56 0) (effects (font (size 1 1))))',
      f' (property "Footprint" "TestPoint:TestPoint_Pad_D1.5mm" (at {x} 170.18 0) (effects (font (size 1 1)) (hide yes)))',
      f' (instances (project "{project}" (path "/{sheet}" (reference "{ref}") (unit 1)))))',
      wire(x,170.18,x,175.26), label(value,x,175.26)])

new = []
new.append('\n'.join([
 '(symbol (lib_id "Connector_Generic:Conn_02x05_Odd_Even") (at 76.2 170.18 0) (unit 1) (in_bom yes) (on_board yes) (dnp no) (uuid "'+uid()+'")',
 ' (property "Reference" "J8" (at 77.47 160.02 0) (effects (font (size 1.27 1.27))))',
 ' (property "Value" "Cortex_Debug_10pin" (at 77.47 162.56 0) (effects (font (size 1 1))))',
 ' (property "Footprint" "" (at 76.2 170.18 0) (effects (font (size 1 1)) (hide yes)))',
 f' (instances (project "{project}" (path "/{sheet}" (reference "J8") (unit 1)))))']))
for y,n in [(165.1,'PWR_3.3V'),(167.64,'GND'),(170.18,'GND'),(175.26,'GND')]:
    new += [wire(71.12,y,53.34,y),label(n,53.34,y)]
for y,n in [(165.1,'SWDIO'),(167.64,'SWCLK'),(170.18,'SWO'),(175.26,'NRST')]:
    new += [wire(83.82,y,88.9,y),label(n,88.9,y)]
for x in (71.12,83.82):
    new.append(f'(no_connect (at {x} 172.72) (uuid "{uid()}"))')
new.append(label('SWO',179.07,116.84))
new += [tp('TP901','USART2_TX',116.84), tp('TP902','USART2_RX',137.16), tp('TP903','GND',101.6)]
new.append(f'(text "SWD 1.27mm 2x5; keyed header / footprint TBD" (at 54.61 187.96 0) (effects (font (size 1.1 1.1)) (justify left)) (uuid "{uid()}"))')
new.append(f'(text "VTref = MCU digital 3V3 sense; pin7 KEY / pin8 TDI = NC" (at 54.61 191.77 0) (effects (font (size 1.1 1.1)) (justify left)) (uuid "{uid()}"))')
new.append(f'(text "USART2 test pads (MCU TX / RX)" (at 114.3 156.21 0) (effects (font (size 1.1 1.1)) (justify left)) (uuid "{uid()}"))')
s = s.rstrip()[:-1] + '\n' + '\n'.join(new) + '\n)\n'
source.write_text(s, encoding='utf-8')
print('removed',len(remove),'root objects; added 10pin SWD and 3 TP')
