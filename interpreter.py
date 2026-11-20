"""MARIE275 interpreter - entry point.

Usage:
    python interpreter.py program.mas [--input 6 7] [--trace]

All the work is done in the marie package; see marie/cli.py.
"""

import sys

from marie.cli import main

if __name__ == "__main__":
    sys.exit(main())
