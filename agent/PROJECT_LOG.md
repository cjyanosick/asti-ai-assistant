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

## Finding: encryption-at-rest roadmap items were already done

### What happened
Asked to pick up "foundations" work — encryption at rest and the
extraction-noise cleanup. Before starting on encryption, checked the
actual code (not just `CLAUDE.md`'s roadmap, which still listed it as
unstarted) and found `storage.py` already encrypts/decrypts every
`load_json`/`save_json` call with Fernet, keyed via `config.py`'s
`keyring`-backed OS Keychain integration — both roadmap #4 and #5,
already committed (`f55459e`, `14a3fc9`) before this session's summarized
window even began.

### Verification, not assumption
Confirmed live against Carter's real data rather than trusting the code
alone: `build_diagnostics_report()` reports "Encryption at rest: on", and
the raw bytes of `personal_memory.json` on disk are a genuine Fernet
token (`gAAAAAB...` prefix) — not parseable as plaintext JSON.

### What this means
No engineering work was needed here — just correcting `CLAUDE.md`'s
roadmap, which had drifted out of sync with what was actually built and
committed. Fixed items 4 and 5 there to say so.

### Open question surfaced, not resolved
`export_personal_memory()` (the Memory Vault panel's "Export" button)
writes through the same encrypted `save_json`, so an export is also an
encrypted blob, not a human-readable backup. Flagged in `CLAUDE.md` —
unclear if that's actually the right default; needs Carter's call, not
a silent change either way.

## Milestone: personal memory extraction now requires confirmation

### What Carter asked for ("foundations")
From `CLAUDE.md`'s GUI Polish list (flagged earlier, not yet fixed):
`extract_memory()` sometimes saves garbage from ambiguous turns (real
examples in Carter's own `personal_memory.json`: `other: chat_previous_message
= "use the chat I just sent to answer why not"`, `other: openai_hack =
"hack"`). Carter's explicit priority: non-technical users in regulated
fields won't notice or clean up wrong stored "facts" the way he does, and
in a regulated context that's closer to a compliance liability than a
cosmetic bug. The fix needed "real design thought... a confirmation step
before saving... or both" (tighter criteria + confirmation), not another
prompt tweak.

### What changed
- `personal_memory.json` is no longer written just because
  `extract_memory()` returned `should_remember: true`. `process_turn()`
  now holds the proposed fact as `pending_memory` and passes it to
  `ask_llm()` as context for *that turn's response only* — the reply
  still reads naturally ("got it, noted...") — without committing it to
  disk.
- CLI: right after the response prints, if there's a pending fact, it
  prompts `[memory] Remember X.Y = Z? [y/N]:` and only calls
  `update_personal_memory()` on `y`.
- GUI: `/api/chat` returns `pending_memory` alongside the response; a new
  Save/Discard chip renders under that message (`buildMemoryChip()` in
  `index.html`). Save calls a new `/api/memory/confirm` route (same
  validation as `/api/memory/edit`); Discard just removes the chip —
  nothing was ever written, so there's nothing to undo.
- Nothing changed about `is_noninformative()`'s existing deterministic
  filtering (still catches questions/greetings/single-token messages per
  the 10/13 fix) — this is a second, independent layer for whatever gets
  past that and still turns out to be noise.

### Verification
All against real data, nothing left polluted (checked with `md5`/content
diffs before and after, not just assumption):
1. `process_turn()` directly: "I just adopted a cat named Whiskers" →
   response read naturally, `pending_memory` returned as
   `{people, cat_name, Whiskers}`, `personal_memory.json`'s content
   provably unchanged (decrypted content diffed byte-for-byte against a
   pre-test copy — raw ciphertext differs run to run since Fernet uses a
   random IV, so ciphertext hash alone isn't the right check).
2. `/api/memory/confirm` via Flask's test client with a throwaway key —
   wrote correctly, then cleaned up via `/api/memory/forget` immediately.
3. Full HTTP round trip against the real running server: `/api/chat` with
   "My favorite coffee order is an oat milk latte" correctly returned
   `pending_memory`; `/api/memory/confirm` against a throwaway key wrote
   and was cleaned up the same way. `memory.json`'s test turn was
   restored from a pre-test backup afterward since that file saves every
   turn unconditionally by design (conversation history, not something
   this feature touches).
This incidentally confirmed the exact noise problem being fixed is real
and already present: Carter's `other` category currently holds several
garbage entries matching the examples in `CLAUDE.md` (`openai_hack`,
`chat_previous_message`, `data_sensitivity`, etc.) — left untouched, not
cleaned up as part of this fix. Worth asking Carter whether to clean
those out separately; this milestone stops new noise, it doesn't retroactively
fix old noise.

## Fix: "are you local or cloud" now answers deterministically

### What happened
While checking message history after the API key rotation, found a
vivid real example of the known llama3-overconfidence limitation: with
cloud toggled off, Carter asked "are you local or cloud right now" and
the local model confidently answered "I'm running on Anthropic's cloud
infrastructure... a distributed instance... across data centers" —
false — with the correct "⚠️ Answered locally (cloud is off)" disclaimer
tacked on right after, producing one self-contradicting message.

### Fix
`process_turn()` now checks for this exact class of question
(`_is_cloud_status_question()`, a regex requiring both "local" and
"cloud" — or "running locally" — near a self-referential question word)
before the model is ever involved, and answers it directly from
`is_cloud_allowed()` + the configured provider/model — the same
deterministic-override precedent as `router.py`'s file-reference regex.
No LLM call happens for this case at all, so there's nothing for it to
get wrong.

### Verification
Tested both branches directly against real state (not mocked): with
cloud off (Carter's real current setting), got "Cloud is OFF right now
— I'm answering entirely locally via ollama's llama3:latest..."; toggled
to on and re-tested, got "Cloud is ON right now — ... answered by
anthropic's claude-haiku-4-5..."; restored the real cloud setting back
to off immediately after. Also tested live through the running server
(Flask's debug reloader had already auto-restarted on the file change)
via a real HTTP call — correct response, then removed that test turn
from `memory.json` afterward, same restore-after-test discipline as
every other real-data test this session.

## GUI polish: Local/Cloud badge replaces the inline disclaimer

### What Carter asked for
Remove the "⚠️ Answered locally (cloud is off)..." text appended to
local-fallback `general_knowledge` answers — it was padding out the
response body too much — and instead show a compact per-message
indicator (emoji + "local"/"cloud") on every AI response so it's always
clear where an answer came from.

### What changed
- `ask_llm()` now returns `(response_text, source)` instead of a bare
  string across every branch (`"cloud"` for the successful cloud path,
  `"local"` everywhere else — chat, recall, and the local-fallback
  general_knowledge path). The old disclaimer text is gone from the
  response body entirely; `process_turn()` now returns a 4-tuple
  (`intent, response, pending_memory, source`) and the CLI/`/api/chat`
  call sites were updated to match.
- `memory.py`'s `add_memory()` takes an optional `source` and persists
  it per turn, so `source` survives into `memory.json` — needed so
  history reloaded via `/api/history` on page open shows the same badge
  as live messages, not just the current session. Turns saved before
  this existed simply have no `source` key; the GUI skips the badge for
  those rather than guessing.
- `index.html`: new `.msg-meta` row holds the existing intent tag plus a
  new `buildSourceBadge()` span ("☁️ Cloud" / "🖥️ Local"). The safety
  information the old disclaimer carried wasn't dropped — it's now the
  Local badge's hover `title` tooltip instead of inline prose, so it's
  available without taking up visible space on every message.
- The new deterministic "are you local or cloud" short-circuit
  (previous milestone) deliberately gets no badge — `source` is `None`
  for it, since no model actually answered; the GUI treats a missing
  `source` as "don't render a badge," same as pre-10/13 history.
- File-summary responses (`/api/read`) always pass `source: "local"` —
  that path has no cloud option at all, so this is just a direct label,
  not an inference.

### Verification
All against real data, backed up and restored after (`md5`-checked):
chat/recall/general_knowledge all correctly tagged "local" with cloud
off; toggled cloud on and confirmed general_knowledge correctly tagged
"cloud", then restored the real setting; confirmed the response body no
longer has any disclaimer text appended. Repeated through the actual
running server over real HTTP (`/api/chat` and `/api/history`), including
confirming pre-10/13 history entries return `source: null` and the GUI's
badge logic skips them. Frontend changes passed brace-balance and
HTML-parser validity checks (no browser automation available in-session;
final visual check is Carter's).

## Milestone: ChatGPT-style conversations + visual overhaul

### What Carter asked for
Three things in one request: (1) opening the app should always start a
brand-new chat, with past chats saved and browsable in a hideable side
panel, like ChatGPT — not one endless continuous history; (2) remove the
"local-first personal assistant" header tagline; (3) a visual polish pass,
especially buttons and colors.

### Data model change — the real risk in this milestone
`memory.json` was a single flat list of every turn ever, shared app-wide.
Restructured to `{"conversations": {id: {title, created_at, updated_at,
turns: [...]}}}` so each chat is its own entity. One-time migration in
`memory._load_store()`: if the loaded file is still the old flat list,
it gets wrapped into one conversation (id `"legacy"`, title "Earlier
conversation") and saved in the new shape immediately — nothing dropped,
just regrouped.
**Verified before touching the real file, not after:** backed up the real
`memory.json` (114 turns at the time — Carter had been testing live
through the GUI), ran the migration, then decrypted and diffed the
pre-migration backup's turns against the migrated `"legacy"` conversation's
turns — `old_turns == new_turns`, byte-for-byte identical. Only after that
passed did any further testing touch the real file.

### Backend changes
- `memory.py`: new `create_conversation()`, `get_conversation()`,
  `list_conversations()` (sidebar listing — only conversations with ≥1
  turn show up, same as ChatGPT not listing an unused new chat),
  `all_turns()` (flattened across every conversation). `load_memory()`
  and `add_memory()` now take `conversation_id`. `semantic_search()`
  (the explicit Recall panel/CLI `/recall` search) now searches
  `all_turns()` — deliberately global, "find something I said anywhere."
  `semantic_search_recent()` (the ambient in-chat ones from the previous
  milestone) now takes `conversation_id` and is scoped to just that
  conversation — matches how ChatGPT itself behaves: a chat's own earlier
  turns are fair game as context, but one chat doesn't bleed into another.
  Removed `search_memory()` (dead code, no callers, keyword-only,
  incompatible with the new shape anyway) and a vestigial "detect simple
  fact updates (color example logic)" block in the old `add_memory()` —
  leftover toy logic from early development that actually contradicted
  the "list position = recency" invariant other code now depends on.
- `llm.py`: `ask_llm()`, `process_turn()`, `read_file_summary()`,
  `summarize_uploaded_file()`, `_summarize_file_content()` all take
  `conversation_id` now. `build_diagnostics_report()` switched from
  `load_memory()` to `all_turns()` for its global turn count. CLI
  (`__main__`) reuses one fixed id (`"cli"`) across every run — it has no
  sidebar, so it keeps the old single-continuous-history feel rather than
  gaining multi-chat complexity it has no UI for.
- `app.py`: new `POST /api/conversations` (create), `GET /api/conversations`
  (sidebar list), `GET /api/conversations/<id>` (load one). `/api/chat` and
  `/api/read` now require `conversation_id`. Removed `/api/history`
  (superseded by the conversation-scoped routes).

### Frontend changes (`index.html`)
- New sidebar (`#sidebar`): "+ New chat" button, scrollable conversation
  list, collapse toggle (hides to width 0; a small ☰ button appears in the
  header to bring it back). `#app` is now a flex row (sidebar + `#main`)
  instead of the old single flex column.
- On page open: always `startNewConversation()` (`POST /api/conversations`),
  never reload old history by default — matches ChatGPT's own behavior of
  a fresh chat on open. Clicking a sidebar item loads that conversation's
  full turns via `openConversation()`. Sending a message refreshes the
  sidebar afterward so a new chat's auto-generated title (first message,
  truncated — no extra model call just to name a chat) and reordering
  show up immediately.
- Removed the "local-first personal assistant" header tagline — Carter's
  call, no replacement text added.
- Visual pass: refined color variables (deeper background, a dedicated
  sidebar shade, softer borders, an accent-hover variant), transitions and
  real hover states added across every button (header buttons, send,
  attach, modal buttons, memory-chip actions), subtle shadows on modals
  and the composer bar, thin themed scrollbars, slightly larger border
  radii throughout for a softer shape language. Removed `.history-divider`
  CSS, now dead code with `loadHistory()` gone.

### Verification
Backend: migration integrity check (above) plus a full real-HTTP lifecycle
test against the live server — create conversation → confirm it's hidden
from the sidebar list until it has a turn → send a message → confirm it
appears, auto-titled, at the top of the list → reload it by id → confirm
`/api/history` now 404s. Confirmed `/api/recall` (global search) and
`/api/status` (diagnostics) both still work correctly against the
migrated data. All test conversations removed from the real file
afterward; real `"legacy"` conversation's 114 turns confirmed intact
throughout. Frontend: brace-balance and HTML-parser validity checks
passed; every element id referenced by new JS confirmed present in the
markup. No browser automation available in-session — final visual check
of the polish pass is Carter's, in his own browser.

### Status
Committed locally, **not pushed** — this is the largest/most structural
change this session (real data migration + new API shape + full UI
rework), so it's waiting on Carter actually testing it before it goes to
the public repo, not on the usual commit-and-push rhythm.

## Fix: visual pass, round 2 — "it looks the exact same"

### What happened
Carter tested the conversations/sidebar rework: "features all work,
visual it looks the exact same." The first visual pass (same session,
earlier milestone) was real but too subtle to register — shade-level
color tweaks and hover-only transitions nobody would notice without
deliberately comparing screenshots or hovering every button.

