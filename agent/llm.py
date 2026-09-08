import re
from model_provider import generate_response, generate_structured_response
from memory import search_memory, add_memory, load_personal_memory, update_personal_memory
from router import classify_intent

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


_QUESTION_RE = re.compile(
    r"^\s*(what|whats|what's|why|how|hows|how's|when|where|who|whos|who's|which|whose|"
    r"do|does|did|are|is|was|were|can|could|would|should|will|tell me|remind me)\b",
    re.IGNORECASE,
)
_SMALL_TALK = {
    "hi", "hey", "hello", "yo", "sup", "thanks", "thank you", "ty", "ok", "okay",
    "k", "cool", "nice", "great", "awesome", "lol", "haha", "yeah", "yep", "nope",
    "sure", "np",
}


def is_noninformative(message):
    # Questions and greetings never carry a durable fact. Catching them here keeps
    # the model from "remembering" a question and overwriting real memory with a
    # garbage value — structure enforced in Python, not asked of the model.
    m = message.strip().lower()

    if not m:
        return True

    if m.endswith("?") or _QUESTION_RE.match(m):
        return True

    stripped = m.rstrip("!.").strip()

    if stripped in _SMALL_TALK:
        return True

    return stripped.startswith(
        ("how's it going", "hows it going", "what's up", "whats up", "how are you")
    )


def reconcile_key(prompt, category, candidate_key):
    # Small models don't produce a stable subject/attribute for the same fact
    # ("savings target" vs "saving amount"), so a plain key never overwrites
    # reliably. Show the model what ASTI already stores in this category and let
    # it decide "same fact or new one"; Python constrains the answer to a known
    # key or the sentinel "__new__", and falls back to candidate_key on anything odd.
    existing = load_personal_memory().get(category, {})

    if not existing:
        return candidate_key

    options = sorted(existing.keys()) + ["__new__"]

    schema = {
        "type": "object",
        "properties": {"key": {"type": "string", "enum": options}},
        "required": ["key"],
    }

    existing_lines = "\n".join(f"- {k}: {existing[k]}" for k in sorted(existing.keys()))

    reconcile_prompt = f"""Existing {category} entries (key: value):
{existing_lines}

New user statement: "{prompt}"

If this statement sets a new value for one of the entries above, return that key.
If it is about something different, return "__new__".

Examples:
- "bump my savings to 60k", with key savings_target present -> savings_target
- "I want to run a marathon", with no running entry present -> __new__

Return JSON matching the schema."""

    raw = generate_structured_response(reconcile_prompt, schema)

    try:
        choice = json.loads(raw).get("key")
    except (json.JSONDecodeError, TypeError):
        return candidate_key

    return choice if choice in existing else candidate_key


def extract_memory(prompt):
    if is_noninformative(prompt):
        return {"should_remember": False}

    memory_prompt = f"""
Analyze the user's message and decide whether it contains a useful personal fact worth remembering.

User message:
{prompt}

Remember information when it expresses a durable personal fact that may be useful in future conversations.

Examples of information that SHOULD be remembered:
- identity details
- likes, dislikes, and preferences
- goals and updated goals
- ongoing projects
- important people and relationships
- recurring habits or routines
- durable personal choices
- long-term plans

Examples of information that should NOT be remembered:
- greetings
- casual small talk
- questions
- temporary emotions
- one-time statements with no future usefulness

Statements such as "I prefer dark mode", "I am working on ASTI", and "my brother's name is Jake" should be remembered.

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
    subject = memory["subject"].lower()
    attribute = memory["attribute"].lower()

    if attribute in subject:
        raw_key = subject
    else:
        raw_key = f"{subject}_{attribute}"

    memory["key"] = normalize_key(raw_key)

    if memory.get("should_remember"):
        memory["key"] = reconcile_key(prompt, memory["category"], memory["key"])

    return memory
    
#add controlled extractor

#memory draw injection:
def ask_llm(prompt, mode="chat"):
    personal_memory = load_personal_memory() #read structured personal memory
    personal_memory_text = str(personal_memory) #translate into readable text for llama

    if mode == "recall":
        # Direct fact lookup: answer only from structured personal memory,
        # skip conversation-history retrieval, and admit when the fact isn't stored.
        recall_prompt = f"""You are a personal assistant answering a question about the user.
Use ONLY the personal memory below. Do not guess.
If the answer is not in personal memory, say you don't have that stored yet.
Answer in one short sentence.

Personal memory:
{personal_memory_text}

User question:
{prompt}
"""
        return generate_response(recall_prompt)

    memory_items = search_memory(prompt)

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
# input ask
if __name__ == "__main__":
    while True:
        user_input = input("\nYou: ")

        if user_input.lower() in ["exit", "quit"]:
            break

        memory_update = extract_memory(user_input)

        if memory_update["should_remember"]:
            update_personal_memory(
                memory_update["category"],
                memory_update["key"],
                memory_update["value"]
            )

        intent = classify_intent(user_input)
        print(f"[intent: {intent}]")

        response = ask_llm(user_input, mode=intent)
        print("\nAI:", response)

        add_memory(user_input, response)

