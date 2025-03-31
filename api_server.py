from flask import Flask, jsonify, request
import docker
import uuid

app = Flask(__name__)
client = docker.from_env()

nodes = {}  # Stores node details

@app.route('/add_node', methods=['POST'])
def add_node():
    data = request.json
    cpu_cores = data.get("cpu_cores", 2)    #default to 2 if no value

    #new container
    container = client.containers.run("CONT_NAME", "sh -c 'while true; do sleep 5; done'", detach=True)

    node_id = str(uuid.uuid4())
    nodes[node_id] = {
        "id": node_id,
        "cpu_cores": cpu_cores,
        "container_id": container.id,
        "status": "running"
    }

    return jsonify({"message": "Node added successfully", "node_id": node_id}), 201

@app.route('/list_nodes', methods=['GET'])
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

if __name__ == '__main__':
    app.run(debug=True) #running on port 5000
