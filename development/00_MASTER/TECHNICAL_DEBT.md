# Technical Debt

**Last updated:** 2026-07-11  
**Rule:** Add entries when discovered; resolve only via active sprint tasks.

## Open

| ID | Severity | Item | Impact | Proposed resolution |
|----|----------|------|--------|---------------------|
| TD-001 | Medium | Legacy entrypoints `main.py`, `dashboard.py`, `config.py` | Confuse newcomers; outside foundation gates | Document as legacy; migrate only under explicit sprint |
| TD-002 | Medium | Root README previously dashboard-only | Weak SSOT discovery | Mitigated by TIOS + README rewrite (Sprint-000) |
| TD-003 | Low | Limited real ML engine backends beyond stub + ORT adapter | Inference path incomplete for non-ORT | Expand adapters only in ML sprints |
| TD-004 | Medium | Product Signal Engine not unified with platform layers | Dual mental models (legacy CLI vs platform) | Mitigated by SIG-001…008; legacy cleanup later |
| TD-005 | Low | Paper trading product loop not fully productized | Current objective incomplete | PAPER-001…PAPER-007 |
| TD-006 | Low | Sentiment / confidence / RAG product surfaces mostly roadmap | Vision diagram ahead of code | Document as planned; implement in later versions |
| TD-007 | Medium | Broker live trading must remain disabled | Safety | Keep V1.5 gated; feature flags off |
| TD-SIG-01 | Medium | Legacy dashboard remains parallel signal UX | Drift vs platform ExplainableSignal path | Later deprecation sprint |
| TD-PAPER-01 | Medium | Paper scaffolds predate Signal Engine mapping | Need orchestration layer | PAPER-001…002 |
| TD-PAPER-02 | Low | Journal UX contracts-only in V1.2 | Rich UI later | PAPER-006 then later UX sprint |

## Resolved

| ID | Resolved in | Notes |
|----|-------------|-------|
| TD-SIG-02 | SIG-001…008 | Signal Engine V1.0 path accepted |
| TD-SIG-03 | SIG-006 (partial) | Confidence binders landed; sentiment engines still later |

## Process

1. Never silently delete debt entries — mark resolved with sprint ID.
2. Debt does not authorize out-of-sprint work.
3. Sync this file when closing any sprint that touches debt.
