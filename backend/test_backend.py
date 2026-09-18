import os
import sys
import io

sys.path.insert(0, os.path.dirname(__file__))

from fastapi.testclient import TestClient
from main import app

client = TestClient(app)

def test_health():
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert "bhashini_configured" in data
    assert "gemini_configured" in data
    print("PASS: /health endpoint working:", data)

def test_providers():
    response = client.get("/providers")
    assert response.status_code == 200
    data = response.json()
    assert len(data["providers"]) == 3
    print("PASS: /providers endpoint working:", [p["name"] for p in data["providers"]])

def test_languages():
    response = client.get("/languages")
    assert response.status_code == 200
    data = response.json()
    assert len(data["languages"]) > 0
    codes = [l["code"] for l in data["languages"]]
    assert "auto" in codes
    assert "bn" in codes
    assert "hi" in codes
    assert "en" in codes
    print(f"PASS: /languages endpoint returned {len(data['languages'])} languages including auto, bn, hi, en")

def test_transcribe_bhashini():
    dummy_wav_header = (
        b"RIFF" + (36 + 1000).to_bytes(4, 'little') + b"WAVE" +
        b"fmt \x10\x00\x00\x00\x01\x00\x01\x00\x80>\x00\x00\x00}\x00\x00\x02\x00\x10\x00" +
        b"data" + (1000).to_bytes(4, 'little') + (b"\x00" * 1000)
    )

    response = client.post(
        "/transcribe",
        files={"audio": ("test_speech.wav", io.BytesIO(dummy_wav_header), "audio/wav")},
        data={"source_language": "hi", "target_language": "en", "provider": "bhashini"}
    )
    assert response.status_code == 200
    data = response.json()
    assert "transcription" in data
    assert "translation" in data
    assert data["provider"] == "bhashini"
    print("PASS: /transcribe (bhashini fallback mock):", data["translation"])

def test_transcribe_gemini_real_speech():
    real_speech_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "test_real_speech.wav")
    if os.path.exists(real_speech_path):
        with open(real_speech_path, "rb") as f:
            audio_bytes = f.read()
    else:
        audio_bytes = (
            b"RIFF" + (36 + 1000).to_bytes(4, 'little') + b"WAVE" +
            b"fmt \x10\x00\x00\x00\x01\x00\x01\x00\x80>\x00\x00\x00}\x00\x00\x02\x00\x10\x00" +
            b"data" + (1000).to_bytes(4, 'little') + (b"\x00" * 1000)
        )

    response = client.post(
        "/transcribe",
        files={"audio": ("real_speech.wav", io.BytesIO(audio_bytes), "audio/wav")},
        data={"source_language": "auto", "target_language": "en", "provider": "gemini"}
    )
    assert response.status_code == 200
    data = response.json()
    assert "transcription" in data
    assert "translation" in data
    assert data["provider"] == "gemini"
    assert data["is_mock"] is False
    print("PASS: /transcribe (gemini LIVE):")
    print("   Transcript:", data["transcription"])
    print("   Translation:", data["translation"])
    print("   Model info:", data.get("model_info"))

if __name__ == "__main__":
    test_health()
    test_providers()
    test_languages()
    test_transcribe_bhashini()
    test_transcribe_gemini_real_speech()
    print("\nALL MULTI-PROVIDER BACKEND TESTS PASSED SUCCESSFULLY!")
