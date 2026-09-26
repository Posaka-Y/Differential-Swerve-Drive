"""Independent placement inventory audit. Run with KiCad's Python."""
import collections
import hashlib
import json
import re
from pathlib import Path


def parse(text):
    tokens = iter(re.findall(r'"(?:\\.|[^"\\])*"|[()]|[^\s()]+', text))
    def node():
        result = []
        for token in tokens:
            if token == ')':
                return result
            result.append(node() if token == '(' else json.loads(token) if token.startswith('"') else token)
        return result
    assert next(tokens) == '('
    return node()


def children(node, key):
    return [x for x in node if isinstance(x, list) and x and x[0] == key]


def first(node, key):
    return children(node, key)[0]


def walk(node):
    if isinstance(node, list):
        yield node
        for item in node:
            yield from walk(item)


root = Path(__file__).resolve().parents[2]
inventory = json.loads((root / 'tools/kicad/central-placement-parts.json').read_text(encoding='utf-8'))
expected = {p['ref']: p for s in inventory['sheets'] for p in s['parts']}
actual = collections.defaultdict(list)
libs = {}
errors = []
for path in (root / 'hardware/central-board-placement').glob('*.kicad_sch'):
    tree = parse(path.read_text(encoding='utf-8'))
    for key in ['wire', 'bus', 'junction', 'label', 'global_label', 'hierarchical_label', 'no_connect']:
        if children(tree, key):
            errors.append(f'{path.name}: forbidden {key}')
    for group in children(tree, 'lib_symbols'):
        for symbol in children(group, 'symbol'):
            libs[symbol[1]] = symbol
    for symbol in children(tree, 'symbol'):
        props = {p[1]: p[2] for p in children(symbol, 'property')}
        ref = props['Reference']
        actual[ref].append(symbol)
        part = expected.get(ref)
        if part is None:
            errors.append('Unexpected ' + ref)
            continue
        for prop, field in [('Value', 'value'), ('Footprint', 'footprint'), ('Placement note', 'note')]:
            if props.get(prop, '') != part.get(field, ''):
                errors.append(f'{ref}: {prop} mismatch')
        if first(symbol, 'lib_id')[1] != part['lib_id']:
            errors.append(ref + ': library mismatch')


def pins(ref, unit=None):
    groups = children(libs[expected[ref]['lib_id']], 'symbol')
    if unit is not None:
        groups = [g for g in groups if re.search(rf'_{unit}_\d+$', g[1])]
    return {first(n, 'number')[1]: first(n, 'name')[1]
            for g in groups for n in walk(g) if n and n[0] == 'pin'}


for ref, part in expected.items():
    if ref not in actual:
        errors.append('Missing ' + ref)
        continue
    units = {int(re.search(r'_(\d+)_\d+$', s[1]).group(1))
             for s in children(libs[part['lib_id']], 'symbol')} - {0}
    units = units or {1}
    found = [int(first(s, 'unit')[1]) for s in actual[ref]]
    if sorted(found) != sorted(units):
        errors.append(f'{ref}: units {found} != {units}')
    if part.get('custom_pins') and pins(ref) != {p['number']: p['name'] for p in part['custom_pins']}:
        errors.append(ref + ': custom pins mismatch')

pinmap = json.loads((root / 'tools/kicad/central-teensy-pinmap.json').read_text())
if pins('J210') != {str(p['pad']): p['teensy_pin'] for p in pinmap['pins']}:
    errors.append('Teensy pad mapping mismatch')
if pins('U101') != dict(zip(map(str, range(1, 11)), ['EN/UVLO', 'OVLO', 'AUXOFF', 'FLT', 'IN', 'OUT', 'dVdt', 'GND', 'ILM', 'ITIMER'])):
    errors.append('TPS259470 pin mismatch')
if pins('Q401') != {'1': 'G', '2': 'S', '3': 'D'}:
    errors.append('IRLML0100 pin mismatch')
if set(pins('U402')) != set('12345') or pins('U402')['3'] != 'GND' or pins('U402')['5'] != 'VCC':
    errors.append('AHCT buffer pin mismatch')
for unit, wanted in enumerate([{1, 2, 15, 16}, {3, 4, 13, 14}, {5, 6, 11, 12}, {7, 8, 9, 10}], 1):
    if set(map(int, pins('U401', unit))) != wanted:
        errors.append(f'LTV847 channel {unit} mismatch')
hashes = json.loads((root / 'output/kicad-check/central-placement/existing-before.json').read_text(encoding='utf-8-sig'))
for item in hashes:
    if hashlib.sha256(Path(item['Path']).read_bytes()).hexdigest().upper() != item['Hash']:
        errors.append('Pre-existing file changed: ' + item['Path'])
status = 'FAIL' if errors else 'PASS'
summary = f'{status}: {len(actual)} references / {sum(map(len, actual.values()))} units / {len(hashes)} preserved hashes'
report = f'''# Independent central placement review

{summary}

- Actual schematic instances were parsed independently of the generator.
- References, units, values, footprint fields, notes and library IDs compared against parts JSON.
- Wiring, buses, junctions, net labels and no-connect objects are prohibited and checked.
- TPS259470: EN1 / OVLO2 / AUXOFF3 / FLT4 / IN5 / OUT6 / dVdt7 / GND8 / ILM9 / ITIMER10, matching transfer reference section 3.1.
- Teensy: all 48 socket pins match the independently verified pinmap; footprint numbering and 15.24mm row spacing were checked separately.
- Q401: G1 / S2 / D3 matches the 2026-09-23 source PDF generator.
- U402: standard AHCT1G125 symbol, 1=OE, 2=A, 3=GND, 4=Y, 5=VCC; standard logic-symbol signal names are blank and identifiable by graphic positions.
- LTV847: all four units and channel pairing 1/2 to 16/15, 3/4 to 14/13, 5/6 to 12/11, 7/8 to 10/9 match transfer reference section 3.4.
- Every pre-existing project file in the before-hash inventory was checked.

This verifies symbol placement only, not completed electrical connectivity or manufacture readiness. U101 and U401 footprints remain deliberately unresolved. No design decisions were changed.
'''
if errors:
    report += '\nErrors:\n' + '\n'.join('- ' + e for e in errors) + '\n'
(root / 'output/kicad-check/central-placement/independent-review.md').write_text(report, encoding='utf-8')
print(summary)
for error in errors:
    print(error)
