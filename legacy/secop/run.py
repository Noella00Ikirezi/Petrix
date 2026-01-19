#!/usr/bin/env python3
"""Script de lancement SecOp Audit."""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from secop.main import main

if __name__ == "__main__":
    main()
