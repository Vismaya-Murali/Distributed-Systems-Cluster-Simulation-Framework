from flask import jsonify
import uuid
import docker
from scheduler.first_fit import first_fit
from scheduler.best_fit import best_fit
from scheduler.worst_fit import worst_fit
from nodes import nodes

pods = {}  # { pod_id: { "node_id": str, "cpu_request": int } }

def launch_pod(data, algo):
    cpu_request = data.get("cpu_request", 1)
    
    # Select algorithm
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

def list_pods():
    return jsonify(pods)

# def recover_pods(data):
#     failed_node_id = data.get("node_id")
#     if failed_node_id not in nodes:
#         return jsonify({"error": "Node not found"}), 404

#     for pod_id in nodes[failed_node_id]["pods"]:
#         pods.pop(pod_id, None)

#     del nodes[failed_node_id]
#     return jsonify({"message": "Pods recovered"}), 200
