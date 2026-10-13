from flask import Flask, request, jsonify, send_from_directory

from llm import process_turn, summarize_uploaded_file
from memory import semantic_search
from model_provider import generate_embedding

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
    # File tools, GUI entry point. No persistence yet — same one-shot
    # behavior as the CLI's /read, deliberately a separate future slice.
    if "file" not in request.files or request.files["file"].filename == "":
        return jsonify({"error": "file is required"}), 400

    uploaded = request.files["file"]
    summary = summarize_uploaded_file(uploaded.filename, uploaded.read())

    return jsonify({"filename": uploaded.filename, "summary": summary})


if __name__ == "__main__":
    # Explicit 127.0.0.1, not the Flask default alone — this binds to
    # localhost only, never the network. Personal data runs through this;
    # it should never be reachable from another device by accident.
    app.run(host="127.0.0.1", port=5050, debug=True)
