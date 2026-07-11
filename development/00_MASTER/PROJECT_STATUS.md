# Project Status

**Last updated:** 2026-07-12
**Control system:** TIOS

## Snapshot

| Field | Value |
|-------|--------|
| Product | Khaldun Trade |
| Current version (platform baseline) | Foundation + Phase 2 ML + Signal Engine V1.0 + paper risk gate |
| Product version target | V1.2 Paper Trading |
| Current sprint | Sprint-002 — Paper Trading (implementation in progress) |
| Current task | PAPER-004 |
| Task status | READY |
| Previous task | PAPER-003 (**complete**) |
| Current milestone | Paper Trading V1.2 — simulation fill + ledger next |
| Coverage gate | ≥ 88% |
| Broker automation | Disabled |
| Signal Engine | V1.0 path **accepted** |
| Signal universe | 20 crypto + 20 PSX + all PMEX instruments (`signal_universe.yaml`) |

## Progress (Roadmap View)

| Area | Completed % | Notes |
|------|-------------|-------|
| Signal Engine V1.0 implementation | 100% | SIG-001…008 done |
| Paper Trading V1.2 | ~40% | PAPER-001…003 done; PAPER-004 READY |
| Broker | disabled | V1.5 gated |

## Next Sprint / Task

**Active coding task: PAPER-004** — see [`NEXT_TASK.md`](NEXT_TASK.md).

## Sync Rule

```bash
python scripts/sync_tios_status.py
python scripts/validate_tios.py
```
