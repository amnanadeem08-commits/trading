# Configuration

## Sources

Configuration loads in this order (later overrides earlier):

1. YAML files in `config/`
2. Environment variables (`.env` + process env)
3. Pydantic Settings validation

## YAML Files

| File | Section |
|---|---|
| `indicators.yaml` | Technical indicator parameters |
| `risk.yaml` | Risk limits |
| `feature_flags.yaml` | Feature flags |
| `markets.yaml` | Market registrations |
| `logging.yaml` | Structured logging |
| `monitoring.yaml` | Monitoring settings |
| `security.yaml` | Security scaffolds |
| `notifications.yaml` | Notification scaffolds |

## Environment Variables

| Variable | Required | Default |
|---|---|---|
| `ENVIRONMENT` | Yes | `development` |
| `APP_NAME` | Yes | `trading-platform` |
| `SCHEMA_VERSION` | Yes | `1.0.0` |
| `TIMEZONE_INTERNAL` | Yes | `UTC` |

Nested overrides use double-underscore delimiter:

```
FEATURE_FLAGS__LIVE_TRADING_ENABLED=false
LOGGING__LEVEL=INFO
```

## Configuration Hash

```python
from config.hash import compute_configuration_hash

config_hash = compute_configuration_hash()
```

Used in `ReproducibilityKey.config_hash` for decision traceability.

## Validation

```bash
python scripts/validate_configuration.py
```

## Safe Defaults (Rule R17)

- `signal_only=true`
- `live_trading_enabled=false`
- `experimental_mode=false`
