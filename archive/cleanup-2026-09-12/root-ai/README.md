# Root AI generated artifacts (2026-09-12)

Moved from the project root after `rg` found no references. These are recoverable generated previews/diagnostics.

| Old path | New path |
|---|---|
| `.ai_board_all.svg` | `archive/cleanup-2026-09-12/root-ai/.ai_board_all.svg` |
| `.ai_board_top.png` | `archive/cleanup-2026-09-12/root-ai/.ai_board_top.png` |
| `.ai_current_drc.rpt` | `archive/cleanup-2026-09-12/root-ai/.ai_current_drc.rpt` |
| `.ai_partial_net.xml` | `archive/cleanup-2026-09-12/root-ai/.ai_partial_net.xml` |
| `.ai_recovery_net.xml` | `archive/cleanup-2026-09-12/root-ai/.ai_recovery_net.xml` |
| `.ai_savepoint_erc.rpt` | `archive/cleanup-2026-09-12/root-ai/.ai_savepoint_erc.rpt` |
| `.ai_stage1_erc.rpt` | `archive/cleanup-2026-09-12/root-ai/.ai_stage1_erc.rpt` |
| `.ai_stage1_net.xml` | `archive/cleanup-2026-09-12/root-ai/.ai_stage1_net.xml` |
| `.ai_stage2_erc.rpt` | `archive/cleanup-2026-09-12/root-ai/.ai_stage2_erc.rpt` |
| `.ai_stage2_net.xml` | `archive/cleanup-2026-09-12/root-ai/.ai_stage2_net.xml` |

Restore from project root (after confirming root destinations are absent):

```powershell
Get-ChildItem -LiteralPath 'archive\cleanup-2026-09-12\root-ai' -File -Filter '.ai_*' | Move-Item -Destination (Resolve-Path '.')
```
