def worst_fit(nodes, cpu_request):
    worst_node = None
    max_remaining = -1

    for node_id, node in nodes.items():
        remaining = node["available_cpu"] - cpu_request
        if remaining >= 0 and remaining > max_remaining:
            worst_node = node_id
            max_remaining = remaining

    return worst_node
