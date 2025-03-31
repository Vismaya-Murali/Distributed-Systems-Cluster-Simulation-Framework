from flask import jsonify
import uuid
import docker

client = docker.from_env()
nodes = {}  # Stores node details { node_id: { "cpu_cores": int, "available_cpu": int, "pods": [] } }

def add_node(data):
    cpu_cores = data.get("cpu_cores", 2)  # Default to 2
    container = client.containers.run("alpine", "sh -c 'while true; do sleep 5; done'", detach=True)
    
    node_id = str(uuid.uuid4())
    nodes[node_id] = {
        "id": node_id,
        "cpu_cores": cpu_cores,
        "available_cpu": cpu_cores,
        "pods": [],
        "container_id": container.id,
        "status": "running"
    }

    return jsonify({"message": "Node added successfully", "node_id": node_id}), 201

def list_nodes():
    # Filter out stopped nodes
    running_nodes = {}
    for node_id, node in list(nodes.items()):
        try:
            container = client.containers.get(node["container_id"])
            if container.status == "running":
                running_nodes[node_id] = node
            else:
                del nodes[node_id]  # Remove stopped node
        except docker.errors.NotFound:
            del nodes[node_id]  # Remove node if container is not found

    return jsonify(running_nodes)