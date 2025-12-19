from collections import deque
from .models import Connection,Station,LineStation
from collections import deque


def build_graph():
    graph = {}

    # Each Connection is undirected (A <-> B)
    for conn in Connection.objects.all():
        a = conn.a_id
        b = conn.b_id

        graph.setdefault(a, []).append(b)
        graph.setdefault(b, []).append(a)

    return graph


def shortest_distance(start_station, end_station):

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



def build_adjacency():
    graph = {}

    # Adjacent stations on each line
    for ls in LineStation.objects.order_by("line", "position"):
        st = ls.station
        graph.setdefault(st.id, set())

    # Same line adjacency
    for line_id in LineStation.objects.values_list("line_id", flat=True).distinct():
        ls = (
            LineStation.objects.filter(line_id=line_id)
            .order_by("position")
            .select_related("station")
        )

        for i in range(len(ls) - 1):
            a = ls[i].station.id
            b = ls[i + 1].station.id

            graph[a].add(b)
            graph[b].add(a)

    # Explicit Connection model
    for conn in Connection.objects.all():
        a = conn.a_id
        b = conn.b_id
        graph.setdefault(a, set()).add(b)
        graph.setdefault(b, set()).add(a)

    return graph


def shortest_path(start_station, end_station):

    graph = build_adjacency()

    start = start_station.id
    end = end_station.id

    queue = deque([[start]])
    visited = set([start])

    while queue:
        path = queue.popleft()
        node = path[-1]

        if node == end:
            # Convert IDs -> Station objects
            return [Station.objects.get(id=sid) for sid in path]

        for nbr in graph.get(node, []):
            if nbr not in visited:
                visited.add(nbr)
                new_path = path + [nbr]
                queue.append(new_path)

    raise Exception("No route found")

