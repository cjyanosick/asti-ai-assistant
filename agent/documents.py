import datetime
import uuid

from storage import load_json, save_json
from memory import _cosine_similarity

DOCUMENTS_FILE = "documents.json"

# Tuned for personal/professional-document scale (a few pages to a few
# hundred), not web-scale RAG — simple fixed-size chunking with a small
# overlap so a fact sitting right at a chunk boundary isn't lost entirely.
CHUNK_SIZE = 1500
CHUNK_OVERLAP = 200


def _now():
    return datetime.datetime.now().isoformat()


def _load_store():
    return load_json(DOCUMENTS_FILE, {"documents": {}, "chunks": []})


def _save_store(store):
    save_json(DOCUMENTS_FILE, store)


def chunk_text(text):
    # Breaks on a paragraph or sentence boundary near the target size when
    # one exists nearby, otherwise just slices — good enough for prose and
    # most real documents without pulling in a sentence tokenizer.
    text = text.strip()
    if not text:
        return []

    chunks = []
    start = 0
    length = len(text)

    while start < length:
        end = min(start + CHUNK_SIZE, length)

        if end < length:
            break_point = text.rfind("\n\n", start, end)
            if break_point == -1 or break_point <= start:
                break_point = text.rfind(". ", start, end)
            if break_point != -1 and break_point > start:
                end = break_point + 1

        chunk = text[start:end].strip()
        if chunk:
            chunks.append(chunk)

        start = end - CHUNK_OVERLAP if end - CHUNK_OVERLAP > start else end

    return chunks


def add_document(conversation_id, filename, text, embed_fn):
    # embed_fn: callable(str) -> list[float], injected rather than imported
    # directly so this module doesn't need to depend on model_provider —
    # same dependency direction memory.py keeps clean.
    store = _load_store()
    doc_id = uuid.uuid4().hex[:12]

    chunk_records = []
    for idx, chunk in enumerate(chunk_text(text)):
        try:
            embedding = embed_fn(chunk)
        except Exception:
            embedding = None
        chunk_records.append({
            "doc_id": doc_id,
            "chunk_index": idx,
            "text": chunk,
            "embedding": embedding,
        })

    store["documents"][doc_id] = {
        "id": doc_id,
        "filename": filename,
        "conversation_id": conversation_id,
        "uploaded_at": _now(),
        "chunk_count": len(chunk_records),
    }
    store["chunks"].extend(chunk_records)
    _save_store(store)
    return doc_id


def list_documents(conversation_id):
    store = _load_store()
    return [
        d for d in store["documents"].values()
        if d["conversation_id"] == conversation_id
    ]


def delete_documents_for_conversation(conversation_id):
    # Called when a conversation is deleted (app.py) — found as a real
    # bug 10/14: deleting a chat only ever removed memory.json's turns,
    # leaving that chat's uploaded documents permanently orphaned in
    # documents.json with no way to remove them at all. "Delete chat"
    # has to mean its document content is actually gone too, not quietly
    # retained — especially for this product's stated use case (a
    # lawyer's case files, a business's real documents).
    store = _load_store()
    doc_ids = {
        doc_id for doc_id, d in store["documents"].items()
        if d["conversation_id"] == conversation_id
    }

    if not doc_ids:
        return 0

    for doc_id in doc_ids:
        del store["documents"][doc_id]
    store["chunks"] = [c for c in store["chunks"] if c["doc_id"] not in doc_ids]

    _save_store(store)
    return len(doc_ids)


def delete_document(conversation_id, doc_id):
    # Single-document delete (10/14) — the GUI's new per-chat Documents
    # panel. Scoped to conversation_id on purpose, same reasoning as every
    # other document boundary in this file: a doc_id alone shouldn't be
    # enough to delete something from a chat you're not even looking at.
    store = _load_store()
    doc = store["documents"].get(doc_id)

    if doc is None or doc["conversation_id"] != conversation_id:
        return False

    del store["documents"][doc_id]
    store["chunks"] = [c for c in store["chunks"] if c["doc_id"] != doc_id]
    _save_store(store)
    return True


