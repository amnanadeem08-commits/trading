# Connector Architecture

## Purpose

The `connectors/` package defines the **market plugin framework**. Every venue (Binance, PMEX, Bybit, OKX, etc.) implements `MarketConnector` without changing platform business logic.

## Dependency Rules

```
connectors/  →  may import  models/
connectors/  →  must NOT import  services/, core/, ml/, ai/, data/
models/      →  must NOT import  connectors/
config/      →  must NOT import  connectors/
```

## Core Components

| Module | Responsibility |
|---|---|
| `base.py` | `MarketConnector` ABC, `LiveSubscription` ABC |
| `registry.py` | Plugin registration and resolution by `market_id` |
| `normalizer.py` | Raw OHLCV → `models.NormalizedBar` |
| `health.py` | `ConnectorHealthStatus`, `HealthCheckResult` |
| `capabilities.py` | Immutable `ConnectorCapabilities` |
| `metadata.py` | `ConnectorMetadata` for audit/versioning |
| `exceptions.py` | Typed connector exceptions |

## MarketConnector Contract

### Required methods

- `connect()`, `disconnect()`, `health_check()`
- `fetch_symbols()`, `fetch_historical_data()`, `fetch_live_data()`
- `subscribe_live()`, `market_metadata()`

### Execution contracts (abstract only in Phase 0)

- `place_order()`, `cancel_order()`, `get_positions()`, `get_account()`

Concrete connectors enforce `SIGNAL_ONLY` and capability flags in later phases.

## Registry Usage

```python
from connectors import ConnectorRegistry, MarketConnector

registry = ConnectorRegistry()
registry.register("crypto:binance", BinanceConnector)
connector = registry.get("crypto:binance")
```

Resolution is by `market_id` only. No `if market` branching.

## Normalization

All OHLCV data must pass through `connectors.normalizer` before leaving the connector layer. Downstream layers receive only `models.NormalizedBar`.

## Health Statuses

| Status | Meaning |
|---|---|
| `CONNECTED` | Operational |
| `DISCONNECTED` | Not connected |
| `DEGRADED` | Partial functionality |
| `FAILED` | Unusable |

## Adding a New Market (Rule R10)

1. Implement `MarketConnector` in `connectors/<market>/connector.py`
2. Declare `ConnectorCapabilities` and `ConnectorMetadata`
3. Register via `ConnectorRegistry.register(market_id, ConnectorClass)`
4. Add entry to `config/markets.yaml` (later phase)
5. No changes to `models/`, `services/`, or intelligence layers

## Legacy Connectors

`connectors/binance_connector.py` and `connectors/psx_connector.py` are pre-Phase 0 modules. They will be wrapped into proper plugins in Phase 2 without deleting legacy behavior until migration is complete.
