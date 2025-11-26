import pytest
from pathlib import Path

#  sys.path tweak
import sys
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))