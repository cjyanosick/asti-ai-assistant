Phase 1 Core AI
- Local LLM
- Persistent memory
- Memory retrieval
COMPLETE

Phase 2 Personal Assistant
- Agent router
- Task management
- Structured memory
- Planning
- File tools

Phase 3
- Document retrieval (RAG)
- Embeddings
- Vector database

Phase 4
- Security Agent
- Log analysis
- Threat modeling
- Cloud security

Phase 5
- GUI
- Docker
- Cloud deployment #maybe



//2026-06-24

Confirmed Ollama installation.
Command:
ollama list
Result:
llama3:latest detected
Outcome:
Local language model successfully installed and available for use.

Added:
Model Inference
Prompt injection of memory
file based persistence
retrievel behavior

//2026-06-25

## Milestone: Working AI Agent v1


### What was built:
- Local LLM integration using Ollama (Llama3)
- Python-based agent loop (CLI interface)
- Persistent memory system using JSON storage
- Memory retrieval + scoring system
- Memory overwrite logic for conflicting facts
- Structured prompt injection for context awareness

### Result:
The agent can now:
- Remember user preferences across sessions
- Update facts when corrected
- Retrieve relevant past context dynamically





8/16/2026

## Milestone: Structured Personal Memory

### What was built
- Added a dedicated `personal_memory.json` for structured user facts.
- Added functions to load and save structured personal memory.
- Added the ability to add and overwrite stored facts.
- Added automatic memory extraction for recognized user information.
- Connected automatic extraction to the main assistant loop.
- Verified that memory persists after the assistant exits.

### Architecture improvement
The assistant now separates structured personal facts from conversation history.

### Example
A statement such as:
"My favorite color is orange"

is extracted and stored as:

{
  "preferences": {
    "favorite_color": "orange"
  }
}

### Result
The assistant can now automatically recognize, update, and persist structured personal information across sessions.


8/21/2026

## Milestone: Model Provider Abstraction

### What changed
- Added a dedicated `model_provider.py` module.
- Removed direct Ollama communication from the main assistant logic.
- `llm.py` now sends prompts through the model provider layer.
- Verified that existing structured memory continues to work after the change.

### Architecture improvement
ASTI's assistant logic is no longer directly tied to Ollama.

Current flow:

User → ASTI → Model Provider → Ollama → Local Model

### Why this matters
This creates the foundation for supporting interchangeable AI models and providers without rebuilding the assistant.

ASTI will remain local/private by default, while the architecture can later support optional additional local or cloud providers.


## Milestone: Structured Memory as Source of Truth

### What changed
- Fixed an issue where old conversation history could override current personal facts.
- Updated prompt logic so structured personal memory is authoritative.
- Conversation history is now treated as context only.

### Result
When conversation history conflicts with structured personal memory, ASTI now uses the structured value.

## Milestone: Configurable Model Provider Routing

### What changed
- Added a configurable default provider.
- Added provider-routing logic inside `model_provider.py`.
- Ollama remains the default local provider.
- Unsupported providers now raise a clear error instead of failing silently.

### Architecture improvement
ASTI now routes model requests through a provider layer rather than assuming a single backend.

Current flow:

User → ASTI → Model Provider → Selected Provider → Model

### Result
The assistant continues to work with Ollama while the codebase is now prepared for additional local or optional cloud providers later.

## Milestone: Interchangeable Local Models

### What changed
- Installed Qwen 2.5 3B as a second local model.
- Switched ASTI from Llama 3 to Qwen through `config.py`.
- Fixed the provider configuration import path.
- Verified that ASTI's existing memory and conversation logic worked without modification.

### Architecture improvement
ASTI is no longer dependent on a specific local language model.

Current architecture:

ASTI → Model Provider → Ollama → Selected Local Model

Available tested models:
- Llama 3
- Qwen 2.5 3B

### Result
The underlying model can now be changed through configuration while the assistant, memory system, and application logic remain unchanged.

## Milestone: Generalized Preference Extraction

### What changed
- Expanded personal memory extraction beyond favorite color.
- Added regex-based parsing for statements such as:
  - "my favorite food is pizza"
  - "my favorite movie is Interstellar"
  - "my favorite sport is football"
- Preference names are normalized into structured memory keys.

### Result
ASTI can now automatically store multiple types of user preferences instead of relying on a hardcoded favorite-color rule.

8/23/2026

## Milestone: AI-Powered Structured Memory Extraction

### What changed
- Replaced hardcoded memory extraction rules with model-based structured extraction.
- Added a JSON schema for memory decisions.
- Added structured-response support through the model provider layer.
- Qwen now determines whether a user message contains durable personal information.
- Automatically classifies memories into categories such as identity, preferences, goals, projects, people, or other.
- Automatically generates a structured key and value.
- Connected extraction to persistent personal memory storage.

### Example
User statement:
"I prefer aisle seats when I fly"

