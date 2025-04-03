from flask import Flask, jsonify, request
import docker
import uuid
import threading
import time

from scheduler.first_fit import first_fit
from scheduler.best_fit import best_fit
from scheduler.worst_fit import worst_fit

app = Flask(__name__)
client = docker.from_env()

nodes = {}  # Stores node details { node_id: { details } }
pods = {}  # Stores pod details { pod_id: { node_id, cpu_request } }

HEARTBEAT_TIMEOUT = 15 # Timeout in seconds before marking a node as failed


# --- NODE MANAGEMENT ---

@app.route('/add_node', methods=['POST'])
def add_node():
    data = request.json
    cpu_cores = data.get("cpu_cores", 2)  # Default to 2 if not specified

    node_id = str(uuid.uuid4())

    # Start a container that continuously sends heartbeats
    container = client.containers.run(
    "alpine",
    'sh -c "apk add --no-cache curl && while true; do curl -X POST  http://10.0.2.15:5000/heartbeat -H \\"Content-Type: application/json\\" -d \\"{\\\\\\"node_id\\\\\\": \\\\\\"%s\\\\\\"}\\\"; sleep 5; done"' % node_id,
    detach=True
)




    nodes[node_id] = {
        "id": node_id,
        "cpu_cores": cpu_cores,
        "available_cpu": cpu_cores,
        "pods": [],
        "container_id": container.id,
        "status": "running",
        "last_heartbeat": time.time() + HEARTBEAT_TIMEOUT 
    }

    return jsonify({"message": "Node added successfully", "node_id": node_id}), 201


@app.route('/list_nodes', methods=['GET'])
def list_nodes():
    return jsonify(nodes)


@app.route('/heartbeat', methods=['POST'])
def heartbeat():
    try:
        data = request.get_json()
        node_id = data.get('node_id')

        if not node_id or node_id not in nodes:
            return jsonify({"error": "Invalid node_id"}), 400

        # *Update last_heartbeat to prevent node removal*
        nodes[node_id]["last_heartbeat"] = time.time()

        return jsonify({"message": f"Heartbeat received for node {node_id}"}), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 400


# --- POD MANAGEMENT ---

def launch_pod(data, algo):
    cpu_request = data.get("cpu_request", 1)

    # Select algorithm based on the provided one
    if algo == "first_fit":
        node_id = first_fit(nodes, cpu_request)
    elif algo == "best_fit":
        node_id = best_fit(nodes, cpu_request)
    elif algo == "worst_fit":
        node_id = worst_fit(nodes, cpu_request)
    else:
        return jsonify({"error": "Invalid algorithm"}), 400

    if not node_id:
        return jsonify({"error": "No suitable node available"}), 400

    # Reserve resources
    nodes[node_id]["available_cpu"] -= cpu_request
    pod_id = str(uuid.uuid4())
    nodes[node_id]["pods"].append(pod_id)
    pods[pod_id] = {"node_id": node_id, "cpu_request": cpu_request}

    return jsonify({"message": "Pod launched", "pod_id": pod_id, "node_id": node_id}), 201


@app.route('/launch_pod', methods=['POST'])
def api_launch_pod():
    data = request.json
    algo = data.get("algorithm", "first_fit")  # Default to first_fit if no algorithm is provided
    return launch_pod(data, algo)


@app.route('/list_pods', methods=['GET'])
def list_pods():
    return jsonify(pods)


# --- FAILURE MONITORING ---

def monitor_heartbeats():
    """Thread that checks node heartbeats and removes dead nodes."""
    while True:
        time.sleep(HEARTBEAT_TIMEOUT)
        now = time.time()
        to_remove = []

        for node_id, node in nodes.items():
            if now - node["last_heartbeat"] > HEARTBEAT_TIMEOUT:
                print(f"Node {node_id} failed (no heartbeat)")
                to_remove.append(node_id)

        for node_id in to_remove:
            recover_pods(node_id)


def recover_pods(failed_node_id):
    if failed_node_id not in nodes:
        return
    
    print(f"Recovering pods from failed node {failed_node_id}...")
    failed_pods = nodes[failed_node_id]["pods"]
    del nodes[failed_node_id]
    
    rescheduled_pods = []
    unscheduled_pods = []
    for pod_id in failed_pods:
        pod_data = pods.pop(pod_id, None)
        if pod_data:
            cpu_request = pod_data["cpu_request"]
            new_node_id = first_fit(nodes, cpu_request)  # Attempt rescheduling
            if new_node_id:
                nodes[new_node_id]["available_cpu"] -= cpu_request
                nodes[new_node_id]["pods"].append(pod_id)
                pods[pod_id] = {"node_id": new_node_id, "cpu_request": cpu_request}
                rescheduled_pods.append(pod_id)
            else:
                unscheduled_pods.append(pod_id)
    
    print(f"Successfully rescheduled pods: {rescheduled_pods}")
    if unscheduled_pods:
        print(f"Failed to reschedule pods due to insufficient resources: {unscheduled_pods}")
threading.Thread(target=monitor_heartbeats, daemon=True).start()


if __name__ == '__main__':
    app.run(host="0.0.0.0", port=5000, debug=True)  # Bind to all interfaces