from flask import Flask, request, jsonify
import requests

app = Flask(__name__)

# URL of the Proxy
PROXY_URL = "http://<PROXY_IP:8080/query"  # replace with Proxy private IP

# Simple demo API key
API_KEY = "secret123"

def validate_sql(sql):
    forbidden = ["drop", "delete all", "truncate"]
    for word in forbidden:
        if word in sql.lower():
            return False
    return True

@app.route("/query", methods=["POST"])
def handle_query():
    data = request.json
    key = data.get("api_key")
    sql = data.get("sql", "")

    # Check API key
    if key != API_KEY:
        return jsonify({"error": "Invalid API key"}), 401

    # Validate SQL
    if not validate_sql(sql):
        return jsonify({"error": "Unsafe query"}), 400

    # Forward to Proxy
    try:
        resp = requests.post(PROXY_URL, json={"sql": sql})
        return jsonify(resp.json())
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8081)