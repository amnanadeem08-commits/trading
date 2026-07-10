# Dependency Audit Report

**Generated:** 2026-07-10T02:41:51.080051+00:00

## Layer Order

```
Services → Pipeline → Workflow → Plugins → Data → Core → ML → AI → Decision → Risk
```

## Pipeline Layer Index

- `connectors`
- `data`
- `core`
- `ml`
- `ai`
- `agents`
- `decision`
- `risk`
- `execution`

## Scan Results

- Files scanned: 322
- Total violations: 0
- Reverse import violations: 0
- Forbidden import violations: 0

## Forbidden Import Rules (Foundation Layers)

- `services` must not import: connectors
- `pipeline` must not import: ai, api, connectors, dashboard, execution, ml, risk
- `workflow` must not import: ai, api, connectors, dashboard, execution, ml, risk
- `plugins` must not import: ai, api, connectors, dashboard, execution, llm, ml, risk
- `data` must not import: ai, api, connectors, core, dashboard, decision, execution, llm, ml, research, risk
- `core` must not import: ai, api, connectors, dashboard, decision, execution, llm, ml, research, risk
- `ml` must not import: ai, api, connectors, dashboard, decision, execution, llm, research, risk
- `ai` must not import: api, connectors, dashboard, decision, execution, research, risk
- `decision` must not import: api, connectors, dashboard, execution, research, risk
- `risk` must not import: api, connectors, dashboard, execution, research
