#!/usr/bin/env python
"""
Utility script to execute the main executable as if it would have been
installed and available in the path.
"""

import sys
import os
sys.path.insert(0, os.getcwd())

from trader.cli import main
main(prog_name='trader')
