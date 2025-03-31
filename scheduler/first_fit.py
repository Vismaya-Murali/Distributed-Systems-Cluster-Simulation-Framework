def first_fit(nodes, cpu_request):
    for node_id, node in nodes.items():
        if node["available_cpu"] >= cpu_request:
            return node_id
    return None  # No suitable node found
