from flask import Flask, request, jsonify
import mysql.connector
import random
import time

app = Flask(__name__)


MANAGER = {
    "host": "<MANAGER_IP",
    "user": "gatekeeper",
    "password": "gatekeeperpass",
    "database": "sakila"
}

WORKERS = [
    {"host": "<WORKER1:IP", "user": "gatekeeper", "password": "gatekeeperpass", "database": "sakila"},
    {"host": "<WORKER2:IP", "user": "gatekeeper", "password": "gatekeeperpass", "database": "sakila"}
]

# --- Choose the strategy ---
# Alternatives: "direct", "random", "customized"
CURRENT_STRATEGY = "customized" 

def safe_serialize(result):
    if isinstance(result, dict):
        return {k: safe_serialize(v) for k, v in result.items()}
    elif isinstance(result, list):
        return [safe_serialize(v) for v in result]
    elif isinstance(result, set):
        return list(result)
    return result

# --- Customized---
def get_latency(node):
    start = time.time()
    try:
        conn = mysql.connector.connect(**node, connect_timeout=1)
        conn.ping()
        conn.close()
        return time.time() - start
    except:
        return 999.0

def query_db(node, sql):
    conn = mysql.connector.connect(**node)
    cursor = conn.cursor(dictionary=True)
    cursor.execute(sql)
    if sql.lower().strip().startswith("select"):
        result = cursor.fetchall()
        result = safe_serialize(result)
    else:
        conn.commit()
        result = {"status": "OK"}
    cursor.close()
    conn.close()
    return result

@app.route("/query", methods=["POST"])
def handle_query():
    data = request.json
    sql = data.get("sql", "")

    is_read = sql.lower().strip().startswith("select")

    if not is_read:
        node = MANAGER
    else:
        if CURRENT_STRATEGY == "direct":
            node = MANAGER
        elif CURRENT_STRATEGY == "customized":
            node = min(WORKERS, key=lambda w: get_latency(w))
        else: 
            node = random.choice(WORKERS)

    try:
        result = query_db(node, sql)
        return jsonify({"result": result, "node": node["host"], "strategy": CURRENT_STRATEGY})
    except Exception as e:
        return jsonify({"error": str(e), "node": node.get("host", "unknown")}), 500

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080)
