import re
from model_provider import generate_response, generate_structured_response, generate_cloud_response, generate_embedding
from memory import (
    add_memory,
    load_memory,
    load_personal_memory,
    update_personal_memory,
    forget_personal_memory,
    export_personal_memory,
    semantic_search,
    semantic_search_recent,
    _cosine_similarity,
)
from router import classify_intent
from outbound_log import load_outbound_log
from cloud_setting import is_cloud_allowed
from config import (
    DEFAULT_PROVIDER,
    DEFAULT_MODEL,
    CLOUD_PROVIDER,
    CLOUD_MODEL,
    CLOUD_API_KEY,
    ENCRYPTION_KEY,
    MAX_CLOUD_PROMPT_CHARS,
    MAX_FILE_READ_CHARS,
)

import io
import json
import os
import requests
from datetime import date
from pypdf import PdfReader
from docx import Document

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
            "[privacy] Cloud disabled — answering general-knowledge "
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

    if stripped.startswith(
        ("how's it going", "hows it going", "what's up", "whats up", "how are you")
    ):
        return True

    # Minimum-content gate (bug found 10/13, see CLAUDE.md): a bare single
    # token — especially a bare number like "2026" sent mid-conversation
    # about something unrelated — has no interpretable subject on its own.
    # extract_memory() would still hallucinate a subject/attribute for it,
    # and reconcile_key() would then trust the model's enum-constrained
    # guess completely, which is exactly how a stray "2026" silently
    # overwrote a real goals.savings_target value in the wild. Blocking
    # should_remember here, before extraction even runs, means
    # reconcile_key() is never offered a chance to match a context-free
    # message onto an existing key at all.
    if len(stripped.split()) <= 1:
        return True

    return False


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
        f"relevant to answering the question.\n\n"
        f"If you do not actually know the answer, or the question references "
        f"something specific you cannot verify (an event, incident, product, "
        f"or detail), say so plainly instead of inventing a plausible-sounding "
        f"answer. A confident but made-up answer is worse than admitting "
        f"you don't know."
    )


def _file_summary_system_prompt():
    return (
        "You are ASTI, the user's personal assistant. Summarize files "
        "clearly and concisely — key points, structure, anything notable. "
        "Respond naturally; skip generic disclaimers."
    )


