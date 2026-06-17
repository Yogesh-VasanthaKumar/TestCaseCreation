import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

class Config:
    NVIDIA_API_KEY = os.getenv("NVIDIA_API_KEY", "")
    NVIDIA_BASE_URL = "https://integrate.api.nvidia.com/v1"
    MODEL_NAME = "nvidia/llama-3.3-nemotron-super-49b-v1.5"
    
    # App Settings
    APP_NAME = "EARS to Gherkin Converter"
    DEFAULT_PREVIEW_MODE = False
    MAX_RETRIES = int(os.getenv("MAX_RETRIES", "3"))
    
    # Qdrant Settings
    QDRANT_URL = os.getenv("QDRANT_URL", "http://localhost:6333")
    QDRANT_API_KEY = os.getenv("QDRANT_API_KEY", "")
