import re
from model_provider import generate_response, generate_structured_response, generate_cloud_response, generate_embedding
from memory import add_memory, load_memory, load_personal_memory, update_personal_memory, forget_personal_memory, export_personal_memory, semantic_search
from router import classify_intent
from tasks import add_task, load_tasks, complete_task
from outbound_log import load_outbound_log
from config import (
    DEFAULT_PROVIDER,
    DEFAULT_MODEL,
    CLOUD_PROVIDER,
    CLOUD_MODEL,
    CLOUD_API_KEY,
    ENCRYPTION_KEY,
    ALLOW_CLOUD,
    MAX_CLOUD_PROMPT_CHARS,
    MAX_FILE_READ_CHARS,
)

import json
import os
import requests
from datetime import date

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

_PEOPLE_WORDS = (
    "people", "person", "relationship", "friend", "family",
    "colleague", "coworker", "co-worker",
)

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

    if any(word in category for word in _PEOPLE_WORDS):
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

_notified_cloud_disabled = False


def _notify_cloud_disabled_once():
    global _notified_cloud_disabled
    if not _notified_cloud_disabled:
        print(
            "[privacy] ASTI_ALLOW_CLOUD=false — answering general-knowledge "
            "questions locally instead of via the cloud provider."
        )
        _notified_cloud_disabled = True


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

The category field must be one of: identity, preferences, goals, projects, people, other.
Use "projects" for ongoing work/projects, and "people" for facts about specific people
and relationships.

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

- "I am working on ASTI, a personal AI assistant"
  category = "projects"
  subject = "ASTI"
  attribute = "description"
  value = "personal AI assistant"

- "My brother's name is Jake"
  category = "people"
  subject = "brother"
  attribute = "name"
  value = "Jake"

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

TASK_SCHEMA = {
    "type": "object",
    "properties": {"text": {"type": "string"}},
    "required": ["text"],
}


def extract_task(prompt):
    # Router already decided this message wants a task recorded; this call only
    # cleans the wording into a short imperative phrase for the tasks list.
    task_prompt = f"""Extract the to-do item from the user's message as a short,
imperative action phrase. Drop lead-ins like "remind me to" or "add ... to my list".

User message:
{prompt}

Examples:
- "remind me to call the dentist" -> "call the dentist"
- "add buy milk to my list" -> "buy milk"
- "I need to finish the report by Friday" -> "finish the report by Friday"

Return JSON matching the schema."""

    raw = generate_structured_response(task_prompt, TASK_SCHEMA)

    try:
        text = json.loads(raw).get("text", "").strip()
    except (json.JSONDecodeError, TypeError):
        text = ""

    return text if text else prompt.strip()


def _general_system_prompt():
    # Response-quality fix: without this, the cloud model gets a bare,
    # context-free prompt and defaults to generic "I'm an AI, here are my
    # limitations" boilerplate — including a made-up knowledge cutoff date,
    # since it has nothing real to ground that claim in. Giving it today's
    # actual date and explicit identity/tone framing fixes that directly.
    today = date.today().isoformat()
    return (
        f"You are ASTI, the user's personal AI assistant, answering a "
        f"general-knowledge question with no connection to their personal "
        f"life. Today's date is {today}.\n\n"
        f"Answer directly and naturally, the way you normally would. Do not "
        f"list generic AI limitations, disclaimers, or capability caveats "
        f"unless the user specifically asks about them or they are directly "
        f"relevant to answering the question."
    )


def _file_summary_system_prompt():
    return (
        "You are ASTI, the user's personal assistant. Summarize files "
        "clearly and concisely — key points, structure, anything notable. "
        "Respond naturally; skip generic disclaimers."
    )


