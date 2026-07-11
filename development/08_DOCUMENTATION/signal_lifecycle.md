# Signal Lifecycle

## States (Canonical)

1. Created / received
2. Validated
3. Accepted or rejected
4. Active / in-flight
5. Completed, cancelled, or failed
6. Audited / reported

## Rules

- Transitions must be explicit and testable
- Prefer events + audit for durable history
- Paper and live paths share conceptual states; live remains gated
- Update TIOS when lifecycle contracts change
- Rejected signals must include explicit reasons (never silent drop)

## Platform Wiring (`signal_engine`)

| Step | Component | Event / audit |
|------|-----------|---------------|
| Validate | `SignalValidator` | `SignalValidationResult` (`accepted` / `rejected`) |
| Accept | `SignalLifecycleService.register_signal` | `PredictionCreatedEvent` + `AuditRecord` |
| Reject | `SignalLifecycleService.register_signal` | `DomainEvent(VALIDATION_COMPLETED)` payload with reasons; raises `SignalValidationError` |
| Store | `SignalRegistry` | In-memory `SignalRecord` (accepted only) |

## Related Packages

See `../01_GLOBAL_RULES/LAYERS.md` and architecture diagrams.
