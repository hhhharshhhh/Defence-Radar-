from flask import Flask, render_template, request, jsonify
import socket
import logging

app = Flask(__name__)
logging.basicConfig(level=logging.INFO)

RADAR_HOST = "127.0.0.1"
RADAR_PORT = 5050
TIMEOUT = 6.0  # seconds

def send_to_radar(command: str) -> str:
    """
    Connects to radar TCP server, sends a single-line command,
    reads full response until socket closes or timeout, returns text.
    """
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.settimeout(TIMEOUT)
            s.connect((RADAR_HOST, RADAR_PORT))
            s.sendall(command.encode("utf-8"))
            # Receive until server closes / times out
            chunks = []
            while True:
                try:
                    data = s.recv(4096)
                    if not data:
                        break
                    chunks.append(data.decode("utf-8"))
                except socket.timeout:
                    break
        return "".join(chunks) or "No response from radar server."
    except Exception as e:
        return f"ERROR: Unable to contact radar server. ({str(e)})"

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/api/command", methods=["POST"])
def api_command():
    """
    Expects form/json: { "cmd": "scan" }
    Returns JSON: { "ok": True, "reply": "..." }
    """
    cmd = request.form.get("cmd") or request.json.get("cmd")
    if not cmd:
        return jsonify({"ok": False, "reply": "No command provided."}), 400

    reply = send_to_radar(cmd.strip())
    return jsonify({"ok": True, "reply": reply})

if __name__ == "__main__":
    print("🚀 Starting Flask UI (Command Center) on http://0.0.0.0:8080")
    app.run(host="0.0.0.0", port=8080, debug=False)
