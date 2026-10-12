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


9/14/2026

## Milestone: Hybrid Local/Cloud Routing (general_knowledge intent)

### What changed
- Added a third intent, `general_knowledge`, alongside `chat` and `recall`.
- Added `generate_cloud_response()` in `model_provider.py`, calling the
  Claude API for questions with no personal angle.
- `config.py` now loads a `.env` file (via `python-dotenv`) for the API key
  instead of any key ever being hardcoded in source.
- `.gitignore` added — blocks `.env`, and stops tracking `memory.json` /
  `personal_memory.json`, which had been committed in plain text since the
  project started.

### Architecture / privacy decision
`ask_llm()` returns early for `general_knowledge` before `load_personal_memory()`
is ever called — personal memory is not loaded, not just excluded from the
prompt, when a question doesn't need it. That is the boundary: personal data
never reaches the cloud provider, regardless of what future cloud calls get
added later.

### Why
Local models (llama3:latest) meaningfully underperform on general-knowledge
questions with no relation to the user. Splitting "needs my context" from
"doesn't" gets frontier-model quality on the second category without
weakening the privacy guarantee on the first.

### Result
General questions now route to Claude; personal chat and recall are
unchanged and still fully local.



9/13/2026

### What changed
- New `tasks.py`: `add_task`/`load_tasks`/`complete_task`, through `storage.py`.
- `router.py` gained a 4th intent, `task` — a brand-new concrete action item,
  distinct from an ongoing goal/target (which stays `chat`) or a question about a
  stored fact (`recall`). Took several prompt iterations to avoid boundary collisions.
- `llm.py`: `extract_task()` cleans wording into a short imperative phrase;
  `ask_llm(mode="task")` adds it and confirms. `/tasks` (view) and `/done <id>`
  (complete) are deterministic commands, same pattern as `/memory`/`/forget`.
- Reordered the main loop to classify intent before extraction, skipping
  `extract_memory` for `task` messages — otherwise a task would also write a
  near-duplicate entry into personal memory.
- `tasks.json` added to `.gitignore` (personal data).

### Known limitations
- "set my goal to X" can misfile as `task` when X reads as an action verb.
- Pre-existing: statements like "my favorite color is teal" can misfile as `recall`.

### Result
Roadmap item #3 (tasks) has its first working slice: add via natural language,
view/complete via commands. Projects/notes/documents are separate future slices.

9/17/2026

## Milestone: Memory Vault UI complete (roadmap #1)

### What changed
- `/edit <category> <key> <value>`: deterministic command, validates category
  against `ALLOWED_MEMORY_CATEGORIES`, writes via `update_personal_memory()`.
- `/export`: new `export_personal_memory()` in `memory.py` writes a timestamped
  JSON snapshot (`memory_export_<timestamp>.json`) via `storage.py`'s
  `save_json` — no direct file I/O, same as the rest of the vault.
- `.gitignore` updated to block `agent/memory_export_*.json` — an export is a
  second plaintext copy of personal data and needed the same protection as
  `personal_memory.json` itself.

### Result
Roadmap item #1 done: `/memory` (inspect), `/edit`, `/forget` (delete), and
`/export` now cover the full Memory Vault UI as originally scoped.

9/17/2026

## Fix: projects/people categories now classify correctly (roadmap #2)

### What changed
- `extract_memory()`'s prompt in `llm.py` never told the model the actual
  `category` vocabulary (identity/preferences/goals/projects/people/other) —
  it only listed reasons to remember things, and worked examples covered
  preference/goal/identity-shaped facts only. `normalize_category()` had
  keyword fallbacks for preference/goal/identity but nothing reliably routing
  project/people facts, so both categories sat empty.
- Added an explicit category list plus one worked example each for
  "projects" and "people" to the prompt.

### Verification
Called `extract_memory()` directly (no writes) against test statements:
- "I'm working on a new woodworking project in the garage" -> category: projects
- "My sister Emma just moved to Denver" -> category: people
Regression-checked preferences/goals/identity still classify correctly.

### Result
Roadmap item #2 done: all six memory categories now populate correctly from
natural conversation, not just the original three.

9/28/2026

## Fix: pinned dependencies, added project venv

### What changed
- Homebrew upgraded Python to 3.14.7 on 9/23, replacing the global
  site-packages ASTI's dependencies (`python-dotenv`, `requests`) lived in.
  `python3 llm.py` was broken as a result, and Homebrew's Python now refuses
  global `pip install` outright (PEP 668).
