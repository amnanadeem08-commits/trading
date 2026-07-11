# Phase Signal — V1.0 Signal Engine

**Status:** SIG-001…008 complete — **Signal Engine V1.0 path accepted**  
**Product version:** V1.0 Signal Engine  
**Readiness:** [`SIGNAL_ENGINE_V1_READINESS.md`](SIGNAL_ENGINE_V1_READINESS.md)  
**Active phase folder:** `sprints/Sprint-001_Signal_Engine_Planning/`

## Purpose

Productize explainable signal generation on top of certified foundation + Phase 2 ML infrastructure. Package `signal_engine` covers intake through validation, registry, lifecycle events, and E2E coverage.

## Rules

- Implement only the task listed in `00_MASTER/NEXT_TASK.md` / `10_STATUS/NEXT_TASK.md`
- When Active coding task is `none`, do not invent work
- Reuse `models.signal.ExplainableSignal` contracts; do not invent parallel signal schemas
- No reverse imports; no live broker paths
- No profit guarantees / financial advice framing

## Sprints

| Sprint | Status |
|--------|--------|
| [Sprint-001 Signal Engine Planning](sprints/Sprint-001_Signal_Engine_Planning/) | Complete — SIG-001…008 done; V1.0 path accepted |
