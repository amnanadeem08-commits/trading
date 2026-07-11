# TASK-SIG-005 — LLM Insight and Explainability Attachment

## Sprint

Sprint-001 — Signal Engine Planning (planning artifacts). Implementation work executes only when this ID is the Active coding task in NEXT_TASK.md.

## Goal

Attach `LLMInsight` for AI-enhanced signals using `ai` contracts; keep advice/profit claims forbidden.

## Objective

Attach `LLMInsight` for AI-enhanced signals using `ai` contracts; keep advice/profit claims forbidden.

## Background

ExplainableSignal requires llm_insight when decision_source is AI_ENHANCED_ML.

## Scope

### Implementation Scope

Prompted insight adapter using ai package contracts; versioned prompt reference in provenance.prompt_version.

## Out of Scope

Autonomous trading agents; RAG productization beyond what's needed for insight text.

## Dependencies

SIG-001, SIG-004 (for AI_ENHANCED_ML path)

## Architecture Impact

signal_engine may depend on ai only if import contracts allow; otherwise bridge from allowed higher orchestrator — resolve in task design before coding.

## Implementation Notes

All LLM text labeled as model output; no financial advice framing.

## Files Expected

- llm insight adapter
- prompt version wiring
- tests with fake LLM provider

## Tests Required

Unit tests; contract tests for required fields.

## Validation Gates

Full code gates + validate_tios

## Validation

Full code gates + validate_tios

## Acceptance Criteria

- [x] llm_insight present for AI_ENHANCED_ML
- [x] prompt_version set
- [x] Safety language respected in fixtures

## Status

done

## Completion Notes

Completed 2026-07-11. LLM attach mapper/port/stub + safety. Report: `SIG-005_COMPLETION_REPORT.md`. Next: SIG-006.

## Completion Report Format

When this task closes, write notes covering:

1. Files created / modified
2. Tests added and commands run
3. Architecture / import impact
4. Acceptance criteria checklist (all [x])
5. Remaining risks / debt
6. Recommended next task ID
7. Run `python scripts/sync_tios_status.py` and `python scripts/validate_tios.py`
