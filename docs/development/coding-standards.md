# Coding Standards

## Language

- Python 3.14
- Strict typing required on all new code
- mypy strict is the authoritative type gate

## Formatting

- `black` — line length 100
- `ruff` — lint and import sorting
- 100% formatted code before merge

## Architecture

- Follow Enterprise Architecture Blueprint v2.0 (Rules R1–R18)
- No market-specific logic above `connectors/`
- No `if market` / `if exchange` in `services/`
- Configuration over code (Rule R16)
- Feature flags for major capabilities (Rule R17)

## Models

- All domain contracts inherit from `PlatformModel`
- Models are immutable (`frozen=True`) unless explicitly documented
- Use Pydantic v2 strict mode

## Time

- UTC internally
- Timezone conversion only at presentation layer

## Logging

- Structured logging only
- UTC timestamps
- Correlation IDs on all pipeline operations

## Exceptions

- Use typed exceptions from `models.common`
- No bare `except:`
- No silent failures

## Testing

- Unit, integration, contract, and architecture tests required per phase
- No phase complete without passing all gates

## Dependencies

- Dependency injection where appropriate
- No global mutable state
- No circular imports