def _summarize_file_content(label, content):
    # Shared core for both file-read paths (CLI path-based, GUI upload
    # bytes-based) so there's one summarization implementation, not two
    # that could drift apart. Always local (generate_response, never
    # generate_cloud_response) — file content could be anything, so there's
    # no cloud option here yet, unlike general_knowledge.
    truncated = len(content) > MAX_FILE_READ_CHARS
    if truncated:
        content = content[:MAX_FILE_READ_CHARS]

    user_prompt = f"File: {label}\n\nContent:\n{content}"
    summary = generate_response(user_prompt, system=_file_summary_system_prompt())

    if truncated:
        summary += (
            f"\n\n(This file is long — only the first {MAX_FILE_READ_CHARS} "
            f"characters were read.)"
        )

    return summary


def read_file_summary(path):
    # File tools, first slice (CLI entry point). Plain open(), not
    # storage.py — that boundary is for ASTI's own encrypted data stores,
    # not arbitrary external files the user points it at.
    expanded = os.path.expanduser(path)

    if not os.path.exists(expanded):
        return f"No file found at {path}"

    if os.path.isdir(expanded):
        return f"{path} is a directory, not a file"

    try:
        with open(expanded, "r", encoding="utf-8") as f:
            content = f.read()
    except UnicodeDecodeError:
        return (
            f"{path} doesn't look like a plain text file — binary and PDF "
            f"files aren't supported yet"
        )
    except PermissionError:
        return f"Permission denied reading {path}"

    return _summarize_file_content(path, content)


def summarize_uploaded_file(filename, raw_bytes):
    # File tools (GUI entry point, upload via app.py's /api/read). No
    # persistence yet — same as /read, this is a one-shot summary, not
    # saved to conversation history or personal memory. Persistence is a
    # deliberately separate future slice.
    try:
        content = raw_bytes.decode("utf-8")
    except UnicodeDecodeError:
        return (
            f"{filename} doesn't look like a plain text file — binary and "
            f"PDF files aren't supported yet"
        )

    return _summarize_file_content(filename, content)


def build_diagnostics_report():
    # Privacy-safe diagnostics (roadmap #6, last slice): config and counts
    # only, never content. Safe to read aloud or paste anywhere — no values,
    # no keys, no personal data, no task text, no prompts.
    try:
        ollama_ok = requests.get("http://localhost:11434/api/tags", timeout=2).status_code == 200
    except requests.RequestException:
        ollama_ok = False

    personal_memory = load_personal_memory()
    categories_populated = sum(1 for v in personal_memory.values() if v)
    total_entries = sum(len(v) for v in personal_memory.values())

    tasks = load_tasks()
    tasks_done = sum(1 for t in tasks if t["done"])

    outbound = load_outbound_log()

    history = load_memory()
    embedded_turns = sum(1 for item in history if "embedding" in item)

    lines = [
        f"Local provider/model:  {DEFAULT_PROVIDER} / {DEFAULT_MODEL}",
        f"Local model reachable: {ollama_ok}",
        f"Cloud provider/model:  {CLOUD_PROVIDER} / {CLOUD_MODEL}",
        f"Cloud allowed:         {ALLOW_CLOUD}",
        f"Cloud API key set:     {bool(CLOUD_API_KEY)}",
        f"Max outbound chars:    {MAX_CLOUD_PROMPT_CHARS}",
        f"Encryption at rest:    {'on' if ENCRYPTION_KEY else 'off (plaintext)'}",
        f"Personal memory:       {categories_populated}/{len(personal_memory)} categories populated, {total_entries} entries",
        f"Tasks:                 {len(tasks)} total, {tasks_done} done",
        f"Outbound calls logged: {len(outbound)}",
        f"Conversation turns:    {len(history)} total, {embedded_turns} semantically searchable",
    ]
    return "\n".join(lines)


