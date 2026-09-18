import json
import asyncio
import logging
import random
import re
from typing import Dict, Any, Optional
import httpx
from config import settings
from bhashini_service import MOCK_DATABASE

logger = logging.getLogger("gemini_service")
logging.basicConfig(level=logging.INFO)

class GeminiService:
    def __init__(self):
        self.api_key = settings.GEMINI_API_KEY
        self.model = settings.GEMINI_MODEL or "gemini-3.5-flash-lite"
        self.mock_mode = settings.MOCK_MODE

    def get_candidate_models(self) -> list[str]:
        """Return prioritized list of Gemini models for automatic failover"""
        primary = self.model or "gemini-3.5-flash-lite"
        # Prioritize verified healthy fast models, followed by fallback alternatives
        fallback_list = [
            primary,
            "gemini-3.5-flash-lite",
            "gemini-flash-lite-latest",
            "gemini-3.1-flash-lite",
            "gemini-3.6-flash",
        ]
        # De-duplicate while preserving order
        ordered = []
        for m in fallback_list:
            if m and m not in ordered:
                ordered.append(m)
        return ordered

    def is_configured(self) -> bool:
        """Check if Gemini API key is configured"""
        return bool(self.api_key and len(self.api_key.strip()) > 10)

    async def run_audio_pipeline(
        self,
        audio_base64: str,
        source_lang: str,
        target_lang: str = "en",
        audio_format: str = "wav"
    ) -> Dict[str, Any]:
        """
        Send audio to Google Gemini API for simultaneous regional transcription and English translation.
        Includes automatic model failover if a model is overloaded (503) or quota exhausted (429).
        """
        if self.mock_mode or not self.is_configured():
            logger.info("Using simulated Gemini response (Gemini API key not configured or Mock Mode active)")
            return self._generate_mock_result(source_lang, target_lang)

        # Normalize audio format to proper MIME type accepted by Gemini
        mime_type_map = {
            "wav": "audio/wav",
            "wave": "audio/wav",
            "x-wav": "audio/wav",
            "webm": "audio/webm",
            "mp3": "audio/mp3",
            "mpeg": "audio/mp3",
            "ogg": "audio/ogg",
            "opus": "audio/ogg",
            "flac": "audio/flac",
            "m4a": "audio/mp4",
            "mp4": "audio/mp4",
            "aac": "audio/aac",
        }
        clean_format = audio_format.lower().replace("audio/", "").replace(";codecs=opus", "").strip()
        mime_type = mime_type_map.get(clean_format, "audio/wav")

        lang_prompt = (
            f"The audio contains speech in regional language code '{source_lang}'."
            if source_lang and source_lang != "auto"
            else "The audio contains speech in any Indian regional language or English. Detect the spoken language automatically."
        )

        prompt = (
            "You are an expert multilingual speech recognition (ASR) and translation system.\n"
            f"{lang_prompt}\n\n"
            "Strict Instructions:\n"
            "1. VERBATIM SPEECH RECOGNITION: Listen attentively to the attached audio. Transcribe the exact words spoken by the human speaker word-for-word.\n"
            "   - If spoken in an Indian regional language (e.g. Bengali/বাংলা, Hindi/हिन्दी, Tamil/தமிழ், Telugu/తెలుగు, Gujarati/ગુજરાતી, Marathi/मराठी, Kannada/ಕನ್ನಡ, etc.), write in its authentic native script.\n"
            "   - If words are spoken in English or code-mixed (loan words like 'mobile', 'hospital', 'train', 'hello', or Hinglish/Bengali-English), keep those English words in English letters.\n"
            "   - Never invent, summarize, or substitute words. Reflect the speaker's exact spoken content.\n"
            "2. ACCURATE ENGLISH TRANSLATION: Translate the transcription accurately into fluent, natural English.\n"
            "   - If the speech is already in English, provide the verbatim text as the translation.\n"
            "3. SILENCE / UNINTELLIGIBLE AUDIO: If the audio contains only background noise, silence, or no recognizable human speech, return empty strings: {\"transcription\": \"\", \"translation\": \"\"}.\n"
            "4. Return ONLY a valid JSON object matching this schema without preamble or markdown:\n"
            '{"transcription": "<exact spoken words>", "translation": "<english translation>"}\n'
        )

        payload = {
            "contents": [
                {
                    "role": "user",
                    "parts": [
                        {"text": prompt},
                        {
                            "inlineData": {
                                "mimeType": mime_type,
                                "data": audio_base64
                            }
                        }
                    ]
                }
            ],
            "generationConfig": {
                "temperature": 0.0,
                "responseMimeType": "application/json"
            }
        }

        candidate_models = self.get_candidate_models()
        data = None
        last_error = None
        successful_model = None

        for model_name in candidate_models:
            url = f"https://generativelanguage.googleapis.com/v1beta/models/{model_name}:generateContent?key={self.api_key}"
            logger.info(f"Connecting to Google Gemini API (model: {model_name}, MIME: {mime_type})")

            model_succeeded = False
            for attempt in range(2):
                try:
                    async with httpx.AsyncClient(timeout=30.0) as client:
                        resp = await client.post(url, json=payload, headers={"Content-Type": "application/json"})

                        if resp.status_code == 200:
                            data = resp.json()
                            successful_model = model_name
                            model_succeeded = True
                            logger.info(f"Gemini model {model_name} responded successfully (200 OK)")
                            break

                        # Extract error details
                        err_detail = ""
                        try:
                            err_detail = resp.json().get("error", {}).get("message", "")
                        except Exception:
                            err_detail = resp.text[:120]

                        logger.warning(
                            f"Gemini model '{model_name}' returned HTTP {resp.status_code}: {err_detail}."
                        )
                        last_error = f"{model_name} HTTP {resp.status_code}: {err_detail}"

                        if resp.status_code in [404, 429]:
                            # Model not found or quota limit for this model, immediately try next candidate
                            break
                        elif resp.status_code in [500, 502, 503, 504]:
                            # Temporary spike, brief sleep and retry or next model
                            if attempt == 0:
                                await asyncio.sleep(0.5)
                                continue
                            else:
                                break
                        else:
                            resp.raise_for_status()

                except (httpx.ReadTimeout, httpx.ConnectTimeout) as te:
                    last_error = f"{model_name} Timeout: {te}"
                    logger.warning(f"Gemini API timeout on {model_name} (attempt {attempt + 1})")
                    if attempt == 0:
                        await asyncio.sleep(0.5)
                    else:
                        break
                except Exception as e:
                    last_error = f"{model_name} Error: {e}"
                    logger.warning(f"Gemini call to {model_name} failed: {e}")
                    break

            if model_succeeded:
                break

        if not data or not successful_model:
            logger.error(f"All Gemini candidate models failed: {last_error}.")
            if self.mock_mode:
                mock_res = self._generate_mock_result(source_lang, target_lang)
                mock_res["error_note"] = f"Gemini notice: {str(last_error)}"
                return mock_res
            raise RuntimeError(f"Google Gemini transcription error: {last_error}")

        try:
            candidates = data.get("candidates", [])
            if not candidates:
                raise ValueError("No candidate output returned from Gemini API")

            raw_text = candidates[0].get("content", {}).get("parts", [{}])[0].get("text", "").strip()

            # Clean possible markdown wrapping
            cleaned_text = raw_text
            if "```" in cleaned_text:
                cleaned_text = re.sub(r"^```[a-zA-Z]*\n", "", cleaned_text)
                cleaned_text = re.sub(r"\n?```$", "", cleaned_text).strip()

            # Robust JSON extraction
            transcription = ""
            translation = ""
            json_match = re.search(r"\{[\s\S]*\}", cleaned_text)

            if json_match:
                try:
                    parsed = json.loads(json_match.group(0))
                    transcription = str(parsed.get("transcription", "")).strip()
                    translation = str(parsed.get("translation", "")).strip()
                except Exception:
                    pass

            # Fallback regex search if json.loads failed
            if not transcription or not translation:
                trans_m = re.search(r'"transcription"\s*:\s*"([^"\\]*(?:\\.[^"\\]*)*)"', cleaned_text)
                transl_m = re.search(r'"translation"\s*:\s*"([^"\\]*(?:\\.[^"\\]*)*)"', cleaned_text)
                if trans_m:
                    transcription = trans_m.group(1).encode('utf-8').decode('unicode_escape', errors='ignore')
                if transl_m:
                    translation = transl_m.group(1).encode('utf-8').decode('unicode_escape', errors='ignore')

            # Handle empty audio or silence
            if not transcription:
                if not translation:
                    transcription = "No audible speech detected. Please speak closer to the microphone and try again."
                    translation = "No audible speech detected."
                else:
                    transcription = translation
            elif not translation:
                translation = transcription

            return {
                "transcription": transcription,
                "translation": translation,
                "source_language": source_lang,
                "target_language": target_lang,
                "is_mock": False,
                "provider": "gemini",
                "model_info": f"Google Gemini ({successful_model})"
            }

        except Exception as exc:
            logger.error(f"Gemini response parsing failed: {exc}")
            if self.mock_mode:
                mock_res = self._generate_mock_result(source_lang, target_lang)
                mock_res["error_note"] = f"Gemini notice: {str(exc)}"
                return mock_res
            raise RuntimeError(f"Failed to parse transcription from Gemini API: {str(exc)}")

    def _generate_mock_result(self, source_lang: str, target_lang: str) -> Dict[str, Any]:
        """Generate realistic mock transcription and translation for testing"""
        lookup_lang = source_lang if source_lang in MOCK_DATABASE else "hi"
        samples = MOCK_DATABASE.get(lookup_lang, MOCK_DATABASE["hi"])
        selected_transcript, selected_translation = random.choice(samples)

        return {
            "transcription": selected_transcript,
            "translation": selected_translation,
            "source_language": source_lang,
            "target_language": target_lang,
            "is_mock": True,
            "provider": "gemini",
            "model_info": f"Google Gemini ({self.model} Demo Mode)"
        }

gemini_service = GeminiService()
