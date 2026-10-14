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

## Milestone: File reading via /read <path>

### What changed
- New `read_file_summary()` in `llm.py`: reads a local text file, summarizes
  it via the local model. Deterministic `/read <path>` command, not
  NLP-routed — reading arbitrary files from disk is a deliberate action,
  same reasoning as `/memory`, `/forget`, `/tasks`, `/outbound`, `/recall`.
- Always local — never `generate_cloud_response`. File content could be
  anything, so unlike `general_knowledge` there's no cloud option here yet.
- Capped at `MAX_FILE_READ_CHARS` (env `ASTI_MAX_FILE_READ_CHARS`, default
  8000) for sane local-model behavior, not privacy — nothing here leaves
  the machine regardless of the cap.
- Plain `open()`, not `storage.py` — that boundary is for ASTI's own
  encrypted data stores, not arbitrary external files the user points it
  at. Handles missing file, directory, binary/non-UTF8 content, and
  permission errors without crashing.

### Verification
Summarized a real file correctly; truncated and noted it for a file over
the cap (tested against the 30KB `PROJECT_LOG.md` itself); clean error
messages for a missing path and a directory.

### Result
This was the last planned "finish the foundation" item before moving to
GUI work — the long-deferred "File tools" capability from the original
Phase 2 plan now exists in its first slice (read + summarize; Q&A against
a loaded file, binary/PDF support, and multi-file are separate future
slices if wanted).

## Attempted and reverted: semantic recall wired into live chat

### What was tried
- Wired `semantic_search()` into `chat` mode's prompt: recent 3 turns plus
  the top 2 semantic matches for the live message, added under the
  existing "personal memory is authoritative, ignore conflicting history"
  instruction — the same guard already proven to handle recent-turn
  conflicts correctly.

### What broke
- Seeded a stale turn ("my savings goal is 10000 dollars") alongside the
  real `personal_memory` value (50000) and asked, via `chat`, "how much
  money am I trying to save up" — `llama3` answered **10000**, the stale
  value. This is the exact stale-value bug fixed earlier this session
  (recent-turn conversation history vs. keyword search), reintroduced via
  semantic match instead.
