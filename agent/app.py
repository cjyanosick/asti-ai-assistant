from flask import Flask, request, jsonify, send_from_directory

from llm import (
    process_turn,
    summarize_uploaded_file,
    ALLOWED_MEMORY_CATEGORIES,
    build_diagnostics_report,
    build_diagnostics_data,
)
from memory import (
    semantic_search,
    create_conversation,
    get_conversation,
    list_conversations,
    delete_conversation,
    set_conversation_pinned,
    load_personal_memory,
    update_personal_memory,
    forget_personal_memory,
    export_personal_memory,
)
from model_provider import generate_embedding
from cloud_setting import is_cloud_allowed, set_cloud_allowed
from documents import list_documents, delete_documents_for_conversation

app = Flask(__name__, static_folder="static", static_url_path="")
# Basic safety net against an accidental huge upload — not a hard
# requirement at personal-use scale, just good practice for a multipart
# endpoint. The real per-prompt cap is MAX_FILE_READ_CHARS in config.py.
app.config["MAX_CONTENT_LENGTH"] = 10 * 1024 * 1024


@app.route("/")
def index():
    return send_from_directory(app.static_folder, "index.html")


@app.route("/api/chat", methods=["POST"])
def chat():
    data = request.get_json(silent=True) or {}
    message = (data.get("message") or "").strip()
    reference = (data.get("reference") or "").strip() or None
    conversation_id = (data.get("conversation_id") or "").strip()

    if not message:
        return jsonify({"error": "message is required"}), 400
    if not conversation_id:
        return jsonify({"error": "conversation_id is required"}), 400

    intent, response, pending_memory, source = process_turn(conversation_id, message, reference=reference)

    return jsonify({
        "intent": intent,
        "response": response,
        "pending_memory": pending_memory,
        "source": source,
    })


@app.route("/api/conversations", methods=["POST"])
def new_conversation():
    # ChatGPT-style rework (10/14): the GUI calls this on every page open
    # and on "New Chat" — each open starts fresh, past chats live in the
    # sidebar (GET /api/conversations) instead of one endless scroll.
    conversation_id = create_conversation()
    return jsonify({"id": conversation_id})


@app.route("/api/conversations", methods=["GET"])
def conversation_list():
    # Sidebar listing — newest-updated first, empty/unused chats omitted
    # (see list_conversations()'s own comment for why).
    return jsonify({"conversations": list_conversations()})


@app.route("/api/conversations/<conversation_id>", methods=["GET"])
def conversation_detail(conversation_id):
    conv = get_conversation(conversation_id)
    if conv is None:
        return jsonify({"error": "conversation not found"}), 404

    return jsonify({
        "id": conv["id"],
        "title": conv["title"],
        "pinned": conv.get("pinned", False),
        "turns": [
            {"user": t["user"], "ai": t["ai"], "source": t.get("source")}
            for t in conv["turns"]
        ],
    })


@app.route("/api/conversations/<conversation_id>", methods=["DELETE"])
def delete_conversation_route(conversation_id):
    if delete_conversation(conversation_id):
        # Found 10/14: deleting a chat only ever removed its memory.json
        # turns — any documents uploaded to it were silently orphaned in
        # documents.json forever. "Delete chat" has to mean its documents
        # are actually gone too, not quietly retained.
        delete_documents_for_conversation(conversation_id)
        return jsonify({"status": "ok"})
    return jsonify({"error": "conversation not found"}), 404


@app.route("/api/conversations/<conversation_id>/documents", methods=["GET"])
def conversation_documents(conversation_id):
    # Visibility into what's actually been chunked/embedded for this
    # chat (multi-document querying, 10/14) — no dedicated GUI panel for
    # this yet, but the data's available for one later without any
    # backend work.
    docs = list_documents(conversation_id)
    return jsonify({
        "documents": [
            {
                "id": d["id"],
                "filename": d["filename"],
                "uploaded_at": d["uploaded_at"],
                "chunk_count": d["chunk_count"],
            }
            for d in docs
        ]
    })


@app.route("/api/conversations/<conversation_id>/pin", methods=["POST"])
def pin_conversation_route(conversation_id):
    data = request.get_json(silent=True) or {}
    pinned = data.get("pinned")

    if not isinstance(pinned, bool):
        return jsonify({"error": "pinned (boolean) is required"}), 400

    if set_conversation_pinned(conversation_id, pinned):
        return jsonify({"status": "ok", "pinned": pinned})
    return jsonify({"error": "conversation not found"}), 404