#memory draw injection:
def ask_llm(prompt, mode="chat"):
    if mode == "task":
        task = add_task(extract_task(prompt))
        return f"Added to your list: {task['text']}"

    if mode == "general_knowledge":
        # No personal angle to this question. personal_memory.json is never
        # loaded on this path at all — not loaded-then-discarded, genuinely
        # never read — so it cannot end up in a request sent to the cloud
        # provider. This is the hard privacy boundary, independent of ALLOW_CLOUD.
        system_prompt = _general_system_prompt()

        if ALLOW_CLOUD:
            # Context minimization: cap what actually leaves the machine,
            # independent of content — a misclassified huge paste shouldn't
            # ship in full just because nothing else caught it. Local paths
            # are never truncated; truncation only matters for what's sent out.
            truncated = len(prompt) > MAX_CLOUD_PROMPT_CHARS
            cloud_question = prompt[:MAX_CLOUD_PROMPT_CHARS] if truncated else prompt

            response = generate_cloud_response(
                cloud_question, intent="general_knowledge", system=system_prompt
            )
            if truncated:
                response += (
                    f"\n\n(Your message was long — only the first "
                    f"{MAX_CLOUD_PROMPT_CHARS} characters were sent to the cloud provider.)"
                )
            return response

        # User-chosen opt-out, not a silent fallback: ASTI_ALLOW_CLOUD=false
        # means every intent answers locally, even the ones that would
        # normally reach the cloud for better quality on plain factual questions.
        _notify_cloud_disabled_once()
        return generate_response(prompt, system=system_prompt)

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

    # Recent turns only, in order — conversational continuity without dredging
    # stale facts out of deep history via keyword match. Semantic recall was
    # tried here too (roadmap #7, second slice) and reverted: injecting
    # semantically-matched older turns reintroduced the exact stale-value bug
    # this comment used to warn about — llama3 answered a savings-goal
    # question from a seeded old turn ($10,000) instead of personal memory
    # ($50,000), even with explicit "this section may be outdated" language
    # added to the prompt. One round of stronger instructions didn't fix it
    # reliably across phrasings, so semantic recall stays an explicit,
    # user-invoked tool (/recall) rather than silent context injection.
    # Durable facts live in personal memory — still the only thing recall
    # mode trusts (see the "authoritative" instruction below).
    recent_turns = load_memory()[-3:]

    memory_text = ""

    for item in recent_turns:
        memory_text += f"User: {item['user']}\nAI: {item['ai']}\n\n"

    full_prompt = f"""
You are ASTI, a personal assistant for the user. Today's date is {date.today().isoformat()}.
Respond naturally and conversationally — don't list generic AI capability
caveats or disclaimers unless the user specifically asks about them.

Personal memory below is the authoritative source for facts about the user.
Conversation history is only for conversational tone and context.
For any fact or value about the user, use personal memory. If the conversation
history shows a different value for that fact, it is outdated — ignore it and
use the personal memory value.

Do not invent facts, numbers, amounts, dates, or history about the user.
If something is not in personal memory, say you do not have it rather than guessing.

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
def process_turn(user_input):
    # The actual "have a conversation" pipeline — shared by the CLI loop
    # below and app.py's web UI, so both interfaces run identical logic
    # instead of risking two copies drifting apart over time.
    intent = classify_intent(user_input)

    # A to-do isn't a personal fact — skip extraction so a task never also
    # lands as a near-duplicate entry in personal_memory.json.
    if intent != "task":
        memory_update = extract_memory(user_input)

        if memory_update["should_remember"]:
            update_personal_memory(
                memory_update["category"],
                memory_update["key"],
                memory_update["value"]
            )

    response = ask_llm(user_input, mode=intent)

    # Embed the turn for semantic recall (roadmap #7) — best-effort: if
    # the embedding model isn't available for some reason, still save
    # the turn itself rather than losing conversation history over it.
    try:
        embedding = generate_embedding(f"{user_input}\n{response}")
    except requests.RequestException:
        embedding = None

    add_memory(user_input, response, embedding=embedding)

    return intent, response


if __name__ == "__main__":
    while True:
        user_input = input("\nYou: ")

        if user_input.lower() in ["exit", "quit"]:
            break

        # Deterministic vault commands — no model involved, so they bypass
        # extraction/routing entirely rather than becoming another intent.
        if user_input.strip() == "/memory":
            memory = load_personal_memory()
            print("\n--- Personal Memory ---")
            for category, entries in memory.items():
                if not entries:
                    continue
                print(f"\n{category}:")
                for key, value in entries.items():
                    print(f"  {key}: {value}")
            print()
            continue

        if user_input.strip().startswith("/forget"):
            parts = user_input.split(maxsplit=2)
            if len(parts) != 3:
                print("\nUsage: /forget <category> <key>")
                continue
            _, category, key = parts
            if forget_personal_memory(category, key):
                print(f"\nForgot {category}.{key}")
            else:
                print(f"\nNo entry found at {category}.{key}")
            continue

        if user_input.strip().startswith("/edit"):
            parts = user_input.split(maxsplit=3)
            if len(parts) != 4:
                print("\nUsage: /edit <category> <key> <value>")
                continue
            _, category, key, value = parts
            if category not in ALLOWED_MEMORY_CATEGORIES:
                valid = ", ".join(sorted(ALLOWED_MEMORY_CATEGORIES))
                print(f"\nUnknown category '{category}'. Valid categories: {valid}")
                continue
            update_personal_memory(category, key, value)
            print(f"\nSet {category}.{key} = {value}")
            continue

        if user_input.strip() == "/export":
            filename = export_personal_memory()
            print(f"\nExported personal memory to {filename}")
            continue

        if user_input.strip() == "/tasks":
            tasks = load_tasks()
            print("\n--- Tasks ---")
            if not tasks:
                print("(no tasks)")
            for task in tasks:
                mark = "x" if task["done"] else " "
                print(f"[{mark}] {task['id']}. {task['text']}")
            print()
            continue

        if user_input.strip().startswith("/done"):
            parts = user_input.split(maxsplit=1)
            if len(parts) != 2 or not parts[1].strip().isdigit():
                print("\nUsage: /done <task id>")
                continue
            task_id = int(parts[1].strip())
            if complete_task(task_id):
                print(f"\nMarked task {task_id} done")
            else:
                print(f"\nNo task with id {task_id}")
            continue

        if user_input.strip() == "/outbound":
            entries = load_outbound_log()
            print("\n--- Outbound Calls ---")
            if not entries:
                print("(no outbound calls yet)")
            for entry in entries[-20:]:
                detail = f" ({entry['detail']})" if "detail" in entry else ""
                print(
                    f"{entry['timestamp']}  {entry['intent']:18} "
                    f"{entry['provider']}/{entry['model']}  {entry['status']}{detail}"
                )
            print()
            continue

        if user_input.strip() == "/status":
            print("\n--- Diagnostics ---")
            print(build_diagnostics_report())
            print()
            continue

        if user_input.strip().startswith("/recall"):
            parts = user_input.split(maxsplit=1)
            if len(parts) != 2:
                print("\nUsage: /recall <query>")
                continue
            query_embedding = generate_embedding(parts[1])
            results = semantic_search(query_embedding, top_k=5)
            print("\n--- Semantic Recall ---")
            if not results:
                print("(no embedded conversation turns yet — only turns saved "
                      "since roadmap #7 are searchable this way)")
            for score, item in results:
                print(f"[{score:.3f}] User: {item['user']}")
                print(f"         AI: {item['ai'][:150]}")
            print()
            continue

        if user_input.strip().startswith("/read"):
            parts = user_input.split(maxsplit=1)
            if len(parts) != 2:
                print("\nUsage: /read <path>")
                continue
            print("\n--- File Summary ---")
            print(read_file_summary(parts[1].strip()))
            print()
            continue

        intent, response = process_turn(user_input)
        print(f"[intent: {intent}]")
        print("\nAI:", response)

