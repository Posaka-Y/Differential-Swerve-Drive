import collections
import sys
import xml.etree.ElementTree as ET

import pcbnew

netlist, board_path = sys.argv[1:3]
root = ET.parse(netlist).getroot()
sch_refs = {c.attrib['ref'] for c in root.findall('./components/comp') if not c.attrib['ref'].startswith('#')}
sch = {}
for net in root.findall('./nets/net'):
    name = net.attrib['name']
    for node in net.findall('node'):
        sch[(node.attrib['ref'], node.attrib['pin'])] = name

board = pcbnew.LoadBoard(board_path)
fps = {f.GetReference(): f for f in board.GetFootprints()}
pads = {}
for ref, f in fps.items():
    for p in f.Pads():
        pads[(ref, p.GetNumber())] = p.GetNetname()

print('Schematic physical refs', len(sch_refs), 'PCB refs', len(fps))
print('Missing PCB refs:', sorted(sch_refs - fps.keys()))
print('Extra PCB refs:', sorted(fps.keys() - sch_refs))
print('Schematic pin to PCB pad mismatches:')
mismatches = []
for key, net in sorted(sch.items()):
    if key[0] not in fps:
        continue
    actual = pads.get(key)
    if actual != net:
        mismatches.append((key[0], key[1], net, actual or '<missing>'))
        print(*mismatches[-1], sep=' | ')
print('Mismatch count', len(mismatches))
print('PCB pads absent from schematic pin list:')
for key, net in sorted(pads.items()):
    if key not in sch:
        print(key[0], key[1], net, sep=' | ')
