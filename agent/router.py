from model_provider import generate_structured_response

import json

# Everything ASTI knows how to do with a turn.
# Adding a capability = add it here, add a branch in llm.py's loop
# (later: a dedicated handler module).
INTENTS = {
    "chat",              # greetings, opinions, open-ended talk *about the user's own life/context*
    "recall",            # user is asking ASTI to retrieve a fact it already stored about them
    "general_knowledge", # a question with no personal angle — answered without personal memory
}

INTENT_SCHEMA = {
    "type": "object",
    "properties": {
        "intent": {
            "type": "string",
            "enum": sorted(INTENTS),
        }
    },
    "required": ["intent"],
}


def classify_intent(message):
    # Model interprets meaning; Python enforces the allowlist.
    # Bad JSON or an unknown label falls back to "chat" — never crash,
    # never route to a capability that doesn't exist.
    prompt = f"""You are an intent classifier for a personal assistant.
Classify the user's message into exactly one intent.

Intents:
- chat: conversation that involves the user's own life, preferences, goals,
  projects, or people — anything where knowing personal context about the
  user would help answer well. Includes the user telling the assistant
  something about themselves.
- recall: the user is explicitly asking the assistant to retrieve a fact it
  already stored about them, such as "what's my favorite color?",
  "what did I say my goal was?", "do you remember my brother's name?".
- general_knowledge: a factual, technical, or open-ended question that has
  nothing to do with the user's own life or stored facts — it would be
  answered the same way no matter who asked it. Examples: "what's the
  capital of France", "explain how TCP handshakes work", "what's a good
  rate limiting algorithm", "who won the world series in 1998".

User message:
{message}

Return JSON matching the provided schema."""

    raw = generate_structured_response(prompt, INTENT_SCHEMA)

    try:
        intent = json.loads(raw).get("intent")
    except (json.JSONDecodeError, TypeError):
        return "chat"

    return intent if intent in INTENTS else "chat"
