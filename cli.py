#!/usr/bin/env python
"""
Entry point for Fennec AI CLI.
"""
import sys
import os

# Add parent directory to path for imports
project_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(project_dir)
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)

from cli.main import main

if __name__ == "__main__":
    main()
