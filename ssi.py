#!/usr/bin/env python
"""CLI entry point wrapper."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from apps.cli.main import main

if __name__ == "__main__":
    main()
