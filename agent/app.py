from flask import Flask, request, jsonify, send_from_directory

from llm import process_turn, summarize_uploaded_file, ALLOWED_MEMORY_CATEGORIES
from memory import (
    semantic_search,
    load_personal_memory,
    update_personal_memory,
    forget_personal_memory,
    export_personal_memory,
)
from model_provider import generate_embedding
from tasks import load_tasks, add_task, complete_task

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

    if not message:
        return jsonify({"error": "message is required"}), 400

    intent, response = process_turn(message)

    return jsonify({"intent": intent, "response": response})


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

    uploaded = request.files["file"]
    summary = summarize_uploaded_file(uploaded.filename, uploaded.read())

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


@app.route("/api/tasks", methods=["GET"])
def get_tasks():
    return jsonify(load_tasks())


@app.route("/api/tasks/add", methods=["POST"])
def add_task_route():
    data = request.get_json(silent=True) or {}
    text = (data.get("text") or "").strip()

    if not text:
        return jsonify({"error": "text is required"}), 400

    task = add_task(text)
    return jsonify(task)


@app.route("/api/tasks/complete", methods=["POST"])
def complete_task_route():
    data = request.get_json(silent=True) or {}
    task_id = data.get("id")

    if not isinstance(task_id, int):
        return jsonify({"error": "id (integer) is required"}), 400

    if complete_task(task_id):
        return jsonify({"status": "ok"})

    return jsonify({"error": f"no task with id {task_id}"}), 404


if __name__ == "__main__":
    # Explicit 127.0.0.1, not the Flask default alone — this binds to
    # localhost only, never the network. Personal data runs through this;
    # it should never be reachable from another device by accident.
    app.run(host="127.0.0.1", port=5050, debug=True)
