# Explainability

**Type:** Documentation only — not imported by production code.
**Product:** Khaldun Trade / TIOS

## Summary

Human-readable reasons, drivers, and invalidation.

## Key Points

- Required for signal UX
- LLM text must be labeled as model output (informational only)
- Keep structured fields separate from prose
- AI-enhanced signals set `provenance.prompt_version` from `LLMInsight.prompt_version`

## Platform Mapping

Signal Engine (`signal_engine.llm`) + `ai` contracts (`LLMResponse`, `Prompt`).

## Safety

Informational model commentary only — no financial-advice framing, no guaranteed profits.
Forbidden-phrase checks live in `signal_engine.llm.safety`. Use with paper trading and human review.