def _extract_text(filename, raw_bytes):
    # Dispatches by extension, returns (content, error) — exactly one is
    # None. Shared by both file-read entry points so PDF/docx support
    # lands in both at once.
    ext = os.path.splitext(filename)[1].lower()

    if ext == ".pdf":
        try:
            reader = PdfReader(io.BytesIO(raw_bytes))
            text = "\n".join(page.extract_text() or "" for page in reader.pages)
        except Exception:
            return None, (
                f"Could not read {filename} as a PDF — it may be corrupted"
            )
        if not text.strip():
            return None, (
                f"{filename} has no extractable text — it may be a "
                f"scanned/image-only PDF (OCR not supported yet)"
            )
        return text, None

    if ext == ".docx":
        try:
            doc = Document(io.BytesIO(raw_bytes))
            text = "\n".join(p.text for p in doc.paragraphs)
        except Exception:
            return None, f"Could not read {filename} as a .docx file — it may be corrupted"
        return text, None

    if ext == ".doc":
        return None, (
            f"{filename} is an old .doc file (pre-2007 Word format) — not "
            f"supported yet, only .docx"
        )

    try:
        return raw_bytes.decode("utf-8"), None
    except UnicodeDecodeError:
        return None, (
            f"{filename} doesn't look like a plain text file, PDF, or "
            f".docx — unsupported format"
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

    # Persistence (file tools, second slice): save the read into
    # conversation history, same path every chat turn already uses — gets
    # recent-turn continuity and /recall searchability for free, no new
    # injection logic. Deliberately NOT running extract_memory() against
    # this — that pipeline is tuned for short conversational statements,
    # not document summaries, and personal_memory is too trusted a store
    # to risk on an untested extraction path. Best-effort embedding, same
    # pattern as process_turn: still save the turn if embedding fails.
    turn_user = f"[uploaded file: {label}]"
    try:
        embedding = generate_embedding(f"{turn_user}\n{summary}")
    except requests.RequestException:
        embedding = None
    add_memory(turn_user, summary, embedding=embedding)

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
        with open(expanded, "rb") as f:
            raw_bytes = f.read()
    except PermissionError:
        return f"Permission denied reading {path}"

    content, error = _extract_text(os.path.basename(path), raw_bytes)
    if error:
        return error

    return _summarize_file_content(path, content)


def summarize_uploaded_file(filename, raw_bytes):
    # File tools (GUI entry point, upload via app.py's /api/read). No
    # persistence yet — same as /read, this is a one-shot summary, not
    # saved to conversation history or personal memory. Persistence is a
    # deliberately separate future slice.
    content, error = _extract_text(filename, raw_bytes)
    if error:
        return error

    return _summarize_file_content(filename, content)


def build_diagnostics_report():
    # Privacy-safe diagnostics (roadmap #6, last slice): config and counts
    # only, never content. Safe to read aloud or paste anywhere — no values,
    # no keys, no personal data, no prompts.
    try:
        ollama_ok = requests.get("http://localhost:11434/api/tags", timeout=2).status_code == 200
    except requests.RequestException:
        ollama_ok = False

    personal_memory = load_personal_memory()
    categories_populated = sum(1 for v in personal_memory.values() if v)
    total_entries = sum(len(v) for v in personal_memory.values())

    outbound = load_outbound_log()

    history = load_memory()
    embedded_turns = sum(1 for item in history if "embedding" in item)

    lines = [
        f"Local provider/model:  {DEFAULT_PROVIDER} / {DEFAULT_MODEL}",
        f"Local model reachable: {ollama_ok}",
        f"Cloud provider/model:  {CLOUD_PROVIDER} / {CLOUD_MODEL}",
        f"Cloud allowed:         {is_cloud_allowed()}",
        f"Cloud API key set:     {bool(CLOUD_API_KEY)}",
        f"Max outbound chars:    {MAX_CLOUD_PROMPT_CHARS}",
        f"Encryption at rest:    {'on' if ENCRYPTION_KEY else 'off (plaintext)'}",
        f"Personal memory:       {categories_populated}/{len(personal_memory)} categories populated, {total_entries} entries",
        f"Outbound calls logged: {len(outbound)}",
        f"Conversation turns:    {len(history)} total, {embedded_turns} semantically searchable",
    ]
    return "\n".join(lines)


_WORD_RE = re.compile(r"[a-z0-9]+")


def _tokenize(text):
    return set(_WORD_RE.findall(text.lower()))


def _personal_memory_fact_tokens(personal_memory):
    # Meaningful (4+ char) tokens drawn from every stored key name, across
    # every category — e.g. "savings_target" contributes {"savings", "target"}.
    # Used by _filter_related_matches() to recognize when an old semantically-
    # retrieved conversation turn is actually about a fact personal_memory
    # already tracks, so it can be dropped instead of handed to the model.
    tokens = set()
    for entries in personal_memory.values():
        for key in entries:
            tokens.update(t for t in key.split("_") if len(t) >= 4)
    return tokens


def _filter_related_matches(matches, recent_cutoff_idx, fact_tokens):
    # Turns semantic_search_recent()'s raw top-k into a small, trustworthy
    # set of background context. Semantic recall over chat was tried once
    # before and reverted (see PROJECT_LOG.md) because dumping every match
    # into the prompt let a stale old value ($10,000) outrank the current
    # personal_memory value ($50,000) — llama3 didn't reliably resolve the
    # conflict even with explicit "this may be outdated" instructions. This
    # filters deterministically in Python instead of hoping the model picks
    # right:
    #
    # 1. Drop anything already shown via recent_turns (idx >= cutoff) — no
    #    point repeating it in a second block.
    # 2. Drop anything below a relevance floor. semantic_search_recent()
    #    always returns top_k regardless of relevance; a low cosine score
    #    means "nothing better matched", not "this is actually related".
    # 3. Drop anything whose text overlaps a personal_memory key's words —
    #    the deterministic fix for the proven stale-value bug. Personal
    #    memory is trusted alone for any fact it already tracks; a
    #    conflicting old turn about that same fact is never shown at all.
    # 4. Collapse near-duplicate matches (the same underlying topic
    #    resurfacing from different points in history) down to just the
    #    most recent one, using list position as the recency signal (no
    #    per-turn timestamp exists to do this more precisely).
    kept = []

    for score, idx, item in matches:
        if idx >= recent_cutoff_idx:
            continue
        if score < 0.5:
            continue

        text_tokens = _tokenize(f"{item['user']} {item['ai']}")
        if text_tokens & fact_tokens:
            continue

        is_duplicate = False
        for pos, (_, kept_idx, kept_item) in enumerate(kept):
            if _cosine_similarity(item["embedding"], kept_item["embedding"]) > 0.92:
                is_duplicate = True
                if idx > kept_idx:
                    kept[pos] = (score, idx, item)
                break

        if not is_duplicate:
            kept.append((score, idx, item))

    kept.sort(key=lambda x: x[0], reverse=True)
    return kept[:3]


#memory draw injection:
def ask_llm(prompt, mode="chat", reference=None, pending_memory=None):
    if mode == "general_knowledge":
        # No personal angle to this question. personal_memory.json is never
        # loaded on this path at all — not loaded-then-discarded, genuinely
        # never read — so it cannot end up in a request sent to the cloud
        # provider. This is the hard privacy boundary, independent of the
        # cloud-allowed setting.
        system_prompt = _general_system_prompt()

        if is_cloud_allowed():
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

        # User-chosen opt-out, not a silent fallback: cloud disabled means
        # every intent answers locally, even the ones that would normally
        # reach the cloud for better quality on plain factual questions.
        _notify_cloud_disabled_once()
        local_response = generate_response(prompt, system=system_prompt)

        # Deterministic, not model-trusted: tried telling llama3 to admit
        # uncertainty instead of inventing plausible-sounding specifics
        # (events, incidents, dates) — it still confidently fabricated a
        # detailed but entirely fake story on a real test question. Claude
        # handled the identical question correctly, so this is a genuine
        # capability gap in the small local model, not fixable by
        # rewording the instruction. Since the model can't be trusted to
        # flag its own unreliability here, Python does it unconditionally
        # on every local-fallback general_knowledge answer instead.
        return local_response + (
            "\n\n⚠️ Answered locally (cloud is off) — the local model can "
            "confidently state incorrect specifics on topics like events, "
            "incidents, or dates. Verify anything specific independently."
        )

    personal_memory = load_personal_memory() #read structured personal memory

    # Not-yet-confirmed extraction (see process_turn): the response should
    # still read naturally as if the fact were already known ("got it,
    # noted your savings goal as 60k") without actually writing it to disk
    # until the user confirms — see the extraction-noise fix in
    # CLAUDE.md/PROJECT_LOG.md for why saves are no longer silent. Applied
    # to a copy only; load_personal_memory()'s real on-disk data is untouched.
    if pending_memory:
        personal_memory = dict(personal_memory)
        category = dict(personal_memory.get(pending_memory["category"], {}))
        category[pending_memory["key"]] = pending_memory["value"]
        personal_memory[pending_memory["category"]] = category

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

    # Recent turns for conversational continuity, plus filtered semantic
    # recall for topical background (roadmap #7, third slice). The first
    # attempt at semantic recall here was reverted — dumping raw matches
    # into the prompt reintroduced the stale-value bug (an old $10,000 turn
    # outranked the current $50,000 personal_memory value, even with
    # "this may be outdated" instructions). This time the staleness/
    # duplicate problem is solved deterministically in Python
    # (_filter_related_matches), not by asking the model to judge it, so
    # semantic recall can go back into every chat turn instead of staying
    # an explicit, user-invoked-only tool.
    history = load_memory()
    recent_turns = history[-3:]
    recent_cutoff_idx = len(history) - len(recent_turns)

    memory_text = ""

    for item in recent_turns:
        memory_text += f"User: {item['user']}\nAI: {item['ai']}\n\n"

    try:
        query_embedding = generate_embedding(prompt)
        raw_matches = semantic_search_recent(query_embedding, top_k=8)
    except requests.RequestException:
        raw_matches = []

    fact_tokens = _personal_memory_fact_tokens(personal_memory)
    related_matches = _filter_related_matches(raw_matches, recent_cutoff_idx, fact_tokens)

    related_block = ""
    if related_matches:
        related_lines = "\n".join(
            f"- User said: {item['user']}\n  You said: {item['ai']}"
            for _, _, item in related_matches
        )
        related_block = f"""

=== RELATED EARLIER CONVERSATION (background only) ===
{related_lines}
This is older conversation that seems related by topic — surfaced because
it might help you answer naturally, not because it's necessarily current.
If it conflicts with personal memory above, personal memory is correct and
this is outdated. Weave it in naturally if genuinely useful (e.g. "like you
mentioned before...") rather than quoting it verbatim or explaining that
you searched memory for it.
=== END RELATED EARLIER CONVERSATION ===
"""

    # Explicit reference (GUI "reply to this message" click): presented
    # distinctly from the general recent-turns block above, since this
    # isn't ambient context — the user deliberately pointed at this exact
    # text, so it should carry more weight than anything inferred.
    reference_block = (
        f"\n\n=== REFERENCED MESSAGE ===\n"
        f"The user clicked \"reply\" on this exact earlier message and is\n"
        f"asking about THIS specific text, not anything else:\n"
        f"{reference}\n"
        f"=== END REFERENCED MESSAGE ===\n\n"
        f"If the user's message below uses a word like \"that\", \"it\", or "
        f"\"this\" without naming what it means, it refers to the "
        f"referenced message above — treat it exactly as if the user had "
        f"pasted that text in place of the pronoun.\n"
        if reference else ""
    )

    full_prompt = f"""
You are ASTI, a personal assistant for the user. Today's date is {date.today().isoformat()}.
Respond naturally and conversationally — don't list generic AI capability
caveats or disclaimers unless the user specifically asks about them. When
something below connects to earlier conversation, reference it naturally
and confidently, the way an assistant who actually remembers past
conversations would — don't explain how you found it or that you searched
memory for it.

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
{related_block}
{reference_block}
User message:
{prompt}
"""

    return generate_response(full_prompt)


#input ask
# input ask
def process_turn(user_input, reference=None):
    # The actual "have a conversation" pipeline — shared by the CLI loop
    # below and app.py's web UI, so both interfaces run identical logic
    # instead of risking two copies drifting apart over time.
    #
    # `reference`: the GUI lets the user click an earlier message to
    # explicitly reference it, instead of relying on the model to guess
    # what "it"/"that" means from fuzzy recent-turns context — the same
    # kind of ambiguity that caused the "this doc" router bug. An explicit
    # reference is an unambiguous signal, so it deterministically forces
    # chat mode rather than risking the classifier routing it elsewhere
    # (same precedent as the file-reference regex in router.py).
    intent = "chat" if reference else classify_intent(user_input)

    memory_update = extract_memory(user_input)

    # Extraction-noise fix (flagged in CLAUDE.md's GUI Polish list, fixed
    # 10/13): personal_memory is no longer written silently just because
    # the model decided should_remember=True. extract_memory() still gets
    # things wrong sometimes (e.g. "other: asti_who_am_i = 'asti'" from an
    # ambiguous exchange), and for a regulated-industry audience a wrong
    # stored "fact" is closer to a compliance liability than a cosmetic
    # bug. The proposed fact is surfaced to the user as `pending_memory`
    # instead — the CLI prompts for y/N right after the response; the GUI
    # shows a Save/Discard chip — and only written via update_personal_memory()
    # if the user actually confirms it (CLI inline, GUI's new
    # /api/memory/confirm route). ask_llm() still sees the proposed value
    # for this turn's response (see its pending_memory handling) so the
    # reply still reads naturally, without it being committed yet.
    pending_memory = None
    if memory_update["should_remember"]:
        pending_memory = {
            "category": memory_update["category"],
            "key": memory_update["key"],
            "value": memory_update["value"],
        }

    response = ask_llm(user_input, mode=intent, reference=reference, pending_memory=pending_memory)

    # Embed the turn for semantic recall (roadmap #7) — best-effort: if
    # the embedding model isn't available for some reason, still save
    # the turn itself rather than losing conversation history over it.
    try:
        embedding = generate_embedding(f"{user_input}\n{response}")
    except requests.RequestException:
        embedding = None

    add_memory(user_input, response, embedding=embedding)

    return intent, response, pending_memory


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

        intent, response, pending_memory = process_turn(user_input)
        print(f"[intent: {intent}]")
        print("\nAI:", response)

        if pending_memory:
            prompt_text = (
                f"\n[memory] Remember {pending_memory['category']}."
                f"{pending_memory['key']} = {pending_memory['value']}? [y/N]: "
            )
            if input(prompt_text).strip().lower() == "y":
                update_personal_memory(
                    pending_memory["category"],
                    pending_memory["key"],
                    pending_memory["value"],
                )
                print("[memory] Saved.")
            else:
                print("[memory] Discarded.")

