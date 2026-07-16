# Technical Debt



**Last updated:** 2026-07-16  

**Rule:** Add entries when discovered; resolve only via active sprint tasks.



## Open



| ID | Severity | Item | Impact | Proposed resolution |

|----|----------|------|--------|---------------------|

| TD-001 | Medium | Legacy entrypoints `main.py`, `dashboard.py`, `config.py` | Confuse newcomers; outside foundation gates | Document as legacy; migrate only under explicit sprint |

| TD-002 | Medium | Root README previously dashboard-only | Weak SSOT discovery | Mitigated by TIOS + README rewrite (Sprint-000) |

| TD-003 | Low | Limited real ML engine backends beyond stub + ORT adapter | Inference path incomplete for non-ORT | Expand adapters only in ML sprints |

| TD-004 | Medium | Product Signal Engine not unified with platform layers | Dual mental models (legacy CLI vs platform) | Mitigated by SIG-001…008; legacy cleanup later |

| TD-006 | Low | Sentiment / confidence / RAG product surfaces mostly roadmap | Vision diagram ahead of code | Document as planned; implement in later versions |

| TD-007 | Medium | Broker live trading must remain disabled | Safety | Keep V1.5 gated; feature flags off |

| TD-SIG-01 | Medium | Legacy dashboard remains parallel signal UX | Drift vs platform ExplainableSignal path | Later deprecation sprint |

| TD-PAPER-03 | Low | Fill uses `paper_trading.fill` not `connectors.SimulationEngine` | Acceptable for V1.2; connector bridge optional later | Revisit only if connector parity required |

| TD-PAPER-04 | Low | Performance metrics max drawdown requires caller-provided PnL ledger | Fill executor uses instance ledger, not global singleton | Wire shared ledger or orchestrator helper in future sprint if needed |
| TD-BT-01 | Low | Backtest fill pricing duplicates PAPER-004 math in `backtesting/engine/pricing.py` | Layer separation forbids `backtesting` → `paper_trading` import | Extract shared pricing contract to `models/` or thin shared module in future sprint if parity audit required |
| TD-BT-02 | Low | Paper `FillConfig.fill_fraction` has no backtest equivalent (backtest assumes 1.0) | Partial-fill simulation differs if fraction < 1 | Add optional fill_fraction to `BacktestConfig` only if product requires partial fills in replay |



## Resolved



| ID | Resolved in | Notes |

|----|-------------|-------|

| TD-SIG-02 | SIG-001…008 | Signal Engine V1.0 path accepted |

| TD-SIG-03 | SIG-006 (partial) | Confidence binders landed; sentiment engines still later |

| TD-PAPER-01 | PAPER-007 | E2E readiness + performance metrics complete |

| TD-005 | PAPER-007 | Paper trading product loop productized through V1.2 acceptance |



## Process



1. Never silently delete debt entries — mark resolved with sprint ID.

2. Debt does not authorize out-of-sprint work.

3. Sync this file when closing any sprint that touches debt.