### What changed this time — asked first, then went bold
Asked Carter which direction ("bold dark + vivid accent," "minimal flat,"
"soft & warm pushed further," or "show me, I'll react") instead of
guessing wrong a second time. He picked "soft & warm, pushed further" —
keep the coral accent, go much bolder with it.
- Body background: layered warm radial gradients instead of flat color.
- Header/composer/sidebar/modals: actual glass — semi-transparent
  backgrounds + `backdrop-filter: blur()`, not just a different solid
  shade.
- `--accent-gradient` (a real 3-stop coral→orange→rust gradient, not a
  single color) now fills every primary action: Send, New Chat's active
  state, the cloud toggle's "on" state, memory-chip Save, Recall's
  search button, the memory-edit form's Save button — each with a
  matching glow-shadow on hover instead of a flat brightness filter.
- Header title "ASTI" is now gradient-filled text
  (`background-clip: text`), not plain colored text.
- Message bubbles gained real shadows and the AI bubble its own subtle
  blur, instead of a flat border-only look.
- Removed two CSS variables (`--panel-solid`, `--accent-2`) added during
  this pass but never actually referenced — caught before committing,
  not left as dead code.

### Verification
CSS brace balance and HTML-parser validity re-checked after every
sub-edit (caught and fixed a duplicate `#new-chat-btn:active` rule this
way). Confirmed live via the running server (`GET /` → 200). Still no
browser available in-session — this is explicitly round 2 *because* the
first round's final-visual-check-is-Carter's caveat turned out to
matter in practice, not just as a disclaimer.

