import os
from dotenv import load_dotenv

load_dotenv()

# Local (personal memory, recall, default chat)
DEFAULT_PROVIDER = "ollama"
DEFAULT_MODEL = "llama3:latest"

# Cloud (general-knowledge questions only — never sent personal memory)
CLOUD_PROVIDER = "anthropic"
CLOUD_MODEL = "claude-haiku-4-5"
CLOUD_API_KEY = os.environ.get("ANTHROPIC_API_KEY")
