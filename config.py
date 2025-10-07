# config.py
import os
from dotenv import load_dotenv

load_dotenv()

# API Keys
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")

# AI Models
INTENT_LLM_MODEL = "gemini-2.0-flash"
CODE_LLM_MODEL = "gemini-2.0-flash"
VISION_IMAGE_MODEL = "gemini-2.0-flash"
TEST_LLM_MODEL = "gemini-2.0-flash"

# API Server Config
API_HOST = os.getenv("API_HOST", "0.0.0.0")
API_PORT = int(os.getenv("API_PORT", "8000"))