## Finding: sharpest local-model hallucination example yet (found 10/14)

### What happened
Checked real chat history for the most recent hallucination at Carter's
request. Found one in the "give me a script to keep my mouse clicking on
mac" conversation (local/llama3 throughout):
1. Carter asked for a mouse-clicker script; got a plausible-sounding but
   truncated Automator/AppleScript answer.
2. Carter: "give it too me so I can just pop it into terminal." The model
   responded with a completely unrelated fabricated question — "What is
   the largest living species of lizard, and what is its average
   length?" — telling Carter to paste *that* into his terminal. Not a
   wrong fact: a total non-sequitur with no connection to the actual
   request.
3. Carter called it out ("wtf are you talking about"); the model got
   defensive, insisted it remembered the mouse-clicker conversation
   correctly, still didn't produce a script.
4. Pushed again, it produced a bash script — but the script itself is a
   generic "ask ASTI a general-knowledge question" REPL loop, unrelated
   to mouse-clicking.

### Ruled out as a retrieval bug, not just assumed
Before concluding this was pure model hallucination, checked whether
this session's own semantic-recall feature (`_filter_related_matches`)
had surfaced an old unrelated turn and the model regurgitated it —
searched all of Carter's real history for any prior mention of "lizard."
None exists anywhere. This was the model fabricating content outright,
not a bug in the recall mechanism surfacing something real but
irrelevant.

