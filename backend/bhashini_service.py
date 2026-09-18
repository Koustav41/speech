import base64
import logging
import random
import time
from typing import Dict, Any, Tuple, Optional
import httpx
from config import settings

logger = logging.getLogger("bhashini_service")
logging.basicConfig(level=logging.INFO)

SUPPORTED_LANGUAGES = [
    {"code": "auto", "name": "Auto-Detect", "native": "Auto-Detect (स्वचालित)"},
    {"code": "hi", "name": "Hindi", "native": "हिन्दी"},
    {"code": "bn", "name": "Bengali", "native": "বাংলা"},
    {"code": "ta", "name": "Tamil", "native": "தமிழ்"},
    {"code": "te", "name": "Telugu", "native": "తెలుగు"},
    {"code": "mr", "name": "Marathi", "native": "मराठी"},
    {"code": "gu", "name": "Gujarati", "native": "ગુજરાતી"},
    {"code": "kn", "name": "Kannada", "native": "ಕನ್ನಡ"},
    {"code": "ml", "name": "Malayalam", "native": "മലയാളം"},
    {"code": "pa", "name": "Punjabi", "native": "ਪੰਜਾਬੀ"},
    {"code": "or", "name": "Odia", "native": "ଓଡ଼ିଆ"},
    {"code": "as", "name": "Assamese", "native": "অসমীয়া"},
    {"code": "ur", "name": "Urdu", "native": "اردو"},
    {"code": "en", "name": "English", "native": "English"},
]

MOCK_DATABASE: Dict[str, list[Tuple[str, str]]] = {
    "hi": [
        (
            "नमस्ते, डिजिटल इंडिया और भाषिणी मंच में आपका हार्दिक स्वागत है।",
            "Hello, a warm welcome to Digital India and the Bhashini platform."
        ),
        (
            "आज का मौसम बहुत सुहावना है और तकनीकी प्रगति तेजी से हो रही है।",
            "Today's weather is very pleasant and technological progress is happening rapidly."
        ),
        (
            "यह भारतीय भाषाओं के लिए कृत्रिम बुद्धिमत्ता आधारित अनुवाद सेवा है।",
            "This is an artificial intelligence-based translation service for Indian languages."
        )
    ],
    "bn": [
        (
            "নমস্কার, ডিজিটাল ইন্ডিয়া এবং ভাষিণী প্ল্যাটফর্মে আপনাকে স্বাগতম।",
            "Hello, welcome to Digital India and the Bhashini platform."
        ),
        (
            "আজকের দিনটি খুব সুন্দর এবং আমরা নতুন প্রযুক্তি শিখছি।",
            "Today is a very beautiful day and we are learning new technology."
        )
    ],
    "ta": [
        (
            "வணக்கம், பாஷினி குரல் அறிதல் மற்றும் மொழிபெயர்ப்பு தளத்திற்கு வரவேற்கிறோம்.",
            "Hello, welcome to the Bhashini speech recognition and translation platform."
        ),
        (
            "இன்று நாம் நவீன தகவல் தொழில்நுட்பத்தை இந்திய மொழிகளில் பயன்படுத்துகிறோம்.",
            "Today we are utilizing modern information technology in Indian languages."
        )
    ],
    "te": [
        (
            "నమస్కారం, భాషిణి డిజిటల్ ప్లాట్‌ఫారమ్‌కు మీకు స్వాగతం.",
            "Hello, welcome to the Bhashini digital platform."
        ),
        (
            "భారతీయ భాషల కోసం ఈ వాయిస్ ట్రాన్స్‌క్రిప్షన్ అద్భుతంగా పనిచేస్తుంది.",
            "This voice transcription works wonderfully for Indian languages."
        )
    ],
    "mr": [
        (
            "नमस्कार, भाषिणी वाणी आणि भाषांतर मंचावर आपले स्वागत आहे.",
            "Hello, welcome to the Bhashini speech and translation platform."
        ),
        (
            "तंत्रज्ञानाच्या साहाय्याने आपण भाषांमधील अंतर सहजपणे कमी करू शकतो.",
            "With the help of technology, we can easily bridge the gap between languages."
        )
    ],
    "gu": [
        (
            "નમસ્તે, ભાષિણી ડિજિટલ મંચ પર આપનું હાર્દિક સ્વાગત છે.",
            "Hello, a warm welcome to the Bhashini digital platform."
        ),
        (
            "ટેકનોલોજી દ્વારા ભારતીય ભાષાઓમાં સંવાદ સાધવો હવે ખૂબ સરળ બન્યો છે.",
            "Communicating in Indian languages through technology has now become very easy."
        )
    ],
    "kn": [
        (
            "ನಮಸ್ಕಾರ, ಭಾಷಿಣಿ ಡಿಜಿಟಲ್ ಧ್ವನಿ ಅನುವಾದ ವೇದಿಕೆಗೆ ಸ್ವಾಗತ.",
            "Hello, welcome to the Bhashini digital voice translation platform."
        )
    ],
    "ml": [
        (
            "നമസ്കാരം, ഭാഷിണി വോയ്സ് ട്രാൻസ്ക്രിപ്ഷൻ പ്ലാറ്റ്‌ഫോമിലേക്ക് സ്വാഗതം.",
            "Hello, welcome to the Bhashini voice transcription platform."
        )
    ],
    "pa": [
        (
            "ਸਤਿ ਸ੍ਰੀ ਅਕਾਲ, ਭਾਸ਼ਿਣੀ ਡਿਜੀਟਲ ਪਲੇਟਫਾਰਮ ਵਿੱਚ ਤੁਹਾਡਾ ਸਵਾਗਤ ਹੈ।",
            "Greetings, welcome to the Bhashini digital platform."
        )
    ],
    "or": [
        (
            "ନମସ୍କାର, ଭାଷିଣୀ ଡିଜିଟାଲ୍ ମଞ୍ଚକୁ ଆପଣଙ୍କୁ ସ୍ୱାଗତ।",
            "Hello, welcome to the Bhashini digital platform."
        )
    ],
    "as": [
        (
            "নমস্কাৰ, ভাষিণী ডিজিটেল মঞ্চলৈ আপোনাক স্বাগতম।",
            "Hello, welcome to the Bhashini digital platform."
        )
    ],
    "ur": [
        (
            "آداب، بھاشنی ڈیجیٹల్ پلیٹ فارم پر آپ کا پرخلوص خیر مقدم ہے۔",
            "Greetings, a sincere welcome to the Bhashini digital platform."
        )
    ],
}


