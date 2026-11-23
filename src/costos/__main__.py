"""Permite ``python -m costos <comando>``, igual que el comando ``costos``."""

from costos.cli import main

raise SystemExit(main())
