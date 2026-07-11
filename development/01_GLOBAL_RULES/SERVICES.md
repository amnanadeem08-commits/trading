# Service Relationships

## `services/`

- Application context, service registry, lifecycle orchestration for foundation services
- Must not import `connectors`

## Business Logic Placement

- Domain logic lives in services / domain packages (`decision`, `risk`, `ml`, pipelines)
- **Not** in API routes, dashboard handlers, or one-off scripts
- Legacy `main.py` / `dashboard.py` are pre-platform and must not become the long-term home of business rules

## Orchestration Neighbors

- `pipeline` — staged processing
- `workflow` — jobs, checkpoints, recovery
- `execution` — execution orchestration (without importing connectors)
- Eventing via `events`

## Rule

New product features add services and contracts first; UI/CLI are thin adapters.
