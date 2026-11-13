"""Rebuild the low-poly gate from the shared procedural geometry source."""
import os
import runpy
from pathlib import Path

os.environ['MAIN_GATE_LOWPOLY'] = '1'
source = Path(__file__).resolve().parent.parent / '3d' / 'build_gate.py'
runpy.run_path(str(source), run_name='__main__')
