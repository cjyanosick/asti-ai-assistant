import re
from model_provider import generate_response, generate_structured_response
from memory import search_memory, add_memory, load_personal_memory, update_personal_memory

import json
import requests

MEMORY_SCHEMA = {
    "type": "object",
    "properties": {
        "should_remember": {
            "type": "boolean"
        },
        "category": {
            "type": "string"
        },
        "subject": {
            "type": "string"
        },
        "attribute": {
            "type": "string"
        },
        "value": {
            "type": "string"
        }
    },
    "required": [
        "should_remember",
        "category",
        "subject",
        "attribute",
        "value"
    ]
}

ALLOWED_MEMORY_CATEGORIES = {
    "identity",
    "preferences",
    "goals",
    "projects",
    "people",
    "other"
}

def normalize_category(category, attribute=""):
    category = category.lower().strip()
    attribute = attribute.lower().strip()

    if "preference" in attribute:
        return "preferences"

    if "goal" in attribute:
        return "goals"

    if category in ALLOWED_MEMORY_CATEGORIES:
        return category

    if "preference" in category:
        return "preferences"

    if "goal" in category:
        return "goals"

    if "project" in category:
        return "projects"

    if "people" in category or "person" in category:
        return "people"

    if "identity" in category or "name" in category:
        return "identity"

    return "other"

def normalize_key(key):
    key = key.lower().strip()

    key = re.sub(r"[^a-z0-9_]+", "_", key)
    key = re.sub(r"_+", "_", key)
    key = key.strip("_")

    words = key.split("_")

    if len(words) > 5:
        words = words[:5]

    return "_".join(words)


import json

def extract_memory(prompt):
    memory_prompt = f"""
Analyze the user's message and decide whether it contains a useful personal fact worth remembering.

User message:
{prompt}

Only remember information that could be useful later, such as:
- identity
- preferences
- goals
- projects
- people
- other durable personal facts

For remembered information, extract:

For subject:
- Use the real-world topic or domain being discussed.
- Do not use generic words like "user", "person", or "self" unless the fact is literally about identity.
- Prefer short nouns grounded in the message.

- attribute: the type of fact or preference, using short snake_case
- value: the actual user-specific value

Examples:
- "I prefer window seats on trains"
  subject = "train"
  attribute = "seat_preference"
  value = "window"

- "My favorite food is pizza"
  subject = "food"
  attribute = "favorite"
  value = "pizza"

- "My name is Carter"
  subject = "user"
  attribute = "name"
  value = "Carter"

Do not remember casual conversation, greetings, temporary statements, or questions.

Return structured JSON matching the provided schema.
"""

    response = generate_structured_response(memory_prompt, MEMORY_SCHEMA)
    memory = json.loads(response)
    memory["category"] = normalize_category(
        memory["category"],
        memory["attribute"]
    )
    memory["key"] = normalize_key(
        f"{memory['subject']}_{memory['attribute']}"
    )
    return memory
    
#add controlled extractor

#memory draw injection:
def ask_llm(prompt):
    memory_items = search_memory(prompt)
    personal_memory = load_personal_memory() #read structured personal memory
    personal_memory_text = str(personal_memory) #translate into readable text for llama

    memory_text = ""

    for item in memory_items:
        memory_text += f"User: {item['user']}\nAI: {item['ai']}\n\n"

    full_prompt = f"""
You are a helpful AI assistant.

Personal memory is the authoritative source for facts about the user.
If conversation history conflicts with personal memory, always trust personal memory.
Use conversation history only for conversational context.

Conversation history:
{memory_text}

Personal memory:
{personal_memory_text}

User message:
{prompt}
"""

    return generate_response(full_prompt)


#input ask
if __name__ == "__main__":
    while True:
        user_input = input("\nYou: ")

        if user_input.lower() in ["exit", "quit"]:
            break

        response = ask_llm(user_input)
        print("\nAI:", response)

        add_memory(user_input, response)

        memory_update = extract_memory(user_input)

        if memory_update["should_remember"]:
            update_personal_memory(
                memory_update["category"],
                memory_update["key"],
                memory_update["value"]
            )


