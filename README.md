# ASTI

**A self-hosted AI assistant that remembers you — and never leaves your machine unless you say so.**

ASTI is a personal AI assistant that runs on your own hardware. It keeps a structured,
persistent memory of who you are, answers from a local model by default, and only ever
calls a cloud model when you've explicitly allowed it — and even then, your memory,
documents, and conversation history never leave your machine.

> **Private by architecture. Local by default. Cloud by choice. User controlled.**

---

## Why

Most AI assistants default to sending everything you say to someone else's server. ASTI
inverts that: the local model and your own data are the default, and the cloud is an
opt-in feature for the handful of questions that genuinely benefit from a frontier model —
general-knowledge lookups and coding help — not a silent fallback.

This matters most for people who can't treat "it's probably fine" as good enough:
a lawyer with privileged case files, a clinician with patient details, a financial
advisor with client records. It also just matters to anyone who'd rather their own
assistant's memory of them stay their own.

## What it does

- **Persistent personal memory** — ASTI remembers facts about you (goals, preferences,
  people, projects) across every conversation, structured into categories, confirmed
  before anything is saved, and encrypted at rest.
- **Local by default, cloud by choice** — every message is routed to the right place:
  personal/contextual chat and anything touching an uploaded document stay on your local
  model; general-knowledge and coding questions can use a cloud model instead, but only
  if you've turned that on, and never with your memory, documents, or history attached.
- **Multi-document upload & Q&A** — upload PDFs, Word docs, or text files into a
  conversation and ask questions across all of them at once; retrieval is tuned to
  surface every document for broad questions, not just a handful of top matches.
  Document content always stays local — it's never eligible for the cloud path.
  Deleting a document or a conversation actually deletes its content, not just its
  listing.
- **Semantic recall** — chat responses draw on relevant past turns automatically,
  with built-in handling for stale or superseded facts so an old value doesn't
  outrank a newer one.
  - **Crisis-aware safety handling** — deterministic detection for self-harm/suicide
  risk language, a response style that stays engaged instead of refusing, and
  up-to-date crisis-line information — checked before routing, memory, or any cloud
  path is even considered.
- **Encryption at rest** — all stored data (conversations, personal memory, documents)
  is encrypted with a key held in your OS's native credential store (Keychain /
  Credential Manager / Secret Service), not a plaintext file.
- **A real privacy boundary, not just a setting** — cloud-eligible requests send only
  the current message and a system prompt. No memory, no document content, and no
  conversation history is ever part of a cloud call, by construction.
- **A GUI and a CLI** — a browser-based chat interface (conversation sidebar, document
  panel, Settings, diagnostics) for day-to-day use, and a terminal REPL for anyone who
  wants direct control, including the personal-memory commands the GUI intentionally
  keeps out of the chat surface.

## How it's built

```
Browser (GUI)  ──┐
                  ├──  Flask app (app.py)  ──  Router  ──┬── Local model   (Ollama)
Terminal (CLI) ──┘                                        └── Cloud model  (Anthropic API)
                                                               only when explicitly allowed,
                                                               only for general-knowledge/code,
                                                               never with memory or documents
```

- **Router** classifies every message (`chat`, `general_knowledge`, `code`, `recall`, …)
  and decides, per message, whether it's even eligible for the cloud path. An uploaded
  document in a conversation locks that whole conversation to the local model,
  permanently, regardless of topic — visibly, via a lock badge and a disabled toggle
  in the GUI, not just silently.
- **Personal memory** is structured (`identity`, `preferences`, `goals`, `projects`,
  `people`, `other`), extracted by the local model, validated and reconciled
  deterministically in Python, and only ever written after you confirm it.
- **Documents** are chunked, embedded, and stored per-conversation — never mixed across
  conversations — with coverage-aware retrieval so a "summarize every file" question
  can't silently drop documents the way a naive top-K search would.
- **Storage** goes through a single encrypted read/write layer; nothing reads or writes
  the data files directly.

## Getting started

Requires Python 3.11+ and [Ollama](https://ollama.com) running locally.

```bash
git clone https://github.com/cjyanosick/asti-ai-assistant.git
cd asti-ai-assistant

python3 -m venv venv
venv/bin/pip install -r requirements.txt

ollama pull qwen2.5:14b
ollama pull nomic-embed-text

cd agent
cp .env.example .env   # add ANTHROPIC_API_KEY only if you want the cloud path
venv/bin/python3 app.py
```

Open `http://127.0.0.1:5050` in a browser. The server binds to localhost only — it's
never reachable from another device.

Cloud access (Anthropic) is **off by default**. Turn it on from Settings whenever you
want it, and turn it back off whenever you don't — nothing about the local features
depends on it.

### CLI

```bash
cd agent
venv/bin/python3 llm.py
```

The terminal REPL shares the same backend as the GUI and adds direct personal-memory
commands: `/memory`, `/forget`, `/edit`, `/export`, `/recall`, `/read`, `/status`,
`/outbound`.

## Status

ASTI's personal-use core — chat, memory, documents, recall, encryption, local/cloud
routing, and a full GUI — is built and stress-tested, including dedicated passes
simulating privacy-sensitive professional use (legal, medical, financial) and a
suicide-crisis scenario. It's a real, working personal assistant today.

Known, open limitations: the local model occasionally fabricates specifics like legal
citations (flagged automatically when it happens, not silently trusted); document
search is scoped to one conversation at a time by design; and this hasn't yet gone
through compliance review for any regulated industry, so it isn't a HIPAA/FINRA/legal-
ethics-compliant product out of the box.

## License

All rights reserved. No license has been granted for use, modification, or
redistribution.
