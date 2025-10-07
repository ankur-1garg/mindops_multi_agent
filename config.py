# config.py
import os
from dotenv import load_dotenv

load_dotenv()

# API Keys
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")

# # GitHub Repository Information
GITHUB_REPO_OWNER = "AmanM137"
GITHUB_REPO_NAME = "SAAS-Website-Builder"
GITHUB_BRANCH = "main"

# # AI Models - Using Gemini for all
# # For text-based intent understanding
# INTENT_LLM_MODEL = "models/gemini-2.5-flash"
# CODE_LLM_MODEL = "models/gemini-2.5-flash"    # For complex code generation
# # For image generation and analysis
# VISION_IMAGE_MODEL = "models/gemini-2.5-flash-image"
# config.py
import os
from dotenv import load_dotenv

load_dotenv()

# API Keys
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
# ... other API keys for Jira, GitHub etc.

# Paths
REPO_PATH = os.getenv("REPO_PATH", "./local_repo")

# AI Models
# Stable version with 1M token context
INTENT_LLM_MODEL = "models/gemini-2.5-flash"
# Stable version for code generation
CODE_LLM_MODEL = "models/gemini-2.5-pro"
VISION_IMAGE_MODEL = "models/gemini-2.5-flash-image"  # Image-specific model
TEST_LLM_MODEL = "models/gemini-2.5-pro"      # Stable version for testing

# API Server Config
API_HOST = os.getenv("API_HOST", "0.0.0.0")
API_PORT = int(os.getenv("API_PORT", "8000"))