### The useful contrast
Carter asked the identical mouse-clicker question again in a fresh chat
a few minutes later. That turn happened to route through cloud (Claude),
and got a correct, on-topic Python script using `pynput` on the first
try. Same question, same session — local vs. cloud was the entire
difference between nonsense and a correct answer.

### What this is, documented plainly in CLAUDE.md
Not a new bug to fix in ASTI's code — a sharper, concrete data point for
the already-known local-model reliability ceiling (first documented
10/13 re: fabricated event/incident details). This one shows the failure
mode can be worse than "confidently wrong fact" — it can be "loses the
thread of the task entirely." See CLAUDE.md's "Build now" section for
the options discussed with Carter for actually addressing this.

## Milestone: code requests route to cloud when allowed

### What Carter asked for
After seeing the mouse-clicker hallucination, asked what he could do
about it. Agreed on the most direct fix: route code/script requests to
cloud the same way general-knowledge questions already do, since the
same test question got a correct answer from Claude and nonsense from
llama3. Asked specifically to have it show a message like "coding
requests are best with cloud access" when answered locally.

### What changed
- `router.py`: new `code` intent. `_CODE_REQUEST_RE` deterministically
  catches clear phrasings ("write/give/generate/create/make" near
  "script/code/function/program/snippet"), checked *after* the existing
  file-reference override — a request about an uploaded file needs that
  file's context, which the cloud-bound `code` path never loads, so
  file-reference wins if both match. The LLM classifier also recognizes
  `code` for phrasings the regex misses, same pattern as
  `general_knowledge`.
- `llm.py`: new `code` branch in `ask_llm()`, structurally identical to
  `general_knowledge` — personal memory is never loaded on this path at
  all (same hard privacy boundary, not a new one), cloud when
  `is_cloud_allowed()`, local fallback otherwise. Unlike the
  `general_knowledge` disclaimer (moved to a hover tooltip 10/13 to save
  space), this one stays visible in the response body — Carter's call,
  since it's actionable advice ("turn cloud on"), not just a liability
  notice.