@app.route("/api/recall", methods=["POST"])
def recall():
    data = request.get_json(silent=True) or {}
    query = (data.get("query") or "").strip()

    if not query:
        return jsonify({"error": "query is required"}), 400

    results = semantic_search(generate_embedding(query), top_k=5)

    return jsonify({
        "results": [
            {"score": score, "user": item["user"], "ai": item["ai"]}
            for score, item in results
        ]
    })


@app.route("/api/read", methods=["POST"])
def read_file():
    # File tools, GUI entry point. Persists into conversation history the
    # same way the CLI's /read does (see _summarize_file_content in llm.py).
    if "file" not in request.files or request.files["file"].filename == "":
        return jsonify({"error": "file is required"}), 400

    conversation_id = (request.form.get("conversation_id") or "").strip()
    if not conversation_id:
        return jsonify({"error": "conversation_id is required"}), 400

    uploaded = request.files["file"]
    summary = summarize_uploaded_file(conversation_id, uploaded.filename, uploaded.read())

    return jsonify({"filename": uploaded.filename, "summary": summary})


@app.route("/api/memory", methods=["GET"])
def get_memory():
    return jsonify(load_personal_memory())


@app.route("/api/memory/edit", methods=["POST"])
def edit_memory():
    data = request.get_json(silent=True) or {}
    category = (data.get("category") or "").strip()
    key = (data.get("key") or "").strip()
    value = (data.get("value") or "").strip()

    if not category or not key or not value:
        return jsonify({"error": "category, key, and value are all required"}), 400

    if category not in ALLOWED_MEMORY_CATEGORIES:
        return jsonify({
            "error": f"unknown category '{category}'",
            "valid_categories": sorted(ALLOWED_MEMORY_CATEGORIES),
        }), 400

    update_personal_memory(category, key, value)
    return jsonify({"status": "ok"})


@app.route("/api/memory/confirm", methods=["POST"])
def confirm_memory():
    # Extraction-noise fix (10/13): /api/chat no longer saves an extracted
    # fact to personal_memory.json by itself — it returns it as
    # `pending_memory` and the GUI shows a Save/Discard chip under that
    # message. Nothing is written unless the user explicitly hits Save,
    # which calls this route. Same validation as /api/memory/edit.
    data = request.get_json(silent=True) or {}
    category = (data.get("category") or "").strip()
    key = (data.get("key") or "").strip()
    value = (data.get("value") or "").strip()

    if not category or not key or not value:
        return jsonify({"error": "category, key, and value are all required"}), 400

    if category not in ALLOWED_MEMORY_CATEGORIES:
        return jsonify({
            "error": f"unknown category '{category}'",
            "valid_categories": sorted(ALLOWED_MEMORY_CATEGORIES),
        }), 400

    update_personal_memory(category, key, value)
    return jsonify({"status": "ok"})


@app.route("/api/memory/forget", methods=["POST"])
def forget_memory():
    data = request.get_json(silent=True) or {}
    category = (data.get("category") or "").strip()
    key = (data.get("key") or "").strip()

    if not category or not key:
        return jsonify({"error": "category and key are required"}), 400

    if forget_personal_memory(category, key):
        return jsonify({"status": "ok"})

    return jsonify({"error": f"no entry found at {category}.{key}"}), 404


@app.route("/api/memory/export", methods=["POST"])
def export_memory():
    filename = export_personal_memory()
    return jsonify({"filename": filename})


@app.route("/api/settings/cloud", methods=["GET"])
def get_cloud_setting():
    return jsonify({"allow_cloud": is_cloud_allowed()})


@app.route("/api/settings/cloud", methods=["POST"])
def set_cloud_setting():
    data = request.get_json(silent=True) or {}
    allow_cloud = data.get("allow_cloud")

    if not isinstance(allow_cloud, bool):
        return jsonify({"error": "allow_cloud (boolean) is required"}), 400

    set_cloud_allowed(allow_cloud)
    return jsonify({"allow_cloud": is_cloud_allowed()})


@app.route("/api/status", methods=["GET"])
def get_status():
    # `report` is the plain-text form the CLI's /status also prints, kept
    # for parity/copy-paste; `data` is the same underlying counts
    # structured for the GUI's grouped, human-readable Status panel.
    # Both come from the same source of truth (_collect_diagnostics in
    # llm.py) — config/counts only, never content (roadmap #6).
    return jsonify({"report": build_diagnostics_report(), "data": build_diagnostics_data()})


if __name__ == "__main__":
    # Explicit 127.0.0.1, not the Flask default alone — this binds to
    # localhost only, never the network. Personal data runs through this;
    # it should never be reachable from another device by accident.
    app.run(host="127.0.0.1", port=5050, debug=True)
