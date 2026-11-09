"""Load the IEEE and NCEII networks shipped with the repository."""

from __future__ import annotations

import importlib.util
from dataclasses import dataclass
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
LEGACY = ROOT / "legacy"


@dataclass
class Network:
    name: str
    n: int
    branches: list[tuple[int, int]]
    adj: list[np.ndarray]
    degrees: np.ndarray
    zibs: np.ndarray
    susceptance: dict[tuple[int, int], float]
    n_components: int

    def closed_neighborhood(self, i: int) -> np.ndarray:
        return np.concatenate(([i], self.adj[i]))


def _adjacency(n: int, branches: list[tuple[int, int]]) -> tuple[list[np.ndarray], np.ndarray]:
    buckets = [[] for _ in range(n)]
    for i, j in branches:
        buckets[i].append(j)
        buckets[j].append(i)
    adj = [np.array(sorted(set(nbrs)), dtype=int) for nbrs in buckets]
    degrees = np.array([len(a) for a in adj], dtype=int)
    return adj, degrees


def _components(n: int, adj: list[np.ndarray]) -> int:
    seen = np.zeros(n, dtype=bool)
    count = 0
    for start in range(n):
        if seen[start]:
            continue
        count += 1
        stack = [start]
        seen[start] = True
        while stack:
            u = stack.pop()
            for v in adj[u]:
                if not seen[v]:
                    seen[v] = True
                    stack.append(int(v))
    return count


def _susceptance(branches: list[tuple[int, int]]) -> dict[tuple[int, int], float]:
    """Distinct positive susceptances from branch order.

    The repository stores endpoints only. Distinct values keep the DC
    Jacobian at generic rank for nonzero line susceptances.
    """
    values = {}
    for k, (i, j) in enumerate(branches):
        a, b = (i, j) if i < j else (j, i)
        values[(a, b)] = 1.0 + (k + 1) * 1e-3
    return values


def _build(name: str, n: int, branches: list[tuple[int, int]], zibs: list[int]) -> Network:
    cleaned = []
    seen = set()
    for i, j in branches:
        i, j = int(i), int(j)
        if i == j:
            continue
        a, b = (i, j) if i < j else (j, i)
        if not (0 <= a < n and 0 <= b < n):
            raise ValueError(f"{name}: branch {(i, j)} outside 0..{n - 1}")
        if (a, b) in seen:
            continue
        seen.add((a, b))
        cleaned.append((a, b))
    zib_arr = np.array(sorted(set(int(z) for z in zibs)), dtype=int)
    if zib_arr.size and (zib_arr.min() < 0 or zib_arr.max() >= n):
        raise ValueError(f"{name}: zero-injection index outside the bus range")
    adj, degrees = _adjacency(n, cleaned)
    return Network(
        name=name,
        n=n,
        branches=cleaned,
        adj=adj,
        degrees=degrees,
        zibs=zib_arr,
        susceptance=_susceptance(cleaned),
        n_components=_components(n, adj),
    )


def _ieee_zero_injections(bus: np.ndarray, gen: np.ndarray) -> list[int]:
    """Zero-injection buses: no load and no generator.

    MATPOWER bus and generator numbers in these pickles are 1-based.
    Returned indices are 0-based, matching ``branchcase*.pickle``.
    """
    generators = {int(row[0]) for row in np.asarray(gen)}
    found = []
    for row in np.asarray(bus):
        number = int(row[0])
        if row[2] == 0 and row[3] == 0 and number not in generators:
            found.append(number - 1)
    return found


def load_ieee_case(bus_count: int, data_dir: Path = DATA) -> Network:
    import pickle

    with open(data_dir / f"branchcase{bus_count}.pickle", "rb") as handle:
        branch = np.asarray(pickle.load(handle))
    with open(data_dir / f"buscase{bus_count}.pickle", "rb") as handle:
        bus = np.asarray(pickle.load(handle))
    with open(data_dir / f"gencase{bus_count}.pickle", "rb") as handle:
        gen = np.asarray(pickle.load(handle))
    edges = [(int(row[0]), int(row[1])) for row in branch]
    zibs = _ieee_zero_injections(bus, gen)
    return _build(f"IEEE{bus_count}", bus_count, edges, zibs)


def _load_legacy_nceii():
    path = LEGACY / "getinfoNCEII.py"
    spec = importlib.util.spec_from_file_location("getinfoNCEII", path)
    if spec is None or spec.loader is None:
        raise FileNotFoundError(path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module.getinfoNCEII()


def load_nceii() -> Network:
    branch, zero_injections = _load_legacy_nceii()
    return _build("NCEII233", 233, list(branch), list(zero_injections))


def make_network(name: str, n: int, branches: list[tuple[int, int]], zibs: list[int] | None = None) -> Network:
    return _build(name, n, branches, [] if zibs is None else zibs)


def load_named(name: str) -> Network:
    key = name.upper()
    if key in {"IEEE14", "14"}:
        return load_ieee_case(14)
    if key in {"IEEE57", "57"}:
        return load_ieee_case(57)
    if key in {"IEEE118", "118"}:
        return load_ieee_case(118)
    if key in {"NCEII", "NCEII233", "233"}:
        return load_nceii()
    raise KeyError(name)


def load_all() -> list[Network]:
    return [load_ieee_case(14), load_ieee_case(57), load_ieee_case(118), load_nceii()]


def zib_clusters(net: Network) -> list[list[int]]:
    """Connected components of the subgraph induced by zero-injection buses."""
    zset = set(int(z) for z in net.zibs)
    seen: set[int] = set()
    clusters: list[list[int]] = []
    for start in net.zibs.tolist():
        start = int(start)
        if start in seen:
            continue
        stack = [start]
        seen.add(start)
        comp = []
        while stack:
            u = stack.pop()
            comp.append(u)
            for v in net.adj[u]:
                v = int(v)
                if v in zset and v not in seen:
                    seen.add(v)
                    stack.append(v)
        clusters.append(sorted(comp))
    clusters.sort(key=len, reverse=True)
    return clusters