### Verification
Fed the exact three real messages from the mouse-clicker incident
through `classify_intent()` — all three now classify as `code` (they
previously fell through to `chat`/whatever the classifier guessed,
which is how the request ended up handled badly by the local model in
the first place). Confirmed `write a story about my brother` and
`how are you doing today` still correctly classify as `chat` — the verb
overlap ("write") didn't cause a false positive since "story" isn't in
the code-noun list.
Tested `ask_llm()`'s new branch directly: cloud off (today's real
setting) → local response with the visible nudge appended; toggled
cloud on → correct, on-topic `pynput` script immediately, confirming
the fix actually reaches Claude correctly; restored the real cloud
setting immediately after. Full `process_turn()` test via a throwaway
conversation id, and a live HTTP round trip through the running server
with the exact real failing message — both correct (`intent: "code"`,
`source: "local"`, nudge message present). All test data cleaned up
from the real `memory.json` afterward (turn count confirmed unchanged).
Interesting note, not a bug: the live HTTP test's local-model response
this time was actually correct and on-topic (model stochasticity — it
doesn't fail the same way every time). The fix doesn't depend on the
failure reproducing every run; it's a structural reliability
improvement for a known-weaker path, not a patch for one bad output.

## Milestone: sidebar delete/pin, icon toolbar, logo mark, cloud feature redesign

### What Carter asked for
Five things in one GUI pass: (1) delete capability for sidebar chats,
(2) a pin feature, (3) a completely different look for the Status/
Memory/Recall buttons, (4) make "ASTI" read as a logo rather than plain
text, (5) center the cloud toggle in the header and make it the visual
centerpiece — his words, "because it is" (the main feature).

### Backend
- `memory.py`: conversations now carry a `pinned` bool (defaults False;
  `.get("pinned", False)` used everywhere reading it, since conversations
  created before this change — including `"legacy"` — have no such key
  on disk). New `delete_conversation()`, `set_conversation_pinned()`.
  `list_conversations()` sorts pinned-first via Python's stable sort
  (sort by `updated_at` descending, then by `pinned` descending — the
  second sort preserves the first's ordering within each group).
- `app.py`: `DELETE /api/conversations/<id>`, `POST
  /api/conversations/<id>/pin` ({"pinned": bool}).

### Frontend
- Sidebar items: pin (📌) and delete (🗑) icon buttons. Pin is always
  visible when pinned (accent-colored), otherwise hover-reveal like the
  existing reply-button pattern; delete is hover-reveal with a native
  `confirm()` before it actually deletes — this is real, unrecoverable
  data loss, not something to fire on a single misclick. Pinned
  conversations render under a small "Pinned" section label, ahead of
  everything else.
- Header rebuilt as a 3-column grid (`1fr auto 1fr`) instead of a single
  flex row: logo on the left, the cloud feature centered in the middle
  column regardless of how wide either side is, utility icons on the
  right.
- Status/Memory/Recall: `.header-btn` (outlined text pills) replaced
  entirely with `.icon-btn` — plain icon, no border, a soft hover
  highlight circle, native `title` tooltip instead of visible text. A
  genuinely different treatment, not a palette tweak.
- Logo: inline SVG "sparkle" mark (gradient-filled, a common AI-product
  glyph) to the left of a bold "ASTI" wordmark, replacing the plain
  gradient-text `<h1>` from the previous visual pass — reads as an
  actual logo lockup now, not styled text.
- Cloud toggle: completely rebuilt as `.cloud-feature`, a centered pill
  with an icon (🖥️/☁️) and label ("Local Only"/"Cloud Connected") plus a
  larger, more tactile switch — replacing the old small corner
  switch-and-label pair. Carter's reasoning for the emphasis: cloud
  on/off is the actual core feature of the product per the North Star
  ("Cloud by choice"), not a secondary setting, so it gets the most
  visually prominent spot in the header, not the same treatment as a
  utility toggle.

### Verification
Backend: pin → appears pinned at the top of the list; unpin → reverts;
delete → 404 on both the deleted conversation and a nonexistent one,
real conversations list unaffected afterward (same 5 real conversations,
same order, confirmed via the live server, not just the test client).
Frontend: CSS brace balance, JS balance, and HTML-parser validity all
re-checked after the full header/sidebar rework; every element id
referenced by JS (including the rebuilt cloud-feature ids) confirmed
present exactly once in the markup; confirmed no leftover references to
the removed old switch/label element ids. No browser automation
available in-session — as with every visual change this session, the
actual look is Carter's call once he's seen it.

## Milestone: icon system, bigger logo, right-click/"..." chat menu

### What Carter asked for
Approved and pushed the prior GUI milestone, then asked for the next
pass: (1) remove emoji entirely — "it looks rudimentary"; (2) make the
"ASTI" logo "way bigger," pushed as "completely into something much
cooler and different," not just a resize; (3) replace the sidebar's
always-both pin/delete icons with a single "..." button or right-click,
opening a small menu instead.

### What changed
- New dependency-free SVG icon system: an `ICONS` lookup of 15 plain
  stroke-based paths (`currentColor`, no fill) and an `icon(name, size)`
  helper, same no-CDN-dependency principle as the markdown renderer.
  Replaced every emoji/symbol across the app — sidebar controls, the
  utility toolbar, the cloud feature, message source badges, the reply
  button, modal close buttons, attach, and the memory vault's edit/
  delete buttons. The one backend-generated emoji (the code-request
  "Tip:" message in `llm.py`) also lost its 💡 prefix for consistency.
  Static icon buttons get their markup filled in once on load instead of
  baking emoji into the HTML, so `ICONS` is the single source of truth.
- Logo: mark grew from 22px to 34px with a stronger glow and a playful
  hover rotation+scale (`cubic-bezier` spring easing); wordmark grew from
  18px to 30px, weight 900, and switched back to gradient-filled text
  (plain solid color read as too plain at this size) — a real logo
  lockup now, not a resize of the same treatment.
- Sidebar items: the always-visible pin+delete icon pair is gone,
  replaced by a single hover-reveal "..." button plus a right-click
  handler on the whole item — both open the same shared `#conv-menu`
  (Pin/Unpin, Delete), positioned at the click point and clamped to stay
  inside the viewport. Delete still confirms before doing anything, same
  as before.

### Verification
Every `icon("name")` call cross-checked against the `ICONS` table — all
15 match, no typos. Full-file scan for remaining emoji/pictograph
characters (Unicode emoji ranges) — none found; the one hit (→) is a
plain typographic arrow in existing UI text, not a pictograph, left as
is. CSS brace balance, JS balance, and HTML-parser validity re-checked
after the full rework. Confirmed `llm.py` still imports cleanly and the
code-request tip message now reads "Tip: ..." with no emoji, tested
directly (no data written). Live server confirmed serving the updated
page. No browser automation available in-session — visual confirmation
of the icons, logo scale, and menu positioning is Carter's, same caveat
as every GUI pass this session.

## Fix: reference chip permanently visible as an empty bar

### What happened
Carter asked what the bar above the composer was — it was always
visible, even with no reference active. It's the "reply to this message"
chip (`#reference-chip`), meant to stay hidden until the reply icon is
clicked. Its own CSS sets `display: flex` directly; since an ID selector
beats the browser's default `[hidden] { display: none }` rule in
specificity, the `hidden` attribute was silently losing that fight the
entire time this feature has existed — not something introduced this
session.

### Fix
Added `#reference-chip[hidden] { display: none; }`, the exact pattern
already correctly used for `.conv-menu[hidden]` and
`.modal-backdrop[hidden]` elsewhere in the same file — those two should
have been the template from the start.

## Milestone: multi-document upload and cross-document querying

### What Carter asked for
Asked how many files could be uploaded for the local model to
summarize/go through — answer at the time was "one, capped at 8,000
characters, no cross-file querying." Asked to build real support for
this "even if it's a big project," specifically tied to the North
Star's lawyer-with-hundreds-of-case-files scenario.

### Design, stated before building
- Multiple files at once (browser picker gets `multiple`), uploaded
  sequentially, not in parallel — avoids racing writes to the single
  `documents.json` store.
- Each file is chunked and embedded in full, not capped at the existing
  8,000-char summary limit — that cap was only ever meant for one quick
  read, not real document storage.
- Documents are scoped to the conversation they're uploaded into, same
  split as conversation-recall: ambient retrieval during chat only
  searches the active conversation's documents (a different case's
  files never bleed into this chat's answers — a correctness/liability
  boundary for the lawyer scenario, not just consistency for its own
  sake). A global cross-chat document search could be a separate
  explicit tool later, mirroring the Recall panel's split from ambient
  chat-recall.
- Stays fully local — document content never reaches a cloud-bound mode,
  same as the existing "file reads never leave the machine" rule. Only
  `ask_llm()`'s always-local `chat` branch sees document context.

### What changed
- New `documents.py`: `chunk_text()` (1500-char chunks, 200-char overlap,
  breaks on a paragraph/sentence boundary near the target size when one
  exists), `add_document()`, `list_documents()`, `search_documents()`
  (cosine similarity, scoped to one conversation, reuses
  `memory.py`'s `_cosine_similarity` rather than duplicating it). New
  `documents.json` — added to `.gitignore` immediately, before it could
  ever hold real uploaded content.
- `llm.py`'s `_summarize_file_content()` now chunks/embeds/stores the
  full original content alongside generating the existing (still
  truncated) immediate summary — two different things with two
  different limits now, not one. `ask_llm()`'s `chat` branch gained a
  `document_block`, built the same way as the existing conversation-
  recall `related_block`: embed the question, search this conversation's
  document chunks, keep only matches scoring ≥0.5, inject with
  instructions to cite the filename and never invent content beyond
  what's shown.
- `app.py`: new `GET /api/conversations/<id>/documents` for visibility
  into what's been stored (no dedicated GUI panel yet, but the data's
  there for one later with no backend work needed).
- `index.html`: file input gained `multiple`; the upload handler now
  loops over every selected file and awaits each one in turn before
  starting the next.

### Verification
All with synthetic test files (a fake contract and a fake recipe, never
real documents), cleaned up completely afterward — `documents.json`
deleted outright each time (confirmed it didn't exist before any test
began, so this was always safe), test conversations removed from the
real `memory.json`, real conversation count and `legacy`'s 114 turns
confirmed unchanged throughout.
1. Uploaded both test files through the real pipeline — correct
   summaries, 2 chunks each stored.
2. Queried `search_documents()` directly for "contract value" and for
   "banana bread baking time" — each correctly ranked its own document's
   chunks above 0.5 and the *other* document's chunks below it,
   confirming cross-document isolation actually works, not just in
   theory.
3. Full `ask_llm()` chat-path test: asked about the contract's value and
   its termination clause — both answered correctly, citing the
   filename. Asked an unanswerable question ("what color is the car in
   my documents") — correctly said it had no such information rather
   than inventing one (though it volunteered an unrelated real fact from
   personal memory alongside — expected, since `chat` mode always loads
   personal memory too; not a bug, just two context sources answering
   together).
4. Full live HTTP round trip through the running server — upload,
   `GET .../documents` listing, then a chat question — all correct.
   Note: the model didn't always literally name the filename in its
   citation (said "the summary I provided" once instead of the filename)
   despite the explicit instruction to — minor instruction-following
   looseness, not a correctness problem (the fact itself was right), and
   not worth chasing per this project's established "don't chase
   prompt-tuning whack-a-mole" rule.

### Known scope cuts, not started
No dedicated GUI panel for browsing/deleting uploaded documents yet
(the listing endpoint exists for one later). No cross-conversation
document search tool (ambient retrieval is conversation-scoped only, by
design — see above). No chunk/document deletion function yet — nothing
calls it, so it wasn't built ahead of an actual need.

## Milestone: drag-and-drop file upload

### What Carter asked for
Drag-and-drop for file uploads, with a visible indicator showing where
to drop while dragging.

### What changed
- `index.html`: window-level `dragenter`/`dragover`/`dragleave`/`drop`
  listeners, gated on `isFileDrag()` (checks `dataTransfer.types`
  includes `"Files"`) so dragging text/links around the page doesn't
  trigger it. A `dragDepth` counter tracks net enter/leave —
  `dragenter`/`dragleave` fire repeatedly as the cursor crosses child
  elements, so a plain "did I just get one enter event" check would
  flicker the overlay or leave it stuck; the counter only hides it once
  it's back to zero.
- New `#drop-overlay`: a full-window dashed-border card with an upload
  icon and "Drop files to add them to this chat," `pointer-events: none`
  so it never intercepts the drag/drop events itself (they're bound to
  `window`, not the overlay).
- Refactored the existing upload handler into a shared `uploadFiles()`
  — both the attach-button picker and the new drop handler call the
  same function (which itself loops `uploadOneFile()` sequentially,
  same multi-file pipeline from the previous milestone), so there's one
  upload path, not two that could drift apart.

### Verification
CSS brace balance, JS balance, and HTML-parser validity re-checked;
confirmed both new element ids (`drop-overlay`, `drop-overlay-icon`)
exist exactly once. No browser automation available in-session — actual
drag-and-drop interaction (the one part of this milestone that's
genuinely hard to verify without a real browser) is Carter's to confirm
directly, more than any other change this session.

## Polish: animated sparkle replaces "ASTI is thinking…" text

### What changed
`addThinking()` no longer renders plain text. It reuses the logo's
4-point sparkle mark (its own gradient def, not a reference to the
header's, so this element stays self-contained), animated with a
`rotate + scale` keyframe loop — spins a full turn while pulsing size,
looping for as long as the response is pending. Carter's call: the mark
already reads as "ASTI" from the header, so no label is needed here at
all, text or otherwise.

### Verification
CSS brace balance, JS balance, and HTML-parser validity re-checked.
Live server confirmed still serving the page. The animation itself
(timing, whether the spin/pulse actually reads well in motion) isn't
something a structural check can confirm — Carter's to look at.

## Fix: deleting a chat now deletes its documents too

### What happened
Carter asked whether deleting a chat deletes what ASTI "learned" from
it or just the words. Answer surfaced a real bug while checking:
`delete_conversation()` only ever removed `memory.json`'s turns —
anything uploaded to that chat stayed permanently orphaned in
`documents.json`, with no deletion path at all. Confirmed this wasn't
theoretical: Carter's real `documents.json` already had 3 orphaned
entries (real invoice files) from a chat he'd already deleted.

### What "delete" actually means now, for the record
- Conversation turns + their embeddings: deleted, fully.
- Confirmed/saved personal_memory.json facts: **not** deleted by chat
  deletion — that's a deliberately separate, persistent store (the
  Memory panel's delete is the right tool for removing a specific
  learned fact).
- Uploaded documents attached to that chat: now deleted too (this fix).

### What changed
`documents.py`: new `delete_documents_for_conversation(conversation_id)`
— removes every document and chunk belonging to that conversation.
`app.py`'s `DELETE /api/conversations/<id>` route now calls it right
after `delete_conversation()` succeeds.

### Verification
Throwaway conversation + throwaway document, via the real HTTP delete
route — confirmed the document existed before, was gone after, and the
conversation count was unaffected otherwise. Then, with Carter's
explicit go-ahead, ran the new function directly against the real
`documents.json` for the already-deleted conversation id that owned the
3 real orphaned entries — confirmed all 3 removed, `documents.json` back
to empty (nothing else in it at the time). Live server confirmed
reloaded and serving correctly after the code change.

## Diagnostics expanded, and made readable to a non-technical user

### What changed
Carter asked to "expand diagnostics to make it more informative to the
user/client" (roadmap #6's "privacy-safe diagnostics" item). Two parts:

**More counted.** `_collect_diagnostics()` (new, llm.py — replaces the
old single-purpose `build_diagnostics_report()`) adds what the recent
features never surfaced: document counts (`document_stats()`, new in
documents.py — files/chunks/conversations, never filenames or content),
conversation count (via the already-existing `list_conversations()`),
and outbound-call health (ok/error split, timestamp + status of the
most recent call — not just a raw count). Same privacy-safe rule as
before: config and counts only, nothing that reveals content.

**More readable.** The GUI's Diagnostics panel was a raw monospace
`<pre>` dump of CLI-style lines — fine for Carter, opaque for the
lawyer/small-business audience this product is actually for. It's now
three grouped, plain-English sections (Privacy / What's stored / Model
gateway) with small green/red dot indicators on the things that are
genuinely health signals (is the local model actually running, is
encryption actually on, is a cloud key actually configured) and no dot
on settings that are just a current state, not a pass/fail (cloud
access allowed/blocked is a toggle, not a problem either way). A
one-line note calls out plainly whether any data has left the device
yet, and if so, when. The original plain-text report still exists,
collapsed under "View as plain text" — kept for parity with the CLI's
`/status` and as a copy-paste-able form, not removed.

`build_diagnostics_report()` (CLI's `/status`, unchanged in behavior)
and the new `build_diagnostics_data()` (GUI) both now read from the same
`_collect_diagnostics()` — one source of truth, two presentations.
`/api/status` returns both `report` and `data` so neither consumer
had to change what it already expected.

### Verification
Called `build_diagnostics_report()`/`build_diagnostics_data()` directly
against Carter's real data — correct counts (6 conversations, 125
turns, 16 memory entries, 38 outbound calls/36 ok/2 error, 0 documents
at the time). Confirmed live over HTTP (`/api/status`) after the
server's auto-reload. Since no browser is available in-session: used
`osascript -l JavaScript` (macOS's JavaScriptCore) to parse the page's
full script block for syntax errors (none), then fed `renderStatus()`
itself the same real numbers in isolation and printed the HTML it
produced — confirmed correct nesting, correct dot placement, correct
wording, before trusting it to Carter's browser. HTML-parser validity
and brace/paren/bracket balance re-checked on the whole file. Actual
visual appearance is Carter's to confirm.

## Recall and Memory panels given the same plain-language treatment; Settings added

### What changed
Carter liked the diagnostics redesign and asked for the same treatment
on Semantic Recall and Personal Memory, plus a Settings panel with
"basic settings that would come with a shipped product of this kind."

**Semantic Recall.** Raw cosine similarity ("score 0.842") meant
nothing to a non-technical reader. Results now show a plain-language
`relevanceLabel()` ("Strong match" / "Good match" / "Possible match" /
"Weak match") with the exact number still available on hover (a
tooltip) for Carter's own debugging — same pattern as diagnostics'
"friendly default, technical detail still reachable." A one-line intro
under the panel header explains what it actually does in plain words.

**Personal Memory.** Added a summary line ("16 facts across 5/6
categories") and a per-category count next to each heading, plus a
one-line intro. The Export button now says plainly what it produces —
"Saved as an encrypted file... not a plain-text backup" — surfacing the
open question flagged in CLAUDE.md roadmap #4 honestly in the UI
instead of leaving it silent.

**Settings (new).** A gear icon in the header opens a panel built from
the same grouped-section language as Diagnostics (reusing
`.status-section`/`.status-row` CSS, not a new visual language):
- *Privacy* — the cloud-access toggle, mirrored here from the header
  (same control, two locations; `cloudToggleEls` now holds both button
  elements and a single render/click path keeps them in sync).
- *Data management* — Export personal memory, with the same
  encrypted-export note as the Memory panel.
- *Danger zone* — three bulk actions, each confirm-gated with the
  live count pulled from `/api/status` in the message itself ("Delete
  all conversations (6)?" not just "Delete all conversations?"):
  - **Clear uploaded documents** — new backend: `delete_all_documents()`
    (documents.py) + `DELETE /api/documents` (app.py). Unlike the
    per-conversation cascade delete, this is a standalone bulk wipe of
    `documents.json` alone; conversations are untouched.
  - **Forget all remembered facts** — no new backend. Loops the
    existing `/api/memory/forget` over every category/key from
    `GET /api/memory`, client-side, sequentially (same safe pattern
    multi-file upload already established for not racing writes to one
    JSON store).
  - **Delete all conversations** — no new backend either. Loops the
    existing per-conversation `DELETE /api/conversations/<id>` (which
    already cascades document deletion, 10/14's earlier fix), then
    calls the existing `startNewConversation()` to reset the view.
- *About* — app name and the North Star line verbatim ("Private by
  architecture. Local by default. Cloud by choice. User controlled."),
  plus a shortcut into the full Diagnostics panel.

### Verification
New backend (`delete_all_documents()` + its route): backed up the real
(already-empty) `documents.json` first per standing rule, added a
throwaway document via the real `add_document()`/`/api/read` path,
confirmed it existed, called the new function/route, confirmed
`documents.json` was empty after, then restored the pre-test file from
backup and re-verified its content matched exactly. Also exercised the
full route via the Flask test client with a throwaway conversation +
upload end to end, then cleaned up the throwaway conversation and
restored `documents.json` again.

The two bulk actions that loop over existing single-item endpoints
(forget-all-memory, delete-all-conversations) were **not** run against
Carter's real data — that would mean actually wiping his real facts and
chats to test a button. Instead, their exact JS logic (the same loop/
counting code as shipped) was run in isolation under `osascript -l
JavaScript` against a mocked `fetch`/`confirm`, confirming the right
number of calls, the right final counts, and that
`startNewConversation()` fires at the end — without touching the real
server or real data at all. The single-item endpoints underneath them
were already verified working in earlier milestones.

Structural checks re-run on the whole file after all changes:
HTML-parser validity, brace/paren/bracket balance, full-script-block
syntax via JavaScriptCore, and a cross-check that every
`getElementById` call in the JS matches exactly one `id=` in the HTML
(58 ids, zero missing, zero duplicates). Live server confirmed serving
the updated page and `/api/status` throughout. Actual visual look and
feel — especially the mirrored cloud toggle, the gear icon, and the
danger-zone confirmations in a real browser — is Carter's to confirm.

## "Show in Finder" — Data & Privacy section in Settings

### What happened
Carter asked whether a "go to my data" button is even possible — a
browser page can't open a native file browser itself (sandboxed, for
good reason: no website should be able to pop a user's Finder). But
ASTI's backend is a local Flask process on the same machine as the
browser, not a remote server, so it can run `open <path>` itself when
asked. Asked what the best version of this looks like for a shipped
product in this category; recommended the pattern privacy-forward
local-data products use (Obsidian's vault location, 1Password's vault
path): show the actual folder path as plain text — the real
trust-builder, since it's proof of "local by default" even if no one
ever clicks a button — with a "Show in Finder" button alongside as a
convenience. Carter agreed; built it.

### What changed
`app.py`: `DATA_DIR = os.path.dirname(os.path.abspath(__file__))` — the
`agent/` directory itself, where memory.json/personal_memory.json/
documents.json/etc. actually live, not whatever the process's cwd
happens to be. Two new routes: `GET /api/data-location` (returns the
path) and `POST /api/data-location/reveal` (runs `open` on macOS,
`explorer` on Windows, `xdg-open` elsewhere, against that fixed
server-side path — never a user-supplied one). Settings panel gets a
new "Data & Privacy" section, between the cloud toggle and Data
management: the path in a monospace box, a reassuring line ("Your data
lives here, encrypted, and stays on this device unless you turn Cloud
on"), and the Show in Finder button.

**Why this is safe here and wouldn't be elsewhere:** this only works
because ASTI is bound to 127.0.0.1 and the browser and server are
always the same machine, same user, same session — the server is
opening its own machine's file browser to its own fixed path. The
moment ASTI became a hosted/remote product (discussed earlier this
session), this feature would have to be removed outright, not adapted —
a remote server opening a file browser on someone else's request is a
different, dangerous thing. Noted in both `app.py`'s comment and here.

### Verification
`GET /api/data-location` checked directly against the live server —
correct path returned. `POST /api/data-location/reveal` was run for
real (not just logic-checked) since it's non-destructive: it only pops
a Finder window, touches no data, and is exactly what Carter asked to
see working. Full structural sweep re-run after the change: HTML-parser
validity, brace/paren/bracket balance, full-script-block syntax via
JavaScriptCore, and the `getElementById`-vs-`id=` cross-check (clean).
Live server confirmed serving the updated page throughout. Actual
Finder-window appearance is Carter's to confirm, same caveat as every
GUI change this session.