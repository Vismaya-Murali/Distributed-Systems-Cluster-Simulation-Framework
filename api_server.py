from flask import Flask, jsonify, request
import uuid
from nodes import nodes, add_node, list_nodes
from pods import launch_pod, list_pods

app = Flask(__name__)

# API: Add Node
@app.route('/add_node', methods=['POST'])
def api_add_node():
    return add_node(request.json)

# API: Launch Pod (Select algorithm dynamically)
@app.route('/launch_pod', methods=['POST'])
def api_launch_pod():
    data = request.json
    algo = data.get("algorithm", "first_fit")  # Default is First Fit
    return launch_pod(data, algo)

# API: List Nodes
@app.route('/list_nodes', methods=['GET'])
def list_nodes():
    return nodes

# API: List Pods
@app.route('/list_pods', methods=['GET'])
def api_list_pods():
    return list_pods()

# # API: Recover Pods
# @app.route('/recover_pods', methods=['POST'])
# def api_recover_pods():
#     return recover_pods(request.json)

if __name__ == '__main__':
    app.run(debug=True)
