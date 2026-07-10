# Contributing Guide

## Before Starting

1. Confirm the authorized phase and task with the project lead.
2. Read `docs/architecture/phase-0.md` and the Enterprise Architecture Contract v2.0.
3. Never implement future phase work without authorization.

## Development Workflow

Every task follows six steps:

1. **Understand** — phase, objective, dependencies, rules
2. **Planning** — goal, files, contracts, risks, tests (STOP if rules violated)
3. **Implementation** — production-quality code only
4. **Self Review** — against R1–R18
5. **Testing** — unit, integration, contract, architecture, mypy, ruff
6. **Completion Report** — summary, validation, next task recommendation

## Quality Gates

```bash
ruff check .
black --check .
mypy models config
pytest tests/ -v
```

## Architecture Change Requests

Architecture is locked. To propose changes, submit an Architecture Change Request (ACR). Do not modify architecture without explicit approval.

## Pull Request Checklist

- [ ] Architecture preserved (R1–R18)
- [ ] Tests added and passing
- [ ] mypy strict passing
- [ ] ruff + black passing
- [ ] Documentation updated
- [ ] No TODO placeholders
- [ ] No temporary hacks
- [ ] Backward compatibility maintained
