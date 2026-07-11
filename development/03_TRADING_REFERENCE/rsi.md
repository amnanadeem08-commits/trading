# RSI

**Type:** Documentation only — not imported by production code.
**Product:** Khaldun Trade / TIOS

## Summary

Relative Strength Index measures momentum on a bounded scale (commonly 0-100).

## Key Points

- Overbought/oversold thresholds are heuristics, not laws
- Divergences require structure confirmation
- Timeframe choice changes interpretation

## Platform Mapping

Platform Signal Engine (`signal_engine.indicators` / `RSIMACDRule`) computes typed RSI for candidates.
Legacy dashboard may still use older helpers — do not grow legacy paths.

## Safety

Not financial advice. No guaranteed profits. Use with paper trading and human review.
