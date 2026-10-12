import datetime

from storage import load_json, save_json

MEMORY_FILE = "memory.json"

def load_memory():
    return load_json(MEMORY_FILE, [])

def save_memory(memory):
    save_json(MEMORY_FILE, memory)

#memory overwrite behavior
def add_memory(user, ai, embedding=None):
    memory = load_memory()

    # detect simple fact updates (color example logic)
    updated = False

    for item in memory:
        if "favorite color" in user.lower() and "color" in item["user"].lower():
            item["user"] = user
            item["ai"] = ai
            if embedding is not None:
                item["embedding"] = embedding
            updated = True
            break

    if not updated:
        entry = {"user": user, "ai": ai}
        if embedding is not None:
            entry["embedding"] = embedding
        memory.append(entry)

    save_memory(memory)

#return relevent memories (data pull)
    #fix memory logic
def search_memory(query):
    memory = load_memory()
    results = []

    query_lower = query.lower()

    for item in memory:
        text = (item["user"] + " " + item["ai"]).lower()

        score = 0
        for word in query_lower.split():
            if word in text:
                score += 1

        if score > 0:
            results.append((score, item))

    results.sort(reverse=True, key=lambda x: x[0])

    return [item for score, item in results[:5]]


def _cosine_similarity(a, b):
    dot = sum(x * y for x, y in zip(a, b))
    norm_a = sum(x * x for x in a) ** 0.5
    norm_b = sum(y * y for y in b) ** 0.5

    if norm_a == 0 or norm_b == 0:
        return 0.0

    return dot / (norm_a * norm_b)


def semantic_search(query_embedding, top_k=5):
    # Brute-force cosine similarity — fine at personal-use scale (hundreds
    # of turns, not millions). A real vector index is a later concern if
    # this ever needs to scale, not a day-one requirement.
    # Turns saved before this feature existed have no "embedding" key and
    # are silently skipped — only going-forward history is searchable here.
    memory = load_memory()
    scored = []

    for item in memory:
        if "embedding" not in item:
            continue
        score = _cosine_similarity(query_embedding, item["embedding"])
        scored.append((score, item))

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