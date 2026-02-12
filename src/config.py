import os
import sys
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables once
load_dotenv()

class Config:
    """Central configuration for API keys and constants."""
    JINA_API_KEY = os.getenv("JINA_API_KEY")
    GROQ_API_KEY = os.getenv("GROQ_API_KEY")
    
    # Paths relative to project root (parent of src directory)
    BASE_DIR = Path(__file__).parent.parent
    DATA_DIR = BASE_DIR / "data"
    OUTPUT_DIR = BASE_DIR / "output"

    @classmethod
    def validate_keys(cls):
        """Validates that necessary API keys are present."""
        missing_keys = []
        if not cls.JINA_API_KEY:
            missing_keys.append("JINA_API_KEY")
        if not cls.GROQ_API_KEY:
            missing_keys.append("GROQ_API_KEY")
            
        if missing_keys:
            print(f"Error: Missing API keys in .env file: {', '.join(missing_keys)}")
            sys.exit(1)

# Automatically validate on import to ensure fail-fast behavior
Config.validate_keys()