class BhashiniService:
    def __init__(self):
        self.user_id = settings.BHASHINI_USER_ID
        self.api_key = settings.BHASHINI_API_KEY
        self.pipeline_id = settings.BHASHINI_PIPELINE_ID
        self.inference_api_key = settings.BHASHINI_INFERENCE_API_KEY
        self.pipeline_config_url = settings.BHASHINI_PIPELINE_CONFIG_URL
        self.compute_url = settings.BHASHINI_COMPUTE_URL
        self.mock_mode = settings.MOCK_MODE

    def is_configured(self) -> bool:
        """Check if Bhashini API keys are configured"""
        return bool(self.user_id and self.api_key)

    async def get_pipeline_config(self, source_lang: str, target_lang: str = "en") -> Dict[str, Any]:
        """Fetch ULCA pipeline configuration with service IDs and inference endpoint"""
        headers = {
            "userID": self.user_id,
            "ulcaApiKey": self.api_key,
            "Content-Type": "application/json"
        }

        payload: Dict[str, Any] = {
            "pipelineTasks": [
                {
                    "taskType": "asr",
                    "config": {
                        "language": {
                            "sourceLanguage": source_lang
                        }
                    }
                },
                {
                    "taskType": "translation",
                    "config": {
                        "language": {
                            "sourceLanguage": source_lang,
                            "targetLanguage": target_lang
                        }
                    }
                }
            ]
        }

        if self.pipeline_id:
            payload["pipelineRequestConfig"] = {"pipelineId": self.pipeline_id}

        async with httpx.AsyncClient(timeout=20.0) as client:
            response = await client.post(
                self.pipeline_config_url,
                json=payload,
                headers=headers
            )
            response.raise_for_status()
            return response.json()

    async def run_pipeline_inference(
        self,
        audio_base64: str,
        source_lang: str,
        target_lang: str = "en",
        audio_format: str = "wav"
    ) -> Dict[str, Any]:
        """
        Execute full pipeline: Regional Audio -> Bhashini ASR -> Transcription -> Bhashini NMT -> Translation
        """
        # If credentials are not set or mock mode is explicitly requested, return mock
        if self.mock_mode or not self.is_configured():
            logger.info("Using simulated Bhashini response (Mock Mode active or missing credentials)")
            return self._generate_mock_result(source_lang, target_lang)

        try:
            # Step 1: Retrieve pipeline configuration
            logger.info(f"Fetching pipeline configuration for {source_lang} -> {target_lang}")
            config_data = await self.get_pipeline_config(source_lang, target_lang)

            pipeline_response_config = config_data.get("pipelineResponseConfig", [])
            callback_url = (
                config_data.get("pipelineInferenceAPIEndPoint", {})
                .get("callbackUrl", self.compute_url)
            )
            inference_key_name = (
                config_data.get("pipelineInferenceAPIEndPoint", {})
                .get("inferenceApiKey", {})
                .get("name", "Authorization")
            )
            inference_key_value = (
                config_data.get("pipelineInferenceAPIEndPoint", {})
                .get("inferenceApiKey", {})
                .get("value", self.inference_api_key)
            )

            asr_service_id = None
            translation_service_id = None

            for task in pipeline_response_config:
                task_type = task.get("taskType")
                configs = task.get("config", [])
                if configs:
                    service_id = configs[0].get("serviceId")
                    if task_type == "asr":
                        asr_service_id = service_id
                    elif task_type == "translation":
                        translation_service_id = service_id

            if not asr_service_id or not translation_service_id:
                raise ValueError("Could not resolve ASR or Translation serviceId from Bhashini pipeline response")

            # Step 2: Call compute endpoint with base64 audio
            compute_headers = {
                inference_key_name: inference_key_value,
                "Content-Type": "application/json"
            }

            compute_payload = {
                "pipelineTasks": [
                    {
                        "taskType": "asr",
                        "config": {
                            "serviceId": asr_service_id,
                            "language": {
                                "sourceLanguage": source_lang
                            },
                            "audioFormat": audio_format,
                            "samplingRate": 16000
                        }
                    },
                    {
                        "taskType": "translation",
                        "config": {
                            "serviceId": translation_service_id,
                            "language": {
                                "sourceLanguage": source_lang,
                                "targetLanguage": target_lang
                            }
                        }
                    }
                ],
                "inputData": {
                    "audio": [
                        {
                            "audioContent": audio_base64
                        }
                    ]
                }
            }

            logger.info(f"Sending audio inference to {callback_url}")
            async with httpx.AsyncClient(timeout=45.0) as client:
                compute_resp = await client.post(
                    callback_url,
                    json=compute_payload,
                    headers=compute_headers
                )
                compute_resp.raise_for_status()
                compute_data = compute_resp.json()

            # Parse pipeline output
            pipeline_results = compute_data.get("pipelineResponse", [])
            transcription = ""
            translation = ""

            for res in pipeline_results:
                task_type = res.get("taskType")
                output = res.get("output", [])
                if output:
                    if task_type == "asr":
                        transcription = output[0].get("source", "")
                    elif task_type == "translation":
                        translation = output[0].get("target", "")

            # If translation didn't arrive via combined pipeline, run separate NMT call
            if transcription and not translation:
                translation = await self.translate_text(
                    text=transcription,
                    source_lang=source_lang,
                    target_lang=target_lang,
                    service_id=translation_service_id,
                    callback_url=callback_url,
                    auth_key=inference_key_value,
                    auth_header=inference_key_name
                )

            return {
                "transcription": transcription,
                "translation": translation,
                "source_language": source_lang,
                "target_language": target_lang,
                "is_mock": False,
                "model_info": f"Bhashini ULCA (ASR: {asr_service_id}, NMT: {translation_service_id})"
            }

        except Exception as exc:
            logger.warning(f"Bhashini API call failed: {exc}. Falling back to high-fidelity mock response.")
            mock_res = self._generate_mock_result(source_lang, target_lang)
            mock_res["error_note"] = f"Upstream API warning: {str(exc)}"
            return mock_res

    async def translate_text(
        self,
        text: str,
        source_lang: str,
        target_lang: str,
        service_id: str,
        callback_url: str,
        auth_key: str,
        auth_header: str
    ) -> str:
        """Fallback direct NMT call if chained inference only returned ASR output"""
        payload = {
            "pipelineTasks": [
                {
                    "taskType": "translation",
                    "config": {
                        "serviceId": service_id,
                        "language": {
                            "sourceLanguage": source_lang,
                            "targetLanguage": target_lang
                        }
                    }
                }
            ],
            "inputData": {
                "input": [
                    {
                        "source": text
                    }
                ]
            }
        }
        headers = {
            auth_header: auth_key,
            "Content-Type": "application/json"
        }
        async with httpx.AsyncClient(timeout=20.0) as client:
            resp = await client.post(callback_url, json=payload, headers=headers)
            resp.raise_for_status()
            data = resp.json()
            return (
                data.get("pipelineResponse", [{}])[0]
                .get("output", [{}])[0]
                .get("target", "")
            )

    def _generate_mock_result(self, source_lang: str, target_lang: str) -> Dict[str, Any]:
        """Generate realistic mock transcription and translation for testing"""
        samples = MOCK_DATABASE.get(source_lang, MOCK_DATABASE["hi"])
        selected_transcript, selected_translation = random.choice(samples)

        return {
            "transcription": selected_transcript,
            "translation": selected_translation,
            "source_language": source_lang,
            "target_language": target_lang,
            "is_mock": True,
            "model_info": "Bhashini Simulated Engine (Demo Mode)"
        }


bhashini_service = BhashiniService()
