"""Paper-eval matrix sweep toolchain (doc 13).

Phase 1 module: orchestrate multi-cell paper-eval matrix runs against the
existing dashboard HTTP API. No bypass of validator/dispatcher; sweep
calls the same endpoints operators use interactively.

Public surface (import directly from submodules):
    from paper_eval.sweep import (
        Sweeper, DashboardClient, MatrixSpec, Cell, SweepResult,
        load_matrix, main,
    )

CLI entry: `python -m paper_eval.sweep --help`
"""
