"""
Test configuration for 'docker-py' package.
"""
# pyright: reportUnusedImport=false
# pylint: disable=unused-import

import inspect
import os
import sys

SCRIPT_DIR = str(os.path.dirname(inspect.getfile(inspect.currentframe())))  # type: ignore[arg-type]
sys.path.insert(0, os.path.abspath(os.path.join(SCRIPT_DIR, os.pardir)))