- Added `venv/` (gitignored) and `requirements.txt` (`python-dotenv`,
  `requests`, `cryptography` — the last one is prep for roadmap #4).
- Run command going forward: `python3 -m venv venv && venv/bin/pip install
  -r requirements.txt`, then `venv/bin/python3 llm.py`.

### Result
ASTI runs again, and dependencies are now isolated from system Python so a
future OS/Homebrew upgrade can't silently break the agent the same way.

## Milestone: Encryption at rest (roadmap #4)

### What changed
- `storage.py`'s `load_json`/`save_json` now transparently encrypt with
  Fernet (from the `cryptography` package), keyed by a new `ENCRYPTION_KEY`
  in `agent/.env` — same pattern as `ANTHROPIC_API_KEY`. No caller changes:
  `memory.py` and `tasks.py` are untouched.
- No key configured -> falls back to plaintext with a one-time printed
  warning, doesn't break. A malformed key fails loudly at import instead —
  that's a real misconfiguration, not "feature not enabled yet."
- Legacy plaintext files stay readable after encryption turns on (a decrypt
  failure falls back to reading the raw bytes as plaintext JSON) and
  self-migrate to encrypted on their next save — no separate migration
  script needed.
- Migrated the real `personal_memory.json`, `memory.json`, and `tasks.json`
  to encrypted today rather than waiting for opportunistic re-save.

### Verification
Backed up all three real data files, re-saved them through the new key,
confirmed none are valid plaintext JSON anymore, then reloaded and diffed
against the backups — byte-for-byte identical content. Confirmed a
malformed `ENCRYPTION_KEY` raises immediately on import. Ran a full
`ask_llm(mode="recall")` call end-to-end through the encrypted files —
correct answer, no behavior change visible to the user.

### Result
Roadmap item #4 done: `personal_memory.json`, `memory.json`, and
`tasks.json` are no longer plaintext on disk. Note: this is disk encryption
only — it does not touch the separate git-history plaintext exposure
(`agent/CLAUDE.md`, "Known housekeeping issue"), which is still open.
Roadmap #5 (OS-level key management) is the natural next step for this —
`ENCRYPTION_KEY` currently lives in a `.env` file, not a real key store.

## Milestone: OS-level key management (roadmap #5)

### What changed
- `config.py` now reads `ENCRYPTION_KEY` via the `keyring` package — macOS
  Keychain on this machine, Windows Credential Manager / Linux Secret
  Service on other platforms, one API. `storage.py` is untouched; it still
  just reads `ENCRYPTION_KEY` from config, same as roadmap #4.
- One-time migration on first run: if the keychain has no key yet but a
  legacy `ENCRYPTION_KEY` line still exists in `.env`, that value is adopted
  into the keychain and returned. Every run after that reads keychain only.
- Removed the `ENCRYPTION_KEY` line from `.env` entirely once the migration
  was confirmed — the key no longer lives in any plaintext file.

### Verification
Ran the migration once and confirmed the key landed in Keychain and matched
the `.env` value. Then removed the `ENCRYPTION_KEY` line from `.env` and
re-ran — `config.ENCRYPTION_KEY` still loaded correctly from Keychain alone.
Full `ask_llm(mode="recall")` smoke test against the already-encrypted data
files passed with the keychain-only key.

### Result
Roadmap item #5 done: the key that unlocks `personal_memory.json`,
`memory.json`, and `tasks.json` lives in the OS keychain, not a dotenv
file. Closes the gap flagged at the end of roadmap #4.

## Milestone: Config-driven provider/model choice (roadmap #6, first slice)

### What changed
- `DEFAULT_PROVIDER`, `DEFAULT_MODEL`, `CLOUD_PROVIDER`, `CLOUD_MODEL` in
  `config.py` now read from env vars (`ASTI_LOCAL_PROVIDER`,
  `ASTI_LOCAL_MODEL`, `ASTI_CLOUD_PROVIDER`, `ASTI_CLOUD_MODEL`) via the
  same `.env` pattern already used for secrets, defaulting to today's
  hardcoded values. Switching models no longer requires editing code.
- `model_provider.py`'s dispatch logic is unchanged — unsupported providers
  still raise a clear error. No second cloud provider is implemented yet,
  so this slice is about the *model/provider choice* being config-driven,
  not about adding new provider integrations.

### Verification
Confirmed no env vars set produces identical values to before the change;
confirmed `ASTI_LOCAL_MODEL` override is picked up; ran a full smoke test
through both the local `recall` path and the cloud `general_knowledge`
path — both still work.

### Result
First slice of roadmap #6 done. Remaining pieces of the Full Model Gateway
(user-facing privacy settings, outbound-call enforcement/auditing, context
minimization beyond "don't load personal memory," privacy-safe
diagnostics) are separate future slices.

## Milestone: ASTI_ALLOW_CLOUD privacy setting (roadmap #6, second slice)

### What changed
- `config.ALLOW_CLOUD` (env `ASTI_ALLOW_CLOUD`, default `true`) is the first
  user-facing privacy setting — "Cloud by choice" needs a way to choose none.
- When false, `ask_llm()`'s `general_knowledge` branch answers via the local
  model instead of `generate_cloud_response()`, with a one-time printed
  notice. This only affects `general_knowledge` — the one intent that would
  otherwise reach the cloud at all.
- The privacy boundary from roadmap #5.5 (general_knowledge never loads
  personal memory) holds either way — both the cloud and local sub-branches
  `return` before `load_personal_memory()` is reached.

