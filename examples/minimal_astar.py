"""Minimal A* demo on a small grid with one obstacle column."""
from gameai.core.astar import Manhattan, UniformCost, find_path

GRID = 6
WALL = {(3, y) for y in range(1, 5)}


def is_walkable(x, y):
    if not (0 <= x < GRID and 0 <= y < GRID):
        return False
    return (x, y) not in WALL


if __name__ == "__main__":
    path = find_path((0, 0), (5, 0), is_walkable, Manhattan(), UniformCost(), allow_diagonal=False)
    print(f"path length: {len(path)}")
    print(" -> ".join(f"({int(p.x)},{int(p.y)})" for p in path))
    assert all((int(p.x), int(p.y)) not in WALL for p in path)
