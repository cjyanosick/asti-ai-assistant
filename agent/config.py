import os
import keyring
from dotenv import load_dotenv

load_dotenv()

# Local (personal memory, recall, default chat). Overridable via .env so
# switching models/providers doesn't require editing code (roadmap #6, first
# slice: config-driven provider/model choice). Defaults match what's been
# running since roadmap #4/#5 — unset envs change nothing.
DEFAULT_PROVIDER = os.environ.get("ASTI_LOCAL_PROVIDER", "ollama")
DEFAULT_MODEL = os.environ.get("ASTI_LOCAL_MODEL", "llama3:latest")

# Cloud (general-knowledge questions only — never sent personal memory)
CLOUD_PROVIDER = os.environ.get("ASTI_CLOUD_PROVIDER", "anthropic")
CLOUD_MODEL = os.environ.get("ASTI_CLOUD_MODEL", "claude-haiku-4-5")

# User-facing privacy setting: "Cloud by choice" means there has to be a way
# to choose none. Default true (today's behavior unchanged); set
# ASTI_ALLOW_CLOUD=false to force every intent to answer locally, including
# general_knowledge — lower quality on plain factual questions, but ASTI
# never reaches the cloud provider at all.
ALLOW_CLOUD = os.environ.get("ASTI_ALLOW_CLOUD", "true").lower() != "false"
CLOUD_API_KEY = os.environ.get("ANTHROPIC_API_KEY")

# Context minimization (roadmap #6): a hard cap on how much of a message can
# leave the machine in one cloud call, independent of what it contains. Not a
# content filter — just a size ceiling so a misclassified huge paste doesn't
# ship in full. Local-only paths are never truncated; nothing leaves for them.
MAX_CLOUD_PROMPT_CHARS = int(os.environ.get("ASTI_MAX_CLOUD_PROMPT_CHARS", "2000"))

# Encryption at rest for storage.py (roadmap #5: OS-level key management).
# `keyring` reads the OS-native secret store — macOS Keychain here, Windows
# Credential Manager / Linux Secret Service on other platforms — instead of
# a plaintext .env line. Not set anywhere -> storage.py falls back to
# plaintext with a warning.
_KEYCHAIN_SERVICE = "asti-ai-assistant"
_KEYCHAIN_ACCOUNT = "encryption-key"


def _load_encryption_key():
    key = keyring.get_password(_KEYCHAIN_SERVICE, _KEYCHAIN_ACCOUNT)
    if key:
        return key

    # One-time migration path: an ENCRYPTION_KEY left over in .env from before
    # this moved to the OS keychain gets adopted into the keychain here, so
    # every run after this one reads from the keychain only.
    legacy_key = os.environ.get("ENCRYPTION_KEY")
    if legacy_key:
        keyring.set_password(_KEYCHAIN_SERVICE, _KEYCHAIN_ACCOUNT, legacy_key)
        return legacy_key

    return None


ENCRYPTION_KEY = _load_encryption_key()
