import os
import sys

# Ensure backend directory and project root are in sys.path
API_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(API_DIR)
BACKEND_DIR = os.path.join(PROJECT_ROOT, "backend")

for path in [BACKEND_DIR, PROJECT_ROOT]:
    if path not in sys.path:
        sys.path.insert(0, path)

try:
    from backend.main import app
except ImportError:
    from main import app

# Support ASGI/WSGI handlers for Vercel Serverless
try:
    from mangum import Mangum
    handler = Mangum(app)
except ImportError:
    handler = app

__all__ = ["app", "handler"]
