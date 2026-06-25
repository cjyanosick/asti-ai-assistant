import json
import os

MEMORY_FILE = "memory.json"

def load_memory():
    if not os.path.exists(MEMORY_FILE):
        return []
    with open(MEMORY_FILE, "r") as f:
        return json.load(f)

def save_memory(memory):
    with open(MEMORY_FILE, "w") as f:
        json.dump(memory, f, indent=2)

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