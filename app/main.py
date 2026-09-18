import os
import sys
import importlib.util

BACKEND_APP_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "backend", "app")
BACKEND_DIR = os.path.dirname(BACKEND_APP_DIR)

for p in [BACKEND_APP_DIR, BACKEND_DIR]:
    if p not in sys.path:
        sys.path.insert(0, p)

spec = importlib.util.spec_from_file_location("backend_app_main", os.path.join(BACKEND_APP_DIR, "main.py"))
backend_app_main = importlib.util.module_from_spec(spec)
spec.loader.exec_module(backend_app_main)

app = backend_app_main.app
TranscriptionResponse = backend_app_main.TranscriptionResponse
health_check = backend_app_main.health_check
get_languages = backend_app_main.get_languages
get_providers = backend_app_main.get_providers
transcribe_audio = backend_app_main.transcribe_audio

__all__ = ["app", "TranscriptionResponse", "health_check", "get_languages", "get_providers", "transcribe_audio"]
