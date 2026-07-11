# Global Rulebook

**Authority:** TIOS  
**Applies to:** Every sprint, every agent, every human contributor

## Absolute Rules

1. **Never break architecture.** Import-linter and architecture validators win over convenience.
2. **Never remove tests.** Never reduce coverage below the configured fail-under (88%).
3. **No reverse imports.** Higher layers may depend downward only as defined in contracts.
4. **No duplicated logic.** Prefer shared services and contracts over copy-paste.
5. **SOLID + dependency inversion.** Depend on abstractions/contracts; inject implementations.
6. **Plugin / adapter architecture.** External engines and brokers integrate via adapters/plugins.
7. **No placeholders.** No unfinished TODOs left in merged production code.
8. **No hidden business logic in API routes.** Business logic belongs in services / domain layers.
9. **Never implement outside the active sprint.**
10. **Never skip validation gates.**
11. **Never change completed public APIs** unless explicitly approved via ACP.
12. **Never remove completed documentation.** Never modify historical sprint reports or certification files.
13. **Always keep TIOS synchronized** with the codebase after each completed task.
14. **Never claim guaranteed profits or give financial advice** in product copy or signals framing.
15. **Broker automation stays disabled** until TIOS release docs explicitly approve it.

## Coding Standards Pointers

- `docs/development/coding-standards.md`
- `docs/development/testing.md`
- `docs/development/contributing.md`
- Architecture freeze: `docs/architecture/foundation_freeze.md`

## After Every Task

1. Run all gates in `../05_VALIDATION/GATES.md`
2. Update sprint/task notes / completion report
3. Update `NEXT_TASK.md`, `PROJECT_STATUS.md`, `CHANGELOG.md`, `TECHNICAL_DEBT.md` as needed
4. Run `python scripts/sync_tios_status.py`
5. Run `python scripts/validate_tios.py`
6. Stop — do not continue into the next task without status sync
