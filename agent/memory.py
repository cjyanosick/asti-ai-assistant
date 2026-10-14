import datetime
import uuid

from storage import load_json, save_json

MEMORY_FILE = "memory.json"


def _now():
    return datetime.datetime.now().isoformat()


def _new_conversation(conv_id, now):
    return {
        "id": conv_id,
        "title": None,
        "created_at": now,
        "updated_at": now,
        "pinned": False,
        "turns": [],
    }


def _load_store():
    raw = load_json(MEMORY_FILE, None)

    if raw is None:
        return {"conversations": {}}

    if isinstance(raw, list):
        # One-time migration (10/14): memory.json used to be a single flat
        # list of every turn ever, shared app-wide. Wrapped into one
        # conversation so the ChatGPT-style "new chat every open, past
        # chats in a sidebar" model has somewhere to show pre-existing
        # history — nothing dropped, just regrouped. Saved immediately so
        # this only runs once.
        now = _now()
        conv_id = "legacy"
        store = {
            "conversations": {
                conv_id: {
                    "id": conv_id,
                    "title": "Earlier conversation",
                    "created_at": now,
                    "updated_at": now,
                    "pinned": False,
                    "turns": raw,
                }
            }
        }
        _save_store(store)
        return store

    return raw


def _save_store(store):
    save_json(MEMORY_FILE, store)


def create_conversation():
    conv_id = uuid.uuid4().hex[:12]
    store = _load_store()
    store["conversations"][conv_id] = _new_conversation(conv_id, _now())
    _save_store(store)
    return conv_id


def get_conversation(conv_id):
    return _load_store()["conversations"].get(conv_id)


def list_conversations():
    # Sidebar listing. Only conversations with at least one turn — an
    # empty "New Chat" the user never used isn't a real conversation
    # worth showing, same as ChatGPT's own sidebar. Pinned conversations
    # sort first (newest-pinned first), then everything else, newest
    # first — `.get("pinned", False)` because conversations created
    # before the pin feature existed have no "pinned" key at all.
    store = _load_store()
    items = [
        {
            "id": c["id"],
            "title": c["title"] or "New chat",
            "created_at": c["created_at"],
            "updated_at": c["updated_at"],
            "pinned": c.get("pinned", False),
        }
        for c in store["conversations"].values()
        if c["turns"]
    ]
    # Stable-sort trick: sort by the secondary key first (newest first
    # within each group), then by the primary key (pinned first) — the
    # second sort preserves the newest-first order within each group
    # since Python's sort is stable.
    items.sort(key=lambda c: c["updated_at"], reverse=True)
    items.sort(key=lambda c: c["pinned"], reverse=True)
    return items


def delete_conversation(conv_id):
    store = _load_store()

    if conv_id not in store["conversations"]:
        return False

    del store["conversations"][conv_id]
    _save_store(store)
    return True


def set_conversation_pinned(conv_id, pinned):
    store = _load_store()

    if conv_id not in store["conversations"]:
        return False

    store["conversations"][conv_id]["pinned"] = bool(pinned)
    _save_store(store)
    return True


def load_memory(conv_id):
    conv = get_conversation(conv_id)
    return conv["turns"] if conv else []


def all_turns():
    # Flattened across every conversation — backs global diagnostics
    # counts and the explicit /recall search, which (unlike live-chat
    # ambient recall, scoped to the active conversation) is meant to
    # search everything, like "find something I said," not ambient
    # context for the model currently answering.
    store = _load_store()
    turns = []
    for conv in store["conversations"].values():
        turns.extend(conv["turns"])
    return turns


#memory overwrite behavior
def add_memory(conv_id, user, ai, embedding=None, source=None):
    store = _load_store()

    if conv_id not in store["conversations"]:
        # Defensive auto-create: the CLI reuses one fixed conversation id
        # across runs and never calls create_conversation() explicitly.
        store["conversations"][conv_id] = _new_conversation(conv_id, _now())

    conv = store["conversations"][conv_id]

    entry = {"user": user, "ai": ai}
    if embedding is not None:
        entry["embedding"] = embedding
    # "local" or "cloud" — which provider actually answered this turn.
    # Backs the GUI's per-message Local/Cloud badge. Turns saved before
    # this existed just have no "source" key; the GUI skips the badge then.
    if source is not None:
        entry["source"] = source
    conv["turns"].append(entry)

    if conv["title"] is None:
        # ChatGPT-style auto title: the first message, truncated — no
        # extra model call just to name a chat.
        conv["title"] = user.strip().replace("\n", " ")[:60] or "New chat"

    conv["updated_at"] = _now()

    _save_store(store)


def _cosine_similarity(a, b):
    dot = sum(x * y for x, y in zip(a, b))
    norm_a = sum(x * x for x in a) ** 0.5
    norm_b = sum(y * y for y in b) ** 0.5

    if norm_a == 0 or norm_b == 0:
        return 0.0

    return dot / (norm_a * norm_b)


def semantic_search(query_embedding, top_k=5):
    # Explicit, user-invoked search (the Recall panel, CLI /recall) —
    # deliberately searches across every conversation, not just the
    # active one; this is "find something I said," not ambient context.
    # Brute-force cosine similarity — fine at personal-use scale (hundreds
    # of turns, not millions). Turns saved before this feature existed
    # have no "embedding" key and are silently skipped.
    scored = []

    for item in all_turns():
        if "embedding" not in item:
            continue
        score = _cosine_similarity(query_embedding, item["embedding"])
        scored.append((score, item))

    scored.sort(reverse=True, key=lambda x: x[0])

    return scored[:top_k]


def semantic_search_recent(query_embedding, conv_id, top_k=5):
    # Same search, scoped to one conversation — ambient in-chat recall
    # (llm.py), matching the "new chat" model: a chat's own earlier turns
    # can surface naturally, but one chat doesn't bleed into another.
    # A conversation's turns list is append-only, so position within it
    # doubles as a recency signal (no separate per-turn timestamp) — used
    # to break ties between two semantically-similar matches by preferring
    # the more recent one.
    turns = load_memory(conv_id)
    scored = []

    for idx, item in enumerate(turns):
        if "embedding" not in item:
            continue
        score = _cosine_similarity(query_embedding, item["embedding"])
        scored.append((score, idx, item))

    scored.sort(reverse=True, key=lambda x: x[0])

    return scored[:top_k]

PERSONAL_MEMORY_FILE = "personal_memory.json"

def load_personal_memory():
    default_memory = {
        "identity": {},
        "preferences": {},
        "goals": {},
        "projects": {},
        "people": {},
        "other": {}
    }

    return load_json(PERSONAL_MEMORY_FILE, default_memory)

def save_personal_memory(memory):
    save_json(PERSONAL_MEMORY_FILE, memory)

def add_personal_memory(category, key, value):
    memory = load_personal_memory()

    if category not in memory:
        memory[category] = {}

    memory[category][key] = value

    save_personal_memory(memory)

def update_personal_memory(category, key, value): #keep memory managemnet seperate from the main conversation logic
    add_personal_memory(category, key, value)

def forget_personal_memory(category, key):
    memory = load_personal_memory()

    if category not in memory or key not in memory[category]:
        return False

    del memory[category][key]
    save_personal_memory(memory)
    return True

def export_personal_memory():
    memory = load_personal_memory()
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"memory_export_{timestamp}.json"

    save_json(filename, memory)
    return filename