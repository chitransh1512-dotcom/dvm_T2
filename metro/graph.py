from collections import deque
from .models import Connection


def build_graph():
    """
    Returns an adjacency list:
    {
        station_id: [neighbor_station_id, ...],
        ...
    }
    """
    graph = {}

    # Each Connection is undirected (A <-> B)
    for conn in Connection.objects.all():
        a = conn.a_id
        b = conn.b_id

        graph.setdefault(a, []).append(b)
        graph.setdefault(b, []).append(a)

    return graph


def shortest_distance(start_station, end_station):
    """
    Returns the number of station hops between two stations using BFS.
    If no route is found, raises an Exception.
    """

    start = start_station.id
    end = end_station.id

    if start == end:
        return 0

    graph = build_graph()
    visited = set()
    queue = deque([(start, 0)])   # (station_id, distance)

    visited.add(start)

    while queue:
        station, dist = queue.popleft()

        for neighbor in graph.get(station, []):
            if neighbor == end:
                return dist + 1

            if neighbor not in visited:
                visited.add(neighbor)
                queue.append((neighbor, dist + 1))

    # No path found
    raise Exception("No route between stations")
