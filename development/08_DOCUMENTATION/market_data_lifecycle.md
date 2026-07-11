# Market Data Lifecycle

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

## Related Packages

See `../01_GLOBAL_RULES/LAYERS.md` and architecture diagrams.
