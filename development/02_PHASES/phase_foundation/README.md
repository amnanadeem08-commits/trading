# Foundation — Intelligence Pipeline Freeze

**Status:** Certified `v1.0.0-foundation`  
**Authority:** `FOUNDATION_CERTIFICATION.md`, `docs/architecture/foundation_freeze.md`

## Layer Order

```
Services → Pipeline → Workflow → Plugins → Data → Core → ML → AI → Decision → Risk
```

Execution was authorized after certification; see codebase `execution/`.

## Import Rules

Higher layers may import lower layers. Reverse imports forbidden. Full table in freeze doc and `pyproject.toml`.

## Validation

```bash
python scripts/foundation_certification.py
```
