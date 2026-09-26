import collections
import hashlib
import json
import sys

import pcbnew as p

path = sys.argv[1]
b = p.LoadBoard(path)

def fingerprint(board):
    entries = []
    for f in board.GetFootprints():
        entries.append(('fp', f.GetReference(), f.GetFPIDAsString(), f.GetPosition().x, f.GetPosition().y, f.GetOrientationDegrees(), f.GetAttributes()))
        for pad in f.Pads():
            entries.append(('pad', f.GetReference(), pad.GetNumber(), pad.GetNetname(), pad.GetPosition().x, pad.GetPosition().y, pad.GetSize().x, pad.GetSize().y, pad.GetLayerSet().FmtHex()))
        for field in f.GetFields():
            if field is f.Reference() or field.GetText() == f.GetReference():
                continue
            entries.append(('field', f.GetReference(), field.GetText(), field.GetLayerName(), field.IsVisible(), field.GetPosition().x, field.GetPosition().y))
    for t in board.GetTracks():
        entries.append(('track', type(t).__name__, t.GetNetname(), t.GetLayerName(), t.GetStart().x, t.GetStart().y, t.GetEnd().x, t.GetEnd().y))
    for z in board.Zones():
        entries.append(('zone', z.GetNetname(), z.GetLayerSet().FmtHex(), z.GetPosition().x, z.GetPosition().y, z.GetNumCorners()))
    return hashlib.sha256(json.dumps(sorted(map(str, entries))).encode()).hexdigest()

before = fingerprint(b)
changed = []
for f in b.GetFootprints():
    ref = f.Reference()
    if ref.GetLayerName() in ('F.Silkscreen', 'B.Silkscreen') and ref.IsVisible():
        ref.SetVisible(False)
        changed.append(f.GetReference())

print('Hidden reference fields:', len(changed), ', '.join(sorted(changed)))
assert len(changed) == 22
assert before == fingerprint(b), 'Non-reference board content changed in memory'
p.SaveBoard(path, b)

r = p.LoadBoard(path)
assert before == fingerprint(r), 'Non-reference board content changed on save'
visible = [f.GetReference() for f in r.GetFootprints() if f.Reference().GetLayerName() in ('F.Silkscreen', 'B.Silkscreen') and f.Reference().IsVisible()]
silk_text = [(f.GetReference(), g.GetText()) for f in r.GetFootprints() for g in f.GraphicalItems() if type(g) is p.PCB_TEXT and g.GetLayerName() in ('F.Silkscreen', 'B.Silkscreen') and ('${REFERENCE}' in g.GetText() or g.GetText() == f.GetReference())]
silk_text += [('board', g.GetText()) for g in r.GetDrawings() if type(g) is p.PCB_TEXT and g.GetLayerName() in ('F.Silkscreen', 'B.Silkscreen') and '${REFERENCE}' in g.GetText()]
print('Visible silk reference fields:', visible)
print('Silk reference text graphics:', silk_text)
print('Non-reference fingerprint:', before)
assert not visible and not silk_text
