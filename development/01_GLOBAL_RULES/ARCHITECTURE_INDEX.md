# Architecture Index

Documentation-only index of platform layers. Educational trading content lives under `../03_TRADING_REFERENCE/`. AI concepts under `../04_AI_REFERENCE/`.

## Vision Pipeline vs Code

| Vision stage | Package / status |
|--------------|------------------|
| Market Data | `market_data` — implemented |
| Historical Storage | `historical` — implemented |
| Feature Engineering | `feature_engineering` — implemented |
| Technical Indicators | Partial via features / legacy CLI — productize in Signal Engine |
| Sentiment Analysis | Planned |
| Machine Learning | `ml`, `training_pipeline`, `model_registry`, Phase 2 stack — implemented (infra) |
| LLM Reasoning | `ai` contracts/agents — foundation present; product loop planned |
| Prediction Engine | Planned productization (V1.0) |
| Confidence Engine | Planned |
| Risk Engine | `risk` — foundation present |
| Validation Engine | Platform validators + planned AI validation loop (V1.3) |
| Paper Trading | `connectors` paper/simulation scaffolds — productize V1.2 |
| Broker Adapter | Future V1.5 — disabled |
| Portfolio | Models/contracts exist; analytics V1.4 |
| Reporting | Planned |

## Layer Docs

- [`LAYERS.md`](LAYERS.md) — package responsibilities
- [`DEPENDENCIES.md`](DEPENDENCIES.md) — allowed/forbidden imports
- [`PLUGINS.md`](PLUGINS.md)
- [`ADAPTERS.md`](ADAPTERS.md)
- [`REPOSITORIES.md`](REPOSITORIES.md)
- [`SERVICES.md`](SERVICES.md)

## Diagrams

See `../09_DIAGRAMS/`.
