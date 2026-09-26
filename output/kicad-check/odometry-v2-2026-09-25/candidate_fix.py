import sys
import pcbnew

path = sys.argv[1]
board = pcbnew.LoadBoard(path)
count = 0
removed = 0
for item in board.GetTracks():
    if type(item) is pcbnew.PCB_TRACK and item.GetWidth() == pcbnew.FromMM(0.175):
        item.SetWidth(pcbnew.FromMM(0.2))
        count += 1
    if type(item) is pcbnew.PCB_TRACK and item.GetNetname() == 'Net-(D1-IO_1)' and item.GetLength() < pcbnew.FromMM(0.06):
        board.Remove(item)
        removed += 1
print('changed 0.175mm segments:', count)
print('removed tiny dangling segment:', removed)
pcbnew.SaveBoard(path, board)
