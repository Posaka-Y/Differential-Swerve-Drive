"""Normalize generated reference sheets without changing the source project."""
import re
import json
import uuid
from pathlib import Path

BASE = Path(__file__).resolve().parents[2] / 'hardware/central-board/reference-2026-09-12'

def parse(text):
    tokens = re.findall(r'"(?:\\.|[^"\\])*"|[()]|[^\s()]+', text)
    stack, root = [], None
    for token in tokens:
        if token == '(':
            item = []
            if stack:
                stack[-1].append(item)
            else:
                root = item
            stack.append(item)
        elif token == ')':
            stack.pop()
        else:
            stack[-1].append(token)
    return root

def children(node, name):
    return [c for c in node if isinstance(c, list) and c and c[0] == name]

def first(node, name):
    return next(iter(children(node, name)), None)

def dump(node, depth=0):
    if not isinstance(node, list):
        return node
    if not any(isinstance(x, list) for x in node):
        return '(' + ' '.join(node) + ')'
    return '(' + ' '.join(dump(x, depth + 1) if not isinstance(x, list)
                           else '\n' + '\t' * (depth + 1) + dump(x, depth + 1)
                           for x in node) + ')'

def walk(node):
    if isinstance(node, list):
        yield node
        for child in node:
            yield from walk(child)

def q(value):
    return json.dumps(str(value))

def main():
    root = parse((BASE / 'central-board.kicad_sch').read_text(encoding='utf-8-sig'))
    root_id = json.loads(first(root, 'uuid')[1])
    # Existing CAN modules use the standard global GND symbol. Explicitly
    # bond that named net to the project's GND_CTRL on the overview sheet.
    if not any(n[0] == 'global_label' and n[1] == q('GND_CTRL') for n in children(root, 'global_label')):
        for name, x in [('GND', 35), ('GND_CTRL', 70)]:
            root.append(['global_label', q(name), ['shape', 'bidirectional'], ['at', str(x), '160', '0'],
                ['effects', ['font', ['size', '1.27', '1.27']]], ['uuid', q(uuid.uuid4())]])
        root.append(['wire', ['pts', ['xy', '35', '160'], ['xy', '70', '160']],
                     ['stroke', ['width', '0'], ['type', 'default']], ['uuid', q(uuid.uuid4())]])
        root.append(['text', q('GND / GND_CTRL: same control-ground net'), ['at', '55', '168', '0'],
                     ['effects', ['font', ['size', '1.27', '1.27']]], ['uuid', q(uuid.uuid4())]])
    (BASE / 'central-board.kicad_sch').write_text(dump(root) + '\n', encoding='utf-8')
    for index, sheet in enumerate(children(root, 'sheet'), 2):
        props = {json.loads(p[1]): json.loads(p[2]) for p in children(sheet, 'property')}
        path = BASE / props['Sheetfile']
        tree = parse(path.read_text(encoding='utf-8-sig'))
        sid = json.loads(first(sheet, 'uuid')[1])
        # Stable identifiers make repeated normalization reproducible.
        for item in walk(tree):
            if item and item[0] == 'uuid':
                item[1] = q(uuid.uuid5(uuid.NAMESPACE_URL, path.name + ':' + item[1]))
            if item and item[0] == 'hierarchical_label':
                item[0] = 'global_label'
            if item and item[0] in ('global_label', 'label') and len(item) > 1:
                if item[1] == q('+5V_TEENSY') and 'TEENSY' in path.name:
                    item[1] = q('VIN_TEENSY')
        counts = {}
        for sym in children(tree, 'symbol'):
            ref_prop = next(p for p in children(sym, 'property') if p[1] == q('Reference'))
            prefix = re.sub(r'\d.*', '', json.loads(ref_prop[2]))
            counts[prefix] = counts.get(prefix, 0) + 1
            ref = prefix + str(index * 100 + counts[prefix])
            ref_prop[2] = q(ref)
            for inst in children(sym, 'instances'):
                sym.remove(inst)
            sym.append(['instances', ['project', q('central-board'),
                ['path', q('/' + root_id + '/' + sid), ['reference', q(ref)],
                 ['unit', first(sym, 'unit')[1] if first(sym, 'unit') else '1']]]])
        path.write_text(dump(tree) + '\n', encoding='utf-8')
    print('Normalized reference sheet identifiers, references and global boundaries.')

if __name__ == '__main__':
    main()