### Verification
Confirmed default behavior is unchanged; with `ASTI_ALLOW_CLOUD=false` the
same question answers locally with the notice printed once; `recall`/`chat`
intents unaffected.

### Result
Second slice of roadmap #6 done. Remaining: outbound-call
enforcement/auditing, context minimization, privacy-safe diagnostics.

## Milestone: Outbound-call auditing (roadmap #6, third slice)

### What changed
- New `outbound_log.py`: `log_outbound_call()` appends an entry every time
  ASTI actually reaches a cloud provider — timestamp, provider, model,
  which intent triggered it, status (`ok`/`error`/`no_key`). Metadata only,
  never the prompt or answer. Goes through `storage.py`, so it's encrypted
  at rest automatically, same as everything else.
- Logging lives inside `generate_cloud_response()` in `model_provider.py` —
  the only place that actually knows whether the call succeeded.
  `ask_llm()`'s `general_knowledge` branch passes `intent="general_knowledge"`
  as an audit label.
- New `/outbound` command (same pattern as `/memory`/`/tasks`) lists the
  last 20 entries — an audit log nobody can see isn't much of an audit log.

### Verification
A real cloud call logs `status=ok` with no content captured. The
`ASTI_ALLOW_CLOUD=false` local-fallback path never reaches
`generate_cloud_response`, so it correctly never logs anything. A missing
API key logs `status=no_key`. Confirmed the log file is encrypted on disk,
same as `personal_memory.json`/`memory.json`/`tasks.json`.

### Result
Third slice of roadmap #6 done. Remaining: context minimization beyond
"don't load personal memory," privacy-safe diagnostics.

## Milestone: Outbound prompt size cap (roadmap #6, fourth slice)

### What changed
- `MAX_CLOUD_PROMPT_CHARS` (env `ASTI_MAX_CLOUD_PROMPT_CHARS`, default 2000)
  caps how much of a message can leave the machine in one cloud call,
  independent of content — a misclassified huge paste doesn't ship in full
  just because nothing else caught it. Not a content filter, a size ceiling.
- Only the `general_knowledge` cloud path truncates. The
  `ASTI_ALLOW_CLOUD=false` local fallback and every other intent always get
  the full message — truncation only matters for what actually leaves.
- Truncation appends a visible notice to the response rather than silently
  dropping content. Factored `_build_general_prompt()` out to avoid
  duplicating the prompt template between truncated/untruncated branches.
- Deliberately did NOT cross-check the outgoing text against stored
  personal-memory values — that would require loading personal memory on
  this path, which breaks the documented "never loaded on this path"
  guarantee from roadmap #6's earlier slices. Out of scope for this step.

### Verification
Short messages unaffected. A long message truncates to 2000 chars with a
notice appended before the cloud call. The same long message through
`ASTI_ALLOW_CLOUD=false` is NOT truncated — confirms the cap only applies
to what leaves the machine. `recall`/`task` intents unaffected.

### Result
Fourth slice of roadmap #6 done. Remaining: privacy-safe diagnostics.

### Note
While testing this slice, `tasks.json` (real data, not test output) was
accidentally deleted via an `rm -f` aimed at clearing test artifacts
between runs. Gitignored + encrypted at rest, so unrecoverable. Low-stakes
content (one completed task), but flagging per Carter's standing
instruction to always call out anything that could delete real data.

## Milestone: Privacy-safe diagnostics via /status (roadmap #6, final slice)

### What changed
- New `build_diagnostics_report()` + `/status` command: local
  provider/model and whether Ollama is actually reachable, cloud
  provider/model, `ALLOW_CLOUD`, whether the cloud API key is set, the
  outbound character cap, whether encryption at rest is on, and counts
  (not content) for personal-memory categories/entries, tasks, and
  outbound calls logged.
