from flask import Flask, request, jsonify
import threading
import time
from nodes import nodes
from pods import pods

timeout_interval = 10  # Time before marking a node as failed
heartbeat_timestamps = {}  # Stores last received heartbeats

def monitor_health():
    while True:
        time.sleep(timeout_interval)
        current_time = time.time()
        for node_id in list(heartbeat_timestamps.keys()):
            if current_time - heartbeat_timestamps[node_id] > timeout_interval:
                print(f"Node {node_id} is unresponsive. Marking as failed.")
                handle_node_failure(node_id)

def handle_node_failure(node_id):
    if node_id in nodes:
        failed_pods = nodes[node_id]["pods"]
        del nodes[node_id]  # Remove failed node
        redistribute_pods(failed_pods)

def redistribute_pods(failed_pods):
    for pod_id in failed_pods:
        pod_info = pods.pop(pod_id, None)
        if pod_info:
            cpu_request = pod_info["cpu_request"]
            for node_id, node in nodes.items():
                if node["available_cpu"] >= cpu_request:
                    node["pods"].append(pod_id)
                    node["available_cpu"] -= cpu_request
                    pods[pod_id] = {"node_id": node_id, "cpu_request": cpu_request}
                    print(f"Pod {pod_id} moved to Node {node_id}")
                    break
app = Flask(__name__)

@app.route("/heartbeat", methods=["POST"])
def receive_heartbeat():
    data = request.json
    node_id = data.get("node_id")
    if node_id in nodes:
        heartbeat_timestamps[node_id] = time.time()
        return jsonify({"message": "Heartbeat received"}), 200
    return jsonify({"error": "Node not found"}), 404

@app.route("/status", methods=["GET"])
def get_status():
    return jsonify({"nodes": nodes, "pods": pods})

# Start health monitoring in a separate thread
threading.Thread(target=monitor_health, daemon=True).start()

if __name__ == "__main__":
    app.run(debug=True)
