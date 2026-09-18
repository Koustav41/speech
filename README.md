# Multilingual AI Speech Transcription & Translation Hub (Bhashini + Google Gemini)

A full-stack application that records regional-language speech, sends it to a FastAPI backend, and provides simultaneous speech-to-text transcription and English translation using either **Bhashini AI (ULCA)** or **Google Gemini Multimodal Audio API**.

---

## 🏛 Multi-Provider Architecture

```
                                [ Audio Recording / Upload ]
                                              │
                                              ▼
                                    [ React Frontend ]
                                              │
                     (audio file, source_language, provider: "auto"|"bhashini"|"gemini")
                                              │
                                              ▼
                                    [ FastAPI Backend ]
                                              │
                    ┌─────────────────────────┴─────────────────────────┐
                    ▼                                                   ▼
         [ Bhashini AI Pipeline ]                             [ Google Gemini API ]
        - ULCA ASR (Regional Speech)                       - Multimodal Audio Input
        - ULCA NMT (Translate to EN)                       - Native Script Transcription
                                                           - English Translation
                    └─────────────────────────┬─────────────────────────┘
                                              ▼
                             { transcription, translation, provider }
                                              │
                                              ▼
                                  [ Enhanced Display UI ]
```

---

## 📁 Project Structure

```
speech/
├── .gitignore
├── README.md                          # Comprehensive documentation & setup guide
├── backend/
│   ├── .env.example                  # Environment configuration template
│   ├── .env                          # Local settings (Bhashini & Gemini keys)
│   ├── requirements.txt              # FastAPI, Uvicorn, httpx, pydantic
│   ├── config.py                     # Pydantic BaseSettings management
│   ├── bhashini_service.py           # Bhashini ULCA ASR & NMT client
│   ├── gemini_service.py             # Google Gemini Multimodal Audio client
│   ├── main.py                       # FastAPI server & POST /transcribe endpoint
│   └── test_backend.py               # Multi-provider test suite
└── frontend/
    ├── package.json                  # React 18, Vite, Lucide-react
    ├── vite.config.js                # Vite development server with /api proxy
    ├── index.html                    # Google Fonts & dark theme
    └── src/
        ├── main.jsx                  # React DOM entrypoint
        ├── App.jsx                   # Central state & pipeline coordinator
        ├── index.css                 # Glassmorphic dark design system & animations
        └── components/
            ├── PipelineDiagram.jsx   # 5-step diagram visualizer matching architecture
            ├── ProviderSelector.jsx  # AI Engine switcher (Auto, Bhashini, Gemini)
            ├── LanguageSelector.jsx  # 12+ Indian regional language selector
            ├── AudioRecorder.jsx     # Web Audio API mic recording & canvas visualizer
            └── ResultCard.jsx        # Dual transcription & translation cards with TTS
```

---

## 🔑 API Keys Configuration

Edit `backend/.env` to configure your preferred engine:

```env
# 1. Google Gemini API (Recommended for quick setup)
# Get your free key at: https://aistudio.google.com/app/apikey
GEMINI_API_KEY=your_gemini_api_key_here
GEMINI_MODEL=gemini-1.5-flash

# 2. Bhashini ULCA API
# Get credentials from: https://bhashini.gov.in or https://meity-auth.ulca.ai
BHASHINI_USER_ID=your_ulca_user_id
BHASHINI_API_KEY=your_ulca_api_key
BHASHINI_PIPELINE_ID=your_pipeline_id

# 3. Provider Routing: "auto" | "bhashini" | "gemini"
DEFAULT_PROVIDER=auto

# Offline testing without credentials:
MOCK_MODE=false
```

> **Zero-Friction Offline Demo**: If neither key is entered, the app runs in **Demo Mode**, generating realistic regional Indian language transcripts and English translations automatically.

---

## 🚀 Running the Application

### 1. Start Backend (FastAPI)
```powershell
cd backend
.\venv\Scripts\Activate.ps1
uvicorn main:app --reload --port 8000
```
- API is running at: `http://localhost:8000`
- Swagger documentation: `http://localhost:8000/docs`

### 2. Start Frontend (React + Vite)
```powershell
cd frontend
npm run dev
```
- Open in browser: `http://localhost:5173`

---

## 🔌 Endpoints

- `POST /transcribe`: Transcribes speech and translates to English. Accepts `audio` (file), `source_language` (e.g. `hi`, `ta`, `te`), and `provider` (`auto`, `bhashini`, `gemini`).
- `GET /providers`: Returns engine availability and configuration status.
- `GET /languages`: Returns supported 12+ Indian regional languages with native scripts.
- `GET /health`: Health status of both Bhashini and Google Gemini services.
