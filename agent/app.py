from flask import Flask, request, jsonify, send_from_directory

from llm import process_turn

app = Flask(__name__, static_folder="static", static_url_path="")


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


if __name__ == "__main__":
    # Explicit 127.0.0.1, not the Flask default alone — this binds to
    # localhost only, never the network. Personal data runs through this;
    # it should never be reachable from another device by accident.
    app.run(host="127.0.0.1", port=5050, debug=True)