Extracted memory:
{
  "category": "preferences",
  "key": "preference_for_aisle_seats_when_flying",
  "value": "prefer aisle seats when flying"
}

### Result
ASTI can now learn new types of personal information without requiring a new hardcoded rule for every topic.


## Milestone: Semantic Memory Normalization

### What changed
- Expanded AI-based memory extraction to produce semantic fields:
  - subject
  - attribute
  - value
- Added Python-side category normalization.
- Added deterministic memory key generation from subject and attribute.
- Improved extraction prompts so the model identifies the real-world topic instead of generic subjects like "user".

### Example
User statement:
"I prefer window seats on trains"

Extracted memory:
{
  "category": "preferences",
  "subject": "train",
  "attribute": "seat_preference",
  "value": "window",
  "key": "train_seat_preference"
}

### Result
ASTI can now convert natural-language personal information into cleaner, reusable structured memory without requiring topic-specific hardcoded rules.

## Milestone: Memory-First Response Flow

### What changed
- Moved personal memory extraction and updates before response generation.
- ASTI now saves durable user updates before asking the model to respond.
- Fixed cases where the assistant referenced an outdated value in the same message where the user corrected it.

### Example
User:
"I actually want to save 25000"

Previous behavior:
- ASTI could answer using the old savings goal.
- Memory updated only after the response.

New behavior:
- ASTI updates the stored goal first.
- The response immediately reflects the new value.

### Result
ASTI's responses are now consistent with the latest structured personal memory on the same turn.


9/7/2026
## Milestone: Centralized Storage Layer

### What changed
- Routed conversation-memory file access (`load_memory`, `save_memory`) through `storage.py`.
- `memory.py` no longer calls `open()` / `json` directly — both conversation memory
  and structured personal memory now go through the `load_json` / `save_json` boundary.
- Removed now-unused `json` / `os` imports from `memory.py`.

### Architecture improvement
`storage.py` is now the single choke point for reading and writing ASTI's memory files.
This is the boundary where an encryption layer will later be inserted without touching
feature code.

Current flow:

ASTI Features → memory.py → storage.py → filesystem

### Note
`memory_backup.py` still uses direct file access but is an orphaned backup copy that
nothing imports.

### Result
The storage abstraction is centralized. Encryption at rest can be added at the
`storage.py` boundary later without changing memory logic.


9/8/2026

### What changed
- Added `router.py` — a dispatch layer that classifies each user message into
  one intent before ASTI responds.
- Model classifies against a fixed schema; Python validates against an allowlist
  (`INTENTS`) and falls back to `chat` on bad output or an unknown label.
- Current intents: `chat` (conversation) and `recall` (user asking ASTI to
  retrieve a fact it already stored).
- `ask_llm()` gained a `mode` argument. In `recall` mode it answers only from
  structured personal memory, skips conversation-history retrieval, and admits
  when a fact isn't stored instead of guessing.
- Main loop now classifies, prints `[intent: …]`, and dispatches.

### Architecture improvement
New capabilities (tasks, planning, file tools) become new intents + handlers
rather than more branches piled into the main loop.

### Result
ASTI decides what a message *wants* before answering, and fact-lookup questions
now get a focused, memory-only response path.

## Milestone: Reliable Personal-Memory Updates

### What changed
- Removed the `goals` special case that forced every goal into one key
  (`current_goal`); goals now use semantic keys like every other category.
- Added `reconcile_key()`: before writing, ASTI shows the model the keys it
  already stores in that category and asks whether the new statement updates one
  of them. Updates land on the existing key instead of creating a near-duplicate
  (`savings_target` vs `saving_amount`). Python validates the choice against the
  real key list; unknown/garbage answers fall back to a fresh key.
- Added `is_noninformative()`: a deterministic Python guard that drops questions
  and greetings before extraction, so asking "what is my savings goal?" can never
  overwrite the goal with a garbage value. Also skips a model call.
- Switched the default model from `qwen2.5:3b` to `llama3:latest`. The 3B model
  could not reliably classify goal updates or produce clean subject/attribute
  fields; llama3 handles both.

### Known limitation
Bare pronoun follow-ups with no noun ("instead make it 50k") lack the context to
resolve what "it" refers to and can land in the wrong category. Explicit
phrasings ("make my savings goal 50k", "I want to save 50k") work.

### Result
Restating or revising a stored fact updates it in place; a genuinely new fact
gets its own entry; questions and small talk never mutate memory.

## Milestone: Recent-Turn Conversation Context

### What changed
- Chat responses now receive the last 3 conversation turns in order, instead of
  the top 5 keyword-matched turns from all of history.
- Keyword search over full history (`search_memory`) pulled in the *evolution* of
  a fact — e.g. every past savings figure — and the model would sometimes answer
  with a stale value. Recent turns give conversational continuity without that.
- `search_memory()` is retained for later semantic recall (embeddings, Phase 3).

### Result
Chat answers stay consistent with structured personal memory; old superseded
values in the conversation log no longer leak into responses.

