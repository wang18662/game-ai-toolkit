from gameai.core.astar import Manhattan, Octile, UniformCost, find_path
from gameai.core.vector import Vector2


def _grid(blocked):
    def is_walkable(x, y):
        if x < 0 or y < 0 or x >= 5 or y >= 5:
            return False
        return (x, y) not in blocked

    return is_walkable


def test_straight_line():
    g = _grid(set())
    path = find_path((0, 0), (4, 0), g, Manhattan(), UniformCost(), allow_diagonal=False)
    assert len(path) == 5
    assert path[0] == Vector2(0, 0)
    assert path[-1] == Vector2(4, 0)


def test_detour_around_obstacle():
    blocked = {(2, 0), (2, 1), (2, 2), (2, 3)}  # leaves (2,4) open as a gap
    g = _grid(blocked)
    path = find_path((0, 0), (4, 0), g, Manhattan(), UniformCost(), allow_diagonal=False)
    assert path
    assert all((int(p.x), int(p.y)) not in blocked for p in path)
    assert path[-1] == Vector2(4, 0)


def test_unreachable_returns_empty():
    blocked = {(x, 2) for x in range(5)}  # full wall splits map
    g = _grid(blocked)
    path = find_path((0, 0), (0, 4), g, Manhattan(), UniformCost(), allow_diagonal=False)
    assert path == []


def test_diagonal_shortens_path():
    g = _grid(set())
    path = find_path((0, 0), (3, 3), g, Octile(), UniformCost(), allow_diagonal=True)
    assert len(path) == 4  # 3 diagonal steps
    assert path[-1] == Vector2(3, 3)


def test_astar_matches_bfs_optimal_length():
    import collections

    blocked = {(1, 1), (2, 1), (1, 2), (3, 3), (0, 4)}
    g = _grid(blocked)
    start, goal = (0, 0), (4, 4)
    path = find_path(start, goal, g, Manhattan(), UniformCost(), allow_diagonal=False)

    # Reference shortest path via BFS on the same grid.
    q = collections.deque([start])
    dist = {start: 0}
    while q:
        cur = q.popleft()
        if cur == goal:
            break
        for dx, dy in [(1, 0), (-1, 0), (0, 1), (0, -1)]:
            nxt = (cur[0] + dx, cur[1] + dy)
            if g(*nxt) and nxt not in dist:
                dist[nxt] = dist[cur] + 1
                q.append(nxt)

    assert len(path) - 1 == dist[goal]  # A* steps == BFS optimal distance
