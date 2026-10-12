from datetime import datetime, timezone

from storage import load_json, save_json

OUTBOUND_LOG_FILE = "outbound_log.json"


def log_outbound_call(provider, model, intent, status, detail=None):
    # Metadata only — never the prompt or the answer. The point is proving a
    # call happened, when, and why, not recording what it contained.
    entries = load_json(OUTBOUND_LOG_FILE, [])

    entry = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "provider": provider,
        "model": model,
        "intent": intent,
        "status": status,
    }
    if detail is not None:
        entry["detail"] = detail

    entries.append(entry)
    save_json(OUTBOUND_LOG_FILE, entries)


def load_outbound_log():
    return load_json(OUTBOUND_LOG_FILE, [])
