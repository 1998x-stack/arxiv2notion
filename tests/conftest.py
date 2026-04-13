"""Configure pytest to find project modules in the root directory."""
import sys
from pathlib import Path

# Add the project root to sys.path so tests can import project modules directly
sys.path.insert(0, str(Path(__file__).parent.parent))
