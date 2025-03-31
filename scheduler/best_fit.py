def best_fit(nodes, cpu_request):
    best_node = None
    min_remaining = float('inf')

    for node_id, node in nodes.items():
        remaining = node["available_cpu"] - cpu_request
        if remaining >= 0 and remaining < min_remaining:
            best_node = node_id
            min_remaining = remaining

    return best_node
