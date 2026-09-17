import datetime

from storage import load_json, save_json

MEMORY_FILE = "memory.json"

def load_memory():
    return load_json(MEMORY_FILE, [])

def save_memory(memory):
    save_json(MEMORY_FILE, memory)

#memory overwrite behavior
def add_memory(user, ai):
    memory = load_memory()

    # detect simple fact updates (color example logic)
    updated = False

    for item in memory:
        if "favorite color" in user.lower() and "color" in item["user"].lower():
            item["user"] = user
            item["ai"] = ai
            updated = True
            break

    if not updated:
        memory.append({"user": user, "ai": ai})

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