- Deliberately config and counts only — no values, keys, task text, or
  prompts anywhere in the report. The point of "privacy-safe" diagnostics
  is that the verification tool itself can't become a new leak surface.

### Verification
Ran the report and confirmed no content leakage — just settings and
counts. Confirmed `recall`/`general_knowledge` intents still work
unaffected.

### Result
Final slice of roadmap #6 done. All five pieces of the Full Model Gateway
(config-driven provider/model, the `ASTI_ALLOW_CLOUD` privacy setting,
outbound-call auditing, context minimization, privacy-safe diagnostics)
are complete. Roadmap #7 (semantic recall over conversation history) is
the one remaining engineering item before #8 (the product/commercialization
path).

## Milestone: Semantic recall over conversation history (roadmap #7, first slice)

### What changed
- New `generate_embedding()` in `model_provider.py`, always local via
  Ollama's `nomic-embed-text` (pulled this session) — never routed through
  the cloud path, since conversation history can contain anything the
  user has said. New `EMBEDDING_MODEL` config (env `ASTI_EMBEDDING_MODEL`).
- `add_memory()` now accepts an optional `embedding` to store alongside a
  turn. The main loop computes one for every new turn going forward,
  best-effort — if the embedding call fails, the turn still saves without
  one rather than losing conversation history over it.
- New `semantic_search()` in `memory.py`: brute-force cosine similarity
  over embedded turns. Fine at personal-use scale; a real vector index is
  a later concern if this ever needs to scale, not a day-one requirement.
  Turns saved before this feature existed have no `embedding` key and are
  silently skipped — not backfilled.
- Deliberately NOT wired into the live `chat`/`recall` prompts yet.
  Surfaced instead through a new `/recall <query>` command so retrieval
  quality could be inspected directly first, after how many rounds of
  prompt-engineering whack-a-mole happened earlier in this project's
  history. Wiring this into live responses is a separate future slice.
- `/status` now also reports how many conversation turns are
  semantically searchable out of the total.

### Verification
A reworded query ("what are my plans for learning a new language") with
zero words in common with a stored turn about learning Spanish to travel
to Mexico correctly ranked that turn highest (0.604 cosine similarity)
over unrelated stored turns about savings (0.480) and a recipe (0.416) —
proof of genuine semantic matching, not keyword overlap. Synthetic test
turns used to verify this were not left in the real `memory.json`.

### Result
First slice of roadmap #7 done: the retrieval engine exists and is
inspectable via `/recall`, but doesn't yet influence what ASTI says in
conversation. That integration is the natural next slice.

## Fix: ground general_knowledge responses with a proper system prompt

### What changed
- Found during manual testing: the cloud (`general_knowledge`) call had no
  system-level grounding — the identity/instruction text and the user's
  question were concatenated into one blob sent as a plain user message.
  Asked about itself, Claude defaulted to generic "here are my AI
  limitations" boilerplate, including a stale/hallucinated knowledge-cutoff
  date, since it had nothing real to ground that claim in.
- `generate_response()` and `generate_cloud_response()` in
  `model_provider.py` now accept an optional `system` parameter (Ollama's
  `/api/generate` `system` field, Anthropic's top-level `system` field).
- `ask_llm()`'s `general_knowledge` branch builds one via
  `_general_system_prompt()`: real identity framing, today's actual date,
  and an explicit instruction not to volunteer generic AI disclaimers
  unless asked. Removed the now-dead `_build_general_prompt()` — the
  system prompt carries that role now.
- Applied a lighter version of the same tone instruction to the local
  chat-mode prompt. Won't make `llama3` sound like Claude — that gap is a
  real model-capability difference, already documented as the reason
  `general_knowledge` exists — but it's a cheap improvement within what
  prompting can actually do there.

### Verification
A neutral technical question (TCP handshakes, rate-limiting algorithms)
now gets a clean, well-formatted, directly-answering response with no
unprompted disclaimer dump. The literal "what's your knowledge cutoff"
question still returns an inaccurate specific date (a known LLM
self-reporting quirk, not fixable without asserting a cutoff date that
can't be verified as correct), but it now correctly reasons from today's
real date instead of being confused about it. `recall`/`chat` unaffected.

### Result
`general_knowledge` responses read like talking to Claude directly, which
was the actual goal — this path genuinely is Claude, it was just being
handicapped by an ungrounded prompt.