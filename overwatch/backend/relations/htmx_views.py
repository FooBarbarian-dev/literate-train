from django.shortcuts import render
from django.http import HttpResponse
from django.views.decorators.http import require_http_methods
from collections import defaultdict
from relations.models import Relation
from accounts.htmx_auth import htmx_login_required

@htmx_login_required
def relations_page(request):
    return render(request, 'relations/index.html')

@require_http_methods(["GET"])
@htmx_login_required
def relations_graph_htmx(request):
    relationship_type = request.GET.get('relationship_type', 'host')

    qs = Relation.objects.all()
    if relationship_type:
        qs = qs.filter(relationship_type=relationship_type)

    nodes_dict = {}
    edges = []
    connection_counts = defaultdict(int)

    for rel in qs.iterator():
        src_id = f"{rel.source_type}:{rel.source_value}"
        tgt_id = f"{rel.target_type}:{rel.target_value}"

        connection_counts[src_id] += 1
        connection_counts[tgt_id] += 1

        if src_id not in nodes_dict:
            nodes_dict[src_id] = {
                "id": src_id,
                "type": rel.source_type,
                "value": rel.source_value,
            }
        if tgt_id not in nodes_dict:
            nodes_dict[tgt_id] = {
                "id": tgt_id,
                "type": rel.target_type,
                "value": rel.target_value,
            }

        # Format peer display value here
        tgt_peer_display = tgt_id.split(':', 1)[1] if ':' in tgt_id else tgt_id
        src_peer_display = src_id.split(':', 1)[1] if ':' in src_id else src_id

        edges.append({
            "source": src_id,
            "target": tgt_id,
            "strength": rel.strength,
            "operation_tags": rel.operation_tags,
            "log_ids": rel.source_log_ids,
            "target_peer_display": tgt_peer_display,
            "source_peer_display": src_peer_display
        })

    # Convert nodes dict to list and add edge list to each node
    nodes = list(nodes_dict.values())
    for node in nodes:
        node["edge_count"] = connection_counts[node["id"]]
        node_edges = []
        for edge in edges:
            if edge["source"] == node["id"]:
                node_edges.append({**edge, "peer_display": edge["target_peer_display"]})
            elif edge["target"] == node["id"]:
                node_edges.append({**edge, "peer_display": edge["source_peer_display"]})
        node["edges"] = node_edges

    # Sort nodes by connections descending
    sorted_nodes = sorted(nodes, key=lambda n: n["edge_count"], reverse=True)

    return render(request, 'relations/partials/graph.html', {
        'nodes': nodes,
        'edges': edges,
        'sorted_nodes': sorted_nodes
    })
