import requests
import time
import csv

GATEKEEPER_URL = "http://<GATAKEEPER_IP>:8081/query"
API_KEY = "secret123" 
NUM_QUERIES = 1000  

def run_benchmark(strategy_label):
    node_usage = {}
    latencies = []
    success_count = 0

    print(f"\n--- Starting test: {strategy_label} ---")
    
    start_test_time = time.time()

    for i in range(NUM_QUERIES):
        sql = "SELECT * FROM film LIMIT 1"
        
        send_time = time.time()
        try:
            r = requests.post(GATEKEEPER_URL, json={"sql": sql, "api_key": API_KEY}, timeout=10)
            duration = time.time() - send_time
            resp = r.json()
            
            if r.status_code == 200:
                success_count += 1
                latencies.append(duration)
                
                node = resp.get("node", "unknown")
                node_usage[node] = node_usage.get(node, 0) + 1
        except Exception as e:
            print(f"Error {i}: {e}")

    total_time = time.time() - start_test_time
    avg_latency = (sum(latencies) / len(latencies)) * 1000 if latencies else 0

    print(f"Total time: {total_time:.2f} seconds")
    print(f"Avrage latancy: {avg_latency:.2f} ms")
    print(f"Node usage: {node_usage}")
    print(f"Success rate: {(success_count/NUM_QUERIES)*100:.1f}%")
    
    return avg_latency

run_benchmark("Cuztomized")