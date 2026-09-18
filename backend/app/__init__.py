import sys
import os

# Enable importing from backend root directory
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from main import app

__all__ = ["app"]
