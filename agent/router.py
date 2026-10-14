from model_provider import generate_structured_response

import json
import re

# Everything ASTI knows how to do with a turn.
# Adding a capability = add it here, add a branch in llm.py's loop
# (later: a dedicated handler module).
INTENTS = {
    "chat",              # greetings, opinions, open-ended talk *about the user's own life/context*
    "recall",            # user is asking ASTI to retrieve a fact it already stored about them
    "general_knowledge", # a question with no personal angle — answered without personal memory
    "code",              # user wants a script/code written — same privacy boundary as
                          # general_knowledge (never loads personal memory), routed to cloud
                          # when allowed since the local model is unreliable at this (10/14)
}

# Deterministic override, checked before the LLM call. A message that
# explicitly references "this/that/the doc/document/file/pdf" is, by
# definition, asking about something in conversation history — never
# general_knowledge (never loads history) or recall (only checks structured
# personal facts, never conversation content). Caught a real failure:
# "what are the grc parts of this doc", asked immediately after a PDF
# upload, classified general_knowledge and got sent to Claude with zero
# context, which correctly replied "I don't see any document attached."
# Python enforces this — it's a clear, mechanical signal, not a judgment
# call worth re-litigating via prompt tuning.
_FILE_REFERENCE_RE = re.compile(
    r"\b(this|that|the)\s+(doc(ument)?|file|pdf)s?\b",
    re.IGNORECASE,
)

# Deterministic override, checked after the file-reference one (a request
# about an uploaded file needs its conversation-history context, which the
# cloud-bound "code" path never loads — file reference wins if both match).
# Catches the clearest "write me code" phrasings without waiting on the LLM
# classifier, same precedent as the file-reference regex above. Added 10/14
# after a real failure: llama3 fabricated an unrelated trivia question
# instead of writing a requested script (see PROJECT_LOG.md).
_CODE_REQUEST_RE = re.compile(
    r"\b(write|give|generate|create|make)\b.{0,20}\b(script|code|function|program|snippet)\b",
    re.IGNORECASE,
)

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
    if _FILE_REFERENCE_RE.search(message):
        return "chat"

    if _CODE_REQUEST_RE.search(message):
        return "code"

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
- code: the user wants a script, program, or code snippet written for them,
  in any programming language. Examples: "write me a bash script that
  renames files", "can you code a function to reverse a string",
  "I need a python program that scrapes a webpage".

User message:
{message}

Return JSON matching the provided schema."""

    raw = generate_structured_response(prompt, INTENT_SCHEMA)

    try:
        intent = json.loads(raw).get("intent")
    except (json.JSONDecodeError, TypeError):
        return "chat"

    return intent if intent in INTENTS else "chat"
