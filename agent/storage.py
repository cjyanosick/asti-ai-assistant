import json
import os

from cryptography.fernet import Fernet, InvalidToken

from config import ENCRYPTION_KEY

# Loaded once at import time, same pattern as CLOUD_API_KEY in model_provider.py.
# A malformed key fails loudly here, at startup — that's a real misconfiguration,
# not the same as the key simply being unset.
_cipher = Fernet(ENCRYPTION_KEY.encode()) if ENCRYPTION_KEY else None

_warned_plaintext = False


def _warn_plaintext_once():
    global _warned_plaintext
    if not _warned_plaintext:
        print(
            "[storage] No ENCRYPTION_KEY configured — reading/writing plaintext. "
            "See CLAUDE.md roadmap #4 to enable encryption at rest."
        )
        _warned_plaintext = True


def load_json(path, default):
    if not os.path.exists(path):
        return default

    with open(path, "rb") as f:
        raw = f.read()

    if _cipher:
        try:
            raw = _cipher.decrypt(raw)
        except InvalidToken:
            # Legacy plaintext file written before encryption was enabled.
            # Leave it readable as-is; it gets encrypted on the next save_json.
            pass
    else:
        _warn_plaintext_once()

    return json.loads(raw)


def save_json(path, data):
    raw = json.dumps(data, indent=2).encode()

    if _cipher:
        raw = _cipher.encrypt(raw)
    else:
        _warn_plaintext_once()

    with open(path, "wb") as f:
        f.write(raw)