- Tried one round of a stronger, section-specific warning ("this section
  may be OLD and OUTDATED, never use a value from it"). Result: fixed one
  phrasing of the question, failed on another — and the failing case got
  *worse*, falsely claiming the stale number came from personal memory
  (false attribution, not just a wrong value).

### Decision
Reverted. Not chasing further prompt iterations against a proven
correctness regression — same discipline as the earlier extraction-prompt
whack-a-mole this session already learned to stop doing. `chat` is back to
recent-turns-only, unchanged behavior from before this attempt.

### Result
Semantic recall stays available only as the explicit, user-invoked
`/recall` command — nothing it returns is ever treated as ground truth
automatically, which is what makes it safe regardless of retrieval
quality. Automatic injection into live responses is not revisited unless
a materially different approach is proposed (e.g. a larger/different
local model, or filtering semantic matches against personal-memory
conflicts before injection) — not just reworded prompt instructions.

## Milestone: First GUI slice — working chat in the browser

### What changed
- New `app.py`: a Flask server, `host="127.0.0.1"` explicit — localhost
  only, never the network, since personal data runs through this. Imports
  `llm.py` directly, one route (`POST /api/chat`) plus the static page.
- Extracted `process_turn()` out of the CLI loop's tail in `llm.py` — the
  actual classify → extract/update memory → respond → embed → save
  pipeline. Both the CLI loop and `app.py`'s `/api/chat` call this same
  function now, instead of risking two copies of the logic drifting apart.
  CLI behavior unchanged — stays the quick testing tool; the web UI is
  meant to become the real day-to-day interface, per the stated goal of a
  polished GUI with the CLI as backend-only.
- `static/index.html`: one self-contained page, no build step, no
  framework — dark theme, message bubbles, an intent tag per AI response
  (same info the CLI's `[intent: X]` gives), a "thinking" indicator, and
  an inline error message if the server can't be reached.
- Explicitly scoped to chat only. Memory browsing, task list, recall
  search, cloud toggle, diagnostics, file upload for `/read` all stay
  CLI-only for now — each is its own future GUI slice.

### Verification
Ran the server locally and hit it directly: index page serves; `/api/chat`
round-trips correctly through both the local `recall` path (real
personal-memory answer) and the cloud `general_knowledge` path (clean
response, no disclaimer dump — same system-prompt fix carries through
since it's the same `ask_llm` code); empty message correctly 400s. Real
`memory.json` backed up before testing, confirmed unaffected after.

### Result
ASTI has a working browser-based chat interface for the first time. The
CLI (`llm.py`) and the GUI (`app.py`) now share one pipeline
(`process_turn()`), so every future fix to the conversation logic applies
to both automatically.

## Milestone: Semantic recall search in the GUI

### What changed
- New `POST /api/recall` in `app.py`, reusing the same `semantic_search()`
  + `generate_embedding()` the CLI's `/recall` command already uses — no
  new retrieval logic, just a route around the existing function.
- Frontend: a "Recall" button in the header opens a modal — search box,
  results list showing similarity score, the stored user message, and
  ASTI's original response. An overlay, doesn't touch the chat layout.
  Empty state explains only turns saved since semantic recall shipped are
  searchable.

### Verification
Tested against real data (accumulated from Carter's own GUI usage since
the chat slice shipped): query "savings goal" correctly ranked the exact
stored match highest (0.806 similarity) with descending scores for less
relevant turns. Empty query correctly 400s. Read-only endpoint, nothing
to restore after testing.

### Result
Two of the two things originally asked for a GUI ("recall and cloud
choice") — recall is done. Cloud toggle is next, which needs the
`ALLOW_CLOUD` live-reload architecture decision first (currently a
load-once constant from `.env`; a GUI toggle needs it read fresh per
call instead).

## Milestone: File upload in the GUI

### What changed
- Refactored `llm.py`'s file summarization into a shared core,
  `_summarize_file_content(label, content)`, used by two thin entry
  points: `read_file_summary(path)` for the CLI (unchanged behavior) and
  new `summarize_uploaded_file(filename, raw_bytes)` for the GUI, which
  decodes already-received upload bytes instead of reading a local path.
  One implementation instead of two that could drift apart.
- New `POST /api/read` in `app.py` accepts a multipart upload, calls
  `summarize_uploaded_file()`. Added a 10MB `MAX_CONTENT_LENGTH` as a
  basic safety net against an accidental huge upload.
- Frontend: a paperclip button in the composer opens a native file
  picker; the upload appears in the chat thread as a filename bubble plus
  an AI summary bubble (tagged "file"), matching how file-upload UX
  generally looks in ChatGPT/Claude.
- Deliberately no persistence yet — same one-shot behavior as the CLI's
  `/read`. Scoped separately on purpose so persistence can be added and
  tried immediately after, not bundled into this step.

### Verification
Real text file (`README.md`) summarizes correctly through the upload
endpoint; missing file field 400s; a binary file gets a clean error
instead of crashing; `memory.json` turn count unchanged across all upload
tests (69 before and after), confirming the stateless behavior; the CLI's
`read_file_summary()` still works correctly after the refactor.

### Result
Both pieces of "file tools" now exist in the GUI the same way they do in
the CLI — upload instead of typing a path, same underlying summarization.
Persistence (saving file reads to conversation history / personal memory)
is the next slice.

## Milestone: PDF and .docx support

### What changed
- New `_extract_text(filename, raw_bytes)` in `llm.py` dispatches by
  extension: `.pdf` via `pypdf` (per-page text joined; clean error if no
  text is extractable — likely scanned/image-only, OCR not supported),
  `.docx` via `python-docx` (paragraph text joined), `.doc` gets an
  explicit "not supported yet, only .docx" message (old binary Word
  format, no good pure-Python library), everything else falls back to
  UTF-8 text decoding as before.
- Both `read_file_summary()` (CLI) and `summarize_uploaded_file()` (GUI)
  now read raw bytes and share this one dispatcher — PDF/docx support
  landed in both entry points at once.
- Added `pypdf` and `python-docx` to `requirements.txt`.

### Verification
Tested against real files — a PDF generated via macOS's `cupsfilter`, a
`.docx` via `python-docx` — each containing a distinct marker value to
confirm genuine extraction, not a stub. Both formats summarize correctly
through the CLI path and the GUI upload path. A fake `.doc` file gives
the correct not-supported message instead of crashing. Plain text still
works unchanged. `memory.json` turn count unchanged (69 before and after)
across all GUI upload tests — still fully stateless.

### Result
File reading now handles the three formats people actually attach day to
day (text, PDF, Word) in both the CLI and GUI. Ready for the persistence
slice — nothing about how files get summarized needs to change for that,
only whether the result gets saved.

## Milestone: File reads now persist into conversation history

### What changed
- `_summarize_file_content()` now calls `add_memory()` after summarizing
  — same path every chat turn already uses, with a best-effort embedding
  (same pattern as `process_turn()`: still save if embedding fails).
  Both `read_file_summary()` (CLI) and `summarize_uploaded_file()` (GUI)
  share this function, so persistence landed in both entry points at
  once. Stored as `{"user": "[uploaded file: <label>]", "ai": "<summary>"}`.
- Deliberately did **not** run `extract_memory()` against file summaries
  — that pipeline is tuned for short conversational statements, not
  document summaries, and `personal_memory` is too trusted a store to
  risk on an untested extraction path. Facts-from-documents stays a
  separate, deliberate future decision if wanted.
- Reusing `add_memory()` gets file reads two already-proven mechanisms
  for free, no new injection logic: recent-turn chat continuity (a file
  read becomes part of the last-3-turns context) and `/recall`
  searchability (same `semantic_search()` every other turn uses).

### Verification
Reading a file adds exactly one turn with an embedding. A reworded
`/recall` query found it correctly (0.613 similarity, zero shared
keywords with the stored content). A direct chat follow-up ("tell me
more about the file I just uploaded") correctly referenced specific
details from the file via recent-turn continuity.

**Also found and flagged, not fixed**: the router doesn't always classify
a "what about that thing I just read" follow-up as `chat` — it sometimes
lands in `general_knowledge` or `recall`, both of which skip conversation
history by design. Same pre-existing router-ambiguity pattern already
documented elsewhere (e.g. "my favorite color is teal" → `recall`), not
something this change broke.

### Result
File reads are now full conversation participants — searchable, and
referenced naturally in follow-up chat when the router classifies the
follow-up correctly. "File tools" (upload, PDF/docx, persistence) is
functionally complete as a first full slice.

## Fix: "what about this doc" routed to general_knowledge, lost all context

### What happened
Carter hit the exact router gap flagged in the persistence milestone
above, immediately: uploaded `Playbook 1.pdf` (a phishing/BEC incident
response playbook), then asked "what are the grc parts of this doc" —
classified `general_knowledge`, which never loads conversation history.
The question went to Claude with zero context and correctly replied "I
don't see any document attached."

### Two issues found and fixed
1. **Router gap** — added a deterministic check in `classify_intent()`,
   before the LLM call: a message matching "this/that/the
   doc(ument)/file/pdf" always routes to `chat` now. Mechanical signal,
   not a judgment call, so Python enforces it rather than more prompt
   tuning on the classifier.
2. **Recency bias** — once the bad "I don't see any document" answer
   happened, it became the most recent AI turn in context, and the local
   model tended to just agree with its own prior wrong statement instead
   of looking back at the real file summary two turns earlier. Confirmed
   this by testing with clean context (just the real summary turn, no
   polluting prior answer) — it then answered correctly, citing the
   actual PCI DSS references in the playbook (8.2/8.3, 12.6.3.1, 12.10.1).

### Remediation
Cleaned up Carter's real conversation history: removed the two erroneous
"I don't see any document" turns and replaced them with the correct
answer, so his actual history reflects reality rather than two wrong bot
responses that would have kept corrupting near-future follow-ups via
recency bias. Backed up before editing.

### Result
File-reference follow-ups now stay local and use conversation history
correctly. The recency-bias finding (a bad answer becomes "sticky" for a
few turns once it's in context) is a real, reproducible local-model
behavior worth remembering if other router/context bugs surface — the
fallout isn't just the one bad answer, it's a few turns of degraded
answers after it until the bad turn ages out of the recent-3 window.

## Milestone: GUI polish pass begins — markdown rendering

### Context
Carter is about to start using ASTI himself day to day and wants the GUI
fully polished first, both visually and for feature completeness, so
daily use surfaces backend issues through a usable interface rather than
the CLI. Agreed order: markdown rendering → memory vault panel → tasks
panel → diagnostics panel → cloud toggle (needs the `ALLOW_CLOUD`
live-reload fix first) → general layout pass once everything's in the GUI.

### What changed (step 1 of the polish pass)
- Every AI response was showing literal `**bold**`/`*italic*`/`# headers`
  as raw characters — the single most visible "feels unpolished" issue,
  since most AI output this session used markdown-shaped formatting.
- New `renderMarkdown()`/`renderInline()` in `static/index.html`: a
  small, dependency-free markdown-to-HTML renderer (headers, bold/
  italic, inline code, fenced code blocks, bullet/numbered lists — not
  full CommonMark, just what AI responses actually use). No CDN library
  on purpose — core UI shouldn't depend on internet access just to
  render text. HTML-escapes input before any markdown transformation.
- Moved `white-space: pre-wrap` off the base `.msg` class onto
  `.msg.user`/`.msg.error` specifically — needed for plain-text bubbles,
  but was adding ugly gaps once AI responses became real block elements.
- Recall search results panel intentionally left as plain text —
  secondary utility view, keeping this step scoped to the main chat
  surface.

### Verification
No browser automation available this session, so ported the renderer to
Python and tested against realistic AI-response-shaped content — all
render correctly. Verified an XSS attempt (`<script>` in response text)
is properly escaped, never executed. Full end-to-end server check
confirms nothing else broke. Final visual check is Carter's, in his own
browser, since that's the authoritative test for a UI change.

### Result
First step of the GUI polish pass done. Next: memory vault panel.

## Milestone: Memory vault panel in the GUI (polish pass, step 2)

### What changed
- New routes in `app.py`, thin wrappers around the same `memory.py`
  functions the CLI's `/memory`/`/edit`/`/forget`/`/export` already use:
  `GET /api/memory`, `POST /api/memory/edit`, `POST /api/memory/forget`,
  `POST /api/memory/export`. Category validated against
  `ALLOWED_MEMORY_CATEGORIES`, same allowlist the CLI enforces.
- Frontend: a "Memory" button opens a modal — categories grouped and
  sorted, each entry with edit (populates the add-form) and delete
  buttons, an Export button, and an add/edit form. Reuses `escapeHtml()`
  from the markdown renderer when building rows, since stored values
  originate from model extraction and shouldn't be trusted uncritically.
- Fixed a stale comment on `/api/read` left over from before the
  persistence slice shipped.

### Verification
Curl-verified against real data: GET returns real categories/entries;
edit adds and confirms an entry; invalid category 400s with the valid
list; forget removes an entry and 404s on a repeat; export writes a real
timestamped file. Real `personal_memory.json` backed up before testing,
confirmed unaffected after; test-triggered export file cleaned up. No
browser automation available — backend fully curl-verified, frontend JS
reviewed against the working recall-modal pattern plus a structural
balance check, but click interactions need Carter's visual confirmation.

### Result
Second step of the GUI polish pass done. Next: tasks panel.

## Milestone: Tasks panel in the GUI (polish pass, step 3)

### What changed
- New routes in `app.py`, thin wrappers around `tasks.py`: `GET /api/tasks`,
  `POST /api/tasks/add`, `POST /api/tasks/complete`. Matches the CLI's
  `/tasks`/`/done` exactly — no uncomplete or delete, since `tasks.py`
  doesn't support those either.
- Frontend: a "Tasks" button opens a modal — checkbox list (checked and
  disabled once done, strikethrough text), add-task input at the bottom.
  Uses `textContent` for task text, not `innerHTML`, so no escaping
  concern there.

### Verification
Curl-verified against a real (empty) `tasks.json`: GET returns `[]`; add
creates and confirms a task; complete marks it done; completing a
nonexistent id 404s; empty text 400s. Test task cleaned up after (file
was created fresh by the test, so removing it just leaves a clean slate).
No browser automation available — backend fully curl-verified, frontend
JS follows the same twice-proven modal pattern (recall, memory) plus
HTML validity and structural balance checks.

### Result
Third step of the GUI polish pass done. Next: diagnostics panel, then the
cloud toggle (needs the `ALLOW_CLOUD` live-reload fix first).

## Fix: tasks now fully conversational — query and complete via chat

### What was broken
Carter asked "what are my tasks" and got told ASTI didn't know. Root
cause: `recall` mode only ever read `personal_memory.json`, never
`tasks.json`. Separately, there was no way at all to mark a task done
through conversation — only the CLI's `/done` or the GUI checkbox could.

### What changed
1. **Query tasks via recall** — `ask_llm()`'s `recall` branch now includes
   the task list alongside personal memory. No new intent needed; "what
   are my tasks" already classified as `recall` correctly, it just had
   nothing to retrieve from.
2. **Complete tasks via conversation** — new `task_complete` intent,
   deliberately conservative (needs a clear signal like "mark X done" or
   "I finished X," not just incidental wording overlap). New
   `_match_task()` reuses the `reconcile_key()` pattern exactly: show the
   model the real open tasks, constrain the answer to a known id or
   `"__none__"`, Python validates — unmatched answers decline rather than
   guessing which task to complete.

### Known, accepted limitation
The router classifies intent with zero visibility into actual task
content. "I finished calling the dentist" → `task_complete` (matches the
`task` intent's own canonical example phrase), but "I finished reading
harry potter" → `chat`, despite referencing a real open task — identical
sentence structure, different outcome. Deliberate: under-firing just
means being more explicit or checking the box manually; over-firing could
mark the wrong task done, corrupting real state. The prompt explicitly
says "when unsure, prefer chat." Giving the classifier real task-list
visibility is a separate, carefully-scoped future step if ever worth it —
not a quick wording fix, and not chased further here.

### Verification
Router: 14/14 on a matrix covering the new intent plus every previously-
established regression case. End-to-end: an ambiguous completion
correctly declines; an explicit one ("mark read harry potter as done")
correctly matches and completes; a second attempt on an already-done task
correctly finds no open match. Task creation, chat, recall all clean.
All test artifacts (a leaked `personal_memory` entry from `extract_memory`
firing on a chat-classified test message, a test task, test conversation
turns) found and cleaned from real data after testing.

### Result
Tasks are a first-class conversational capability now: create, query,
and complete, not just create.

## Milestone: Diagnostics panel in the GUI (polish pass, step 4)

### What changed
- New `GET /api/status`, a thin wrapper returning `build_diagnostics_report()`
  verbatim — same function the CLI's `/status` uses, so GUI and CLI can
  never show different diagnostics.
- Frontend: a "Status" button opens a modal showing the report in a
  monospace block, with a Refresh button. Simplest of the four modals so
  far — no interactivity beyond fetch-and-display.

### Verification
Endpoint returns real data (provider/model config, Ollama reachability,
cloud settings, encryption status, real counts). HTML validity and
structural balance checks pass; full end-to-end server check confirms
nothing else broke. No content in the response to worry about leaking.

### Result
Fourth step of the GUI polish pass done. Last remaining piece: the cloud
toggle, which needs the `ALLOW_CLOUD` live-reload fix first (currently a
load-once constant from `.env`; a GUI toggle needs it read fresh per
call). After that: the general layout pass, now that everything is
actually in the GUI to evaluate.

## Removal: tasks feature torn out entirely

### Why
Carter flagged twice, across two separate messages, that the tasks
feature isn't actually useful for what he's building — a product for
privacy-sensitive professionals and ordinary consumers, not a to-do app.
Chose full removal over leaving it in as unused weight.

### What was removed
- `router.py`: the `task`/`task_complete` intents and their classifier
  examples — `INTENTS` is back to the original three (`chat`, `recall`,
  `general_knowledge`).
- `llm.py`: `TASK_SCHEMA`, `extract_task()`, `_match_task()`, the
  `task`/`task_complete` branches in `ask_llm()`, the task-list addition
  to `recall` mode's context, the task-skip condition in `process_turn()`
  (`extract_memory()` now runs unconditionally again, as it did before
  tasks existed), the `/tasks`/`/done` CLI commands, the tasks line in
  `build_diagnostics_report()`.
- `app.py`: the `tasks.py` import and all three `/api/tasks*` routes.
- `static/index.html`: the Tasks header button, its modal, its CSS, ~110
  lines of its JS.
- `tasks.py` deleted entirely. `tasks.json` deleted — Carter's real data
  (2 tasks), flagged before removal, orphaned once nothing referenced it.
- `.gitignore`: removed the now-unnecessary `agent/tasks.json` entry.

### Verification
Syntax and HTML validity clean. Router confirmed to have zero task
references. Full server check: index, `/api/status`, `/api/memory` all
200; `/api/tasks` correctly 404s now that the route is gone; `/api/status`
report no longer mentions tasks.

### Found and flagged, not fixed
Removing two intents from the classifier prompt shifted its decision
boundary — "what is my savings goal" and "what are my preferences" now
land in `chat` instead of `recall` (other phrasings of the same question
still correctly hit `recall`). Verified this doesn't break correctness:
`chat` mode still has `personal_memory` access and answers right, just
more conversationally. Not chasing this with more prompt tuning — same
tolerance already extended to other known router fuzziness (e.g. "my
favorite color is teal" → `recall`).

### Result
Tasks is fully gone, not just hidden. Roadmap #3 (originally "tasks /
projects / notes / documents") now has nothing built under it — if
projects/notes/documents are ever wanted, they start from scratch, and
shouldn't be assumed wanted just because they were adjacent to tasks in
the original roadmap bullet.

## Milestone: Live cloud toggle in the GUI (polish pass, final panel)

### What changed
- **Architecture fix first**: `config.ALLOW_CLOUD` was a load-once
  constant read from the environment at import time — a GUI toggle could
  never affect an already-running process, only the next restart.
  Renamed to `ALLOW_CLOUD_DEFAULT` (env-sourced fallback only). New
  `cloud_setting.py` (mirrors `outbound_log.py`'s pattern):
  `is_cloud_allowed()` reads fresh from a small file via `storage.py` on
  every call, so a toggle takes effect on the very next message, no
  restart. Had to live in a new module, not `config.py` itself —
  `config.py` importing `storage.py` would be circular, since
  `storage.py` already imports `config.py` for `ENCRYPTION_KEY`.
- `llm.py` updated to call `is_cloud_allowed()` at all three call sites
  that used the old constant.
- New `GET`/`POST /api/settings/cloud` in `app.py`. Frontend: a single
  header button (no modal needed for one boolean) — "Cloud: ON"/"Cloud:
  OFF", click to flip, red-tinted when off.

### Verification
The critical test was proving live-reload actually works: toggled off
and back on within a single running Python process (no restart) and
confirmed `ask_llm(mode="general_knowledge")` respected each change
immediately, including the privacy notice on the local fallback. Backend
endpoints curl-verified. HTML validity and structural balance checks
pass. Full server check confirms nothing else broke.

### Result
This closes out the GUI polish pass's planned panels: chat, recall
search, file upload, memory vault, diagnostics, and cloud toggle (tasks
shipped then removed per Carter's call). Remaining: the general layout
pass, now that everything is actually in the GUI to evaluate.

## Fix: local-fallback general_knowledge answers can confidently fabricate facts

### What was reported
Carter said the agent "seemed limited when cloud was on, and reaching
the cloud when off" — the opposite of expected, and worrying given the
toggle had just shipped.

### What was actually happening
Investigated with real evidence, not guessing: compared `outbound_log.py`
entries against `cloud_setting.json`'s last-modified time. The toggle was
working correctly the entire time — zero outbound calls after Carter
switched cloud off. What looked like "must be cloud, that's detailed" was
llama3 **confidently fabricating a fake, detailed "OpenAI Hack hackathon"
story** in response to "open ai hack" — a real hallucination, not a
routing bug. Detailed isn't the same as true.

### What was tried and didn't work
Added an explicit "if you don't know, say so instead of inventing an
answer" instruction to the shared general-knowledge system prompt.
Retested the identical question — llama3 fabricated a *second*,
differently-detailed fake story anyway. Confirmed this is a genuine
capability gap, not a prompt-wording problem, by running the same
question through the cloud path: Claude handled it correctly (asked for
clarification, named what it would need to verify). Not iterating the
prompt further against a model that demonstrably can't follow the
instruction — same discipline as the earlier router whack-a-mole.

### The real fix
Since the local model can't be trusted to flag its own unreliability,
Python does it unconditionally instead. Every `general_knowledge` answer
that takes the local-fallback path (cloud off) now gets a deterministic
warning appended regardless of what the model said: local answers can be
confidently wrong on events/incidents/dates, verify independently. Cloud
answers are unaffected.

### Verification
Direct test against the exact failing question with cloud off shows the
warning; the identical call with cloud on does not. Full server check
confirms nothing else broke. Carter's real `cloud_setting.json` restored
to its actual prior state (off) after testing.

### Why this matters beyond this one bug
This is the most serious trust finding of the polish pass so far — not
"the local model is lower quality" (already an accepted, named tradeoff
when the toggle shipped) but "the local model can present fabricated
specifics with full confidence." That's a materially bigger risk,
especially given the stated target audience includes regulated
professional users. Worth remembering if other local-only paths (or a
future smaller/different local model) are evaluated: check not just
answer quality, but whether the model can be trusted to flag its own
uncertainty, and don't assume a system-prompt instruction fixes that —
this one didn't.

## Milestone: Conversation history loads in the GUI on page open

### What Carter asked for
"I want it so that the chat overall is searchable as well. If I say
something in the chat cloud or not, I want to be able to reference it."

### What was already true, verified before building anything
Every turn — cloud-answered or local, any intent — was already saved and
embedded identically via `process_turn()`'s unconditional `add_memory()`
call, so it was already fully searchable through Recall regardless of
which path answered it. Confirmed with real data: queried semantically
for cloud-adjacent turns and got correct, high-similarity matches.

### The actual gap
The GUI chat window started completely empty on every page load, even
though `memory.json` had the real history. The only way to "reference"
something said earlier was opening Recall and typing a search query —
not scrolling back and reading, like a normal chat app.

### What changed
- New `GET /api/history` returns the last 50 turns as plain `{user, ai}`
  pairs. Capped, not the full history, to keep the page snappy as
  `memory.json` keeps growing — Recall stays the tool for finding
  something specific/older by topic, this is just "what did we just say."
- Frontend `loadHistory()` runs on page open, renders each turn through
  the same `addMessage()`/markdown pipeline as live messages, with a
  divider ("Earlier conversation loaded above") marking where loaded
  history ends and the live session begins.
- Small refactor to `addMessage()`: markdown rendering now applies to
  every `role="ai"` message, not just ones with an intent tag — historical
  turns have no stored intent (never persisted per-turn) but should still
  render the same way live ones do.

### Verification
`GET /api/history` returns real data in the correct shape. HTML validity
and structural balance checks pass. Full server check confirms nothing
else broke.

### Result
The GUI now reads as a continuous conversation on open, and the
"searchable regardless of cloud or local" half of the request was already
true and is now confirmed/documented rather than assumed.

## Milestone: Reference a prior message

### What changed
- A small reply icon on every message (live or loaded history) lets the
  user explicitly point at it, instead of relying on the model to guess
  "it"/"that" from fuzzy recent-turns context — the same ambiguity that
  caused the earlier "this doc" router bug. A chip above the composer
  shows the referenced text; sending clears it (one-shot, like "reply to"
  in most chat apps).
- `process_turn(user_input, reference=None)` forces `intent="chat"`
  whenever a reference is present — deterministic, same precedent as
  `router.py`'s file-reference regex. `ask_llm()` threads the reference
  into chat mode's prompt as a clearly-delimited block, with explicit
  pronoun-resolution instructions. `memory.json` storage is unaffected —
  only the live prompt includes the reference, not what gets saved.

### Known limitation, not chased further
Took three prompt iterations to get working reliably. llama3 handles
explicit phrasing ("summarize the referenced message") perfectly, but
vague pronoun follow-ups ("simplify it") are still sometimes unreliable
even with an instruction telling it how to resolve them — same local-model
instruction-following ceiling documented elsewhere this session.

### Verification
End-to-end through the real HTTP route: an explicit referenced question
correctly resolves; a normal message with no reference is unaffected;
`general_knowledge`/`recall` unaffected. Real `memory.json` backed up
before testing, restored after.

### Side discovery, flagged separately
While testing, found Carter's real `personal_memory.json` had a corrupted
`goals.savings_target` value — literally the string `"2026"` instead of a
dollar amount. Traced likely cause: a bare, context-free message `"2026"`
sent during a confusing exchange about "openai hack" got matched by
`reconcile_key()` onto the existing `savings_target` key and silently
overwrote it. This is a real failure mode of `reconcile_key()` — an
ambiguous short message can get mismatched to the wrong existing key —
not something to fix inside this feature's scope, but worth a dedicated
look: `reconcile_key()` has no sanity check on whether a bare, low-context
message should be eligible to overwrite an existing value at all.

## Fix: minimum-content gate on personal memory extraction

### What changed
`is_noninformative()` in `llm.py` now also returns `True` for any message
that reduces to a single token (after stripping trailing punctuation) —
`"2026"`, `"20"`, `"pizza"` with nothing else said, etc. This runs before
`extract_memory()`'s model call, so `should_remember` is forced `False`
for these inputs and `reconcile_key()` is never reached at all — it can't
mismatch a message onto an existing key if the message is never offered
to it in the first place.

### Why this shape, not a fix inside `reconcile_key()` itself
The actual root cause traced in the prior milestone: a bare `"2026"` had
no interpretable subject, yet `extract_memory()`'s model call still
produced a confident (hallucinated) subject/attribute/value for it, and
`reconcile_key()` then trusted the model's enum-constrained key choice
completely. Gating upstream, on message content, is simpler and more
reliable than trying to make `reconcile_key()` itself second-guess a
key choice it has no independent way to verify — consistent with the
project's "let the model interpret meaning, let deterministic Python
enforce structure" rule in `CLAUDE.md`.

### Trade-off, accepted deliberately
A genuinely informative one-word answer (e.g. "Pizza." answering "what's
your favorite food?") will now also be dropped — the pipeline has no
dialogue-state tracking to tell that case apart from a stray bare token.
This is the same known limitation already documented for bare pronoun
follow-ups ("instead make it 50k") — explicit phrasing keeps working,
context-free fragments don't. Accepted trade: stopping real data
corruption outweighs losing some one-word answers, especially since
explicit phrasing already works fine for the audience this is being
built for.

### Verification
Tested `is_noninformative()` directly (pure function, no model calls, no
file I/O) against 9 cases — the real `"2026"` bug case, several question/
greeting/multi-word-fact cases, and more single-token cases. All matched
expected behavior. No real data touched; nothing needed backing up.

### Status
The existing corrupted `goals.savings_target` value (`"2026"`) is left
as-is for now, per Carter's call — this fixes the mechanism going
forward, not the already-corrupted stored value.

## Milestone: Semantic recall back in live chat, this time deterministic

### What Carter asked for
Chat that feels like ChatGPT/Claude-level memory — asked directly whether
that's achievable, then said to build it and "add in anything you need to
make the chat feel like a frontier model even if it is limited."

### Honest framing, given before building
Retrieval (finding the right past turn) can get close to frontier-level —
it's a mostly model-independent, solved problem, and the infrastructure
already existed (`nomic-embed-text` embeddings on every turn,
`semantic_search()`). Synthesis quality (judging staleness, resolving
conflicts, writing a coherent answer) is bottlenecked by llama3's raw
reasoning ability and will not match GPT-4/Claude-class models — proven
in this exact codebase already (see the reverted first attempt at this,
noted in `CLAUDE.md`'s roadmap #7). Agreed to build retrieval as strong as
possible with Python-enforced rules instead of trusting the model to
self-correct, and accept the synthesis ceiling as a known limitation.

### What changed
- `memory.py`: new `semantic_search_recent()` — same cosine-similarity
  search as `semantic_search()`, but also returns each match's position
  in the full history list. `memory.json` is append-only with no
  per-turn timestamp, so list position doubles as a recency signal.
- `llm.py`: `ask_llm()`'s `chat` mode now runs semantic recall on every
  turn (embeds the live prompt, searches history) instead of only
  responding to the explicit `/recall` command. Raw matches go through a
  new deterministic filter, `_filter_related_matches()`, before ever
  reaching the model:
  1. Drop anything already in the last-3-turns window (no duplicate
     context).
  2. Drop anything below a relevance floor (score < 0.5) — top-k always
     returns *something*, a low score means "nothing better", not
     "relevant."
  3. **The actual fix for the original bug**: drop any match whose text
     overlaps a `personal_memory` key's words (`_personal_memory_fact_tokens()`
     — e.g. `savings_target` → `{"savings", "target"}`). This is why the
     first attempt at this failed: an old "$10,000" turn semantically
     outranked the current $50,000 `personal_memory` value, and llama3
     didn't reliably resolve the conflict even with explicit "this may be
     outdated" instructions in the prompt. Now that conflicting old turn
     is never shown to the model at all — personal memory is trusted
     alone for anything it already tracks, enforced in Python, not asked
     of the model.
  4. Collapse near-duplicate matches (the same topic resurfacing from
     different points in history) down to the most recent one, using
     list position, not raw score, to break the tie.
  Surviving matches (capped at 3) go into a clearly-delimited "RELATED
  EARLIER CONVERSATION (background only)" block in the prompt, separate
  from the authoritative personal-memory block and the recent-turns
  block, with explicit "this may be outdated, personal memory wins on
  conflict" instructions.
- Added one line to the system-level instructions telling the model to
  reference recalled context naturally and confidently ("like you
  mentioned before...") instead of explaining that it searched memory —
  the "frontier model feel" half of the ask. Small, but changes how
  recall actually reads in a response.

### Verification
Three tests, all via `ask_llm()` directly (read-only — never touched real
data files, confirmed with `git status` after):
1. Real end-to-end call against Carter's actual data (`what is my savings
   goal?`) — ran clean, no crash, correctly stayed authoritative to
   personal memory (still showing the known, not-yet-fixed `"2026"`
   corruption, unrelated to this change).
2. Reproduced the exact originally-reverted bug with fake in-memory data
   (an old "$10,000 saved" turn + a clean personal_memory value of
   $50,000) — confirmed via direct inspection that the $10,000 match was
   genuinely the top semantic result (score 0.664) and was then correctly
   dropped by the fact-token filter; the model answered $50,000.
3. Fake in-memory data for a topic personal_memory does *not* track (an
   old "trip to Japan" turn) with a later query ("have I mentioned any
   travel plans?") — confirmed the match survived filtering and the model
   referenced it naturally: "Like you mentioned before, you've been
   considering a trip to Japan, maybe exploring Kyoto and Tokyo."
First pass at test 3 silently used real production data instead of the
fake history because `semantic_search_recent()` resolves `load_memory()`
against `memory.py`'s own module namespace, not `llm.py`'s imported name
— patching `llm.load_memory` alone doesn't affect it. Needed to patch
`memory.load_memory` directly too. Worth remembering for any future test
that monkeypatches a `from module import name` import.

### Known limitation, accepted not chased
Synthesis quality (how well the model actually reasons over what's
retrieved) still won't match a frontier cloud model — that's the honest
ceiling discussed before building this, not a bug to fix here.