def delete_all_documents():
    # Settings panel's "Clear uploaded documents". Returns (count,
    # doc_ids) — the caller (app.py) uses doc_ids to also cascade-delete
    # each document's upload-summary turn from memory.json, same reasoning
    # as the single-document delete route (document stress test, 10/14):
    # without this, "Clear uploaded documents" wiped documents.json but
    # left every document's content fully recallable from conversation
    # history, which isn't what "clear uploaded documents" should mean.
    store = _load_store()
    doc_ids = list(store["documents"].keys())
    if doc_ids:
        _save_store({"documents": {}, "chunks": []})
    return len(doc_ids), doc_ids


def document_stats():
    # Global counts for diagnostics (roadmap #6, "privacy-safe diagnostics")
    # — file/chunk counts only, never filenames or content, same rule the
    # rest of build_diagnostics_report() follows.
    store = _load_store()
    conv_ids = {d["conversation_id"] for d in store["documents"].values()}
    return {
        "documents": len(store["documents"]),
        "chunks": len(store["chunks"]),
        "conversations": len(conv_ids),
    }


def search_documents(conversation_id, query_embedding, top_k=5):
    # Scoped to one conversation on purpose — ambient document context for
    # the model answering a question shouldn't mix documents from an
    # unrelated chat (a different client's case files, a different
    # project's contracts). Brute-force cosine similarity, same as
    # memory.py's semantic search — fine at personal/professional scale
    # (hundreds of chunks per conversation, not millions).
    #
    # Returns (score, filename, text, uploaded_at) — uploaded_at added
    # 10/14 (document stress test): re-uploading a corrected file under
    # the same filename left both versions in the store with identical
    # labels and no way for the model to tell which was current; a stale
    # chunk even scored higher than the corrected one in testing. The
    # timestamp lets llm.py tell the model which same-named source is
    # actually the most recent, instead of it guessing.
    store = _load_store()
    scored = []

    for chunk in store["chunks"]:
        doc = store["documents"].get(chunk["doc_id"])
        if doc is None or doc["conversation_id"] != conversation_id:
            continue
        if chunk.get("embedding") is None:
            continue
        score = _cosine_similarity(query_embedding, chunk["embedding"])
        scored.append((score, doc["filename"], chunk["text"], doc["uploaded_at"]))

    scored.sort(reverse=True, key=lambda x: x[0])
    return scored[:top_k]


def search_documents_by_coverage(conversation_id, query_embedding, per_document=1):
    # Found 10/14 (document-pipeline stress test): plain top-k search is
    # global across every chunk in the conversation, not per-document — 8
    # small case files uploaded, asked to "list all clients across every
    # case file", and only 5 of the 8 ever made the cut. The model then
    # presented that partial list as if it were complete, with nothing
    # anywhere saying 3 files were silently left out. For a broad/
    # enumerative question (see _BROAD_DOCUMENT_QUERY_RE in llm.py), this
    # guarantees every document contributes at least `per_document`
    # chunk(s) regardless of its relevance score — the point of a "list
    # everything" question is coverage, not relevance ranking, so there's
    # no score threshold here the way search_documents() has one.
    store = _load_store()
    by_doc = {}

    for chunk in store["chunks"]:
        doc = store["documents"].get(chunk["doc_id"])
        if doc is None or doc["conversation_id"] != conversation_id:
            continue
        if chunk.get("embedding") is None:
            continue
        score = _cosine_similarity(query_embedding, chunk["embedding"])
        by_doc.setdefault(chunk["doc_id"], []).append(
            (score, doc["filename"], chunk["text"], doc["uploaded_at"])
        )

    results = []
    for scored_chunks in by_doc.values():
        scored_chunks.sort(reverse=True, key=lambda x: x[0])
        results.extend(scored_chunks[:per_document])

    results.sort(reverse=True, key=lambda x: x[0])
    return results
