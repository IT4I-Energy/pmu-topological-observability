"""Placement algorithms.

Integer linear programming is exact for unlimited channels and for a
finite channel limit, both without zero-injection rules. With zero-injection
rules the same solver uses a depth-indexed linearization of the two
propagation rules and is run on the IEEE cases. The NCEII zero-injection
instance is left to the heuristics: its largest zero-injection cluster has
150 buses, and a depth-indexed model of that size is not a routine check.

GA, PSO, and SA search the binary placement vector. A feasible vector is
reduced by greedy deletion of redundant PMUs before it is kept. ILS uses
the same deletion neighborhood, a PageRank start, and a two-PMU restart.
"""

from __future__ import annotations

import time
from typing import Callable

import numpy as np
from scipy.optimize import Bounds, LinearConstraint, milp
from scipy.sparse import coo_matrix

from .network import Network
from .observability import fitness, is_observable, observe, observe_channels

# Documented defaults. Benchmarks call these values.
ILS_T = 20
ILS_M = 30
ILS_RESTART = 2
GA_POPULATION = 30
GA_GENERATIONS = 40
GA_CROSSOVER = 0.8
GA_ELITISM = 2
GA_TOURNAMENT = 3
PSO_PARTICLES = 30
PSO_ITERATIONS = 40
PSO_INERTIA = 0.7
PSO_COGNITIVE = 1.5
PSO_SOCIAL = 1.5
PSO_VMAX = 4.0
SA_T0 = 2.0
SA_COOLING = 0.95
SA_TMIN = 0.05
SA_MAX_EVALS = 4000
PAGERANK_DAMPING = 0.85
PAGERANK_ITERS = 60


def parameters() -> dict:
    return {
        "ils": {
            "T_local_steps": ILS_T,
            "M_outer_iterations": ILS_M,
            "restart_pmus": ILS_RESTART,
            "perturbation": "Move one PMU onto an adjacent candidate bus. Accept the move only when the network stays observable.",
            "neighborhood": "Delete every PMU that is redundant under the active observability rules.",
            "stopping": "Stop after M outer iterations. There is no optimality gap test.",
        },
        "ga": {
            "population": GA_POPULATION,
            "generations": GA_GENERATIONS,
            "crossover": f"uniform, probability {GA_CROSSOVER}",
            "mutation": "independent bit flip with probability 1/N",
            "selection": f"tournament of {GA_TOURNAMENT}",
            "elitism": GA_ELITISM,
            "repair": "greedy deletion of redundant PMUs on every feasible individual",
            "stopping": "Stop after the generation count.",
        },
        "pso": {
            "particles": PSO_PARTICLES,
            "iterations": PSO_ITERATIONS,
            "inertia": PSO_INERTIA,
            "cognitive": PSO_COGNITIVE,
            "social": PSO_SOCIAL,
            "velocity_clamp": [-PSO_VMAX, PSO_VMAX],
            "transfer": "sigmoid",
            "repair": "greedy deletion of redundant PMUs on every feasible particle",
            "stopping": "Stop after the iteration count.",
        },
        "sa": {
            "T0": SA_T0,
            "cooling": SA_COOLING,
            "Tmin": SA_TMIN,
            "trials_per_temperature": "N",
            "max_evaluations": SA_MAX_EVALS,
            "neighbor": "flip one bus",
            "acceptance": "Metropolis",
            "repair": "greedy deletion after an accepted feasible move",
            "stopping": "Stop at Tmin or at the evaluation cap, whichever comes first.",
        },
        "pagerank": {"damping": PAGERANK_DAMPING, "power_iterations": PAGERANK_ITERS},
        "channel_assignment": (
            "Visit PMU buses by descending degree and then by ascending index. "
            "Spend each current channel on the lowest-index neighbor that is still unobserved."
        ),
        "seeds": [0, 1],
    }


def pagerank(net: Network) -> np.ndarray:
    n = net.n
    degree = net.degrees.astype(float)
    rank = np.full(n, 1.0 / n)
    for _ in range(PAGERANK_ITERS):
        updated = np.full(n, (1.0 - PAGERANK_DAMPING) / n)
        for i in range(n):
            if degree[i] == 0:
                updated += PAGERANK_DAMPING * rank[i] / n
            else:
                share = PAGERANK_DAMPING * rank[i] / degree[i]
                updated[net.adj[i]] += share
        rank = updated
    return rank


def prune(
    net: Network,
    placement: np.ndarray,
    channel_limit: int | None,
    use_zib: bool,
) -> np.ndarray:
    placement = np.array(placement, dtype=int, copy=True)
    changed = True
    while changed:
        changed = False
        for i in np.flatnonzero(placement):
            placement[i] = 0
            if is_observable(net, placement, channel_limit, use_zib):
                changed = True
            else:
                placement[i] = 1
    return placement


def ppa(
    net: Network,
    channel_limit: int | None = None,
    use_zib: bool = False,
) -> np.ndarray:
    """PageRank placement: cover every leaf, then the highest-rank unobserved bus."""
    placement = np.zeros(net.n, dtype=int)
    for i in range(net.n):
        if net.degrees[i] == 1:
            placement[int(net.adj[i][0])] = 1
    order = np.argsort(-pagerank(net), kind="mergesort")
    for _ in range(net.n + 1):
        if is_observable(net, placement, channel_limit, use_zib):
            break
        mask, _channels = observe(net, placement, channel_limit, use_zib)
        placed = False
        for i in order:
            i = int(i)
            if placement[i] == 0 and not mask[i]:
                placement[i] = 1
                placed = True
                break
        if not placed:
            missing = np.flatnonzero(~mask & (placement == 0))
            if missing.size == 0:
                break
            placement[int(missing[0])] = 1
    return placement


def degree_greedy(
    net: Network,
    channel_limit: int | None = None,
    use_zib: bool = False,
) -> np.ndarray:
    placement = np.zeros(net.n, dtype=int)
    for _ in range(net.n):
        if is_observable(net, placement, channel_limit, use_zib):
            break
        mask, _channels = observe(net, placement, channel_limit, use_zib)
        best_i = 0
        best_key = (-1, -1, -net.n)
        for i in range(net.n):
            if placement[i]:
                continue
            cover = 0 if mask[i] else 1
            for j in net.adj[i]:
                if not mask[int(j)]:
                    cover += 1
            key = (cover, int(net.degrees[i]), -i)
            if key > best_key:
                best_key = key
                best_i = i
        placement[best_i] = 1
    return prune(net, placement, channel_limit, use_zib)


def random_start(
    net: Network,
    rng: np.random.Generator,
    channel_limit: int | None,
    use_zib: bool,
) -> np.ndarray:
    placement = np.zeros(net.n, dtype=int)
    for i in rng.permutation(net.n):
        placement[int(i)] = 1
        if is_observable(net, placement, channel_limit, use_zib):
            break
    return prune(net, placement, channel_limit, use_zib)


def _polish(net, placement, channel_limit, use_zib) -> np.ndarray:
    placement = np.array(placement, dtype=int, copy=True)
    if is_observable(net, placement, channel_limit, use_zib):
        return prune(net, placement, channel_limit, use_zib)
    return placement


def _empty_history(count: int) -> list:
    return [None] * count


def _best_count(placement, channel_limit, use_zib, net) -> int | None:
    if is_observable(net, placement, channel_limit, use_zib):
        return int(np.sum(placement))
    return None


def iterated_local_search(
    net: Network,
    rng: np.random.Generator,
    channel_limit: int | None = None,
    use_zib: bool = False,
    local_steps: int = ILS_T,
    outer: int = ILS_M,
    start: np.ndarray | None = None,
) -> tuple[np.ndarray, list]:
    if start is None:
        current = ppa(net, channel_limit, use_zib)
    else:
        current = np.array(start, dtype=int, copy=True)
    current = prune(net, current, channel_limit, use_zib)
    best = current.copy()
    history = [int(best.sum())]
    for _outer in range(outer):
        for _step in range(local_steps):
            moved = _perturb(net, current, rng, channel_limit, use_zib)
            if moved is None:
                continue
            current = prune(net, moved, channel_limit, use_zib)
            if int(current.sum()) < int(best.sum()) and is_observable(
                net, current, channel_limit, use_zib
            ):
                best = current.copy()
        history.append(int(best.sum()))
        current = _add_random(net, current, ILS_RESTART, rng)
    if not is_observable(net, best, channel_limit, use_zib):
        best = current
    return best, history


def _perturb(net, placement, rng, channel_limit, use_zib):
    pmus = np.flatnonzero(placement)
    if pmus.size == 0:
        return None
    candidates = [i for i in range(net.n) if placement[i] == 0 and net.degrees[i] != 1]
    if not candidates:
        candidates = [i for i in range(net.n) if placement[i] == 0]
    if not candidates:
        return None
    pmu_set = set(int(p) for p in pmus)
    for _try in range(40):
        destination = int(candidates[int(rng.integers(0, len(candidates)))])
        adjacent = [p for p in pmu_set if p in set(int(j) for j in net.adj[destination])]
        if not adjacent:
            continue
        source = int(adjacent[int(rng.integers(0, len(adjacent)))])
        trial = placement.copy()
        trial[source] = 0
        trial[destination] = 1
        if is_observable(net, trial, channel_limit, use_zib):
            return trial
    return None


def _add_random(net, placement, count, rng):
    placement = placement.copy()
    candidates = [i for i in range(net.n) if placement[i] == 0 and net.degrees[i] != 1]
    if len(candidates) < count:
        candidates = [i for i in range(net.n) if placement[i] == 0]
    if not candidates:
        return placement
    take = min(count, len(candidates))
    chosen = rng.choice(np.array(candidates), size=take, replace=False)
    placement[np.asarray(chosen, dtype=int)] = 1
    return placement


def genetic_algorithm(
    net: Network,
    rng: np.random.Generator,
    channel_limit: int | None = None,
    use_zib: bool = False,
    population_size: int = GA_POPULATION,
    generations: int = GA_GENERATIONS,
) -> tuple[np.ndarray, list]:
    seed = prune(net, ppa(net, channel_limit, use_zib), channel_limit, use_zib)
    density = min(0.5, max(float(seed.sum()) / net.n, 2.0 / net.n))
    population = [seed]
    while len(population) < population_size:
        draw = (rng.random(net.n) < density).astype(int)
        if int(draw.sum()) == 0:
            draw[int(rng.integers(0, net.n))] = 1
        population.append(draw)
    history = []
    best = seed.copy()
    for _gen in range(generations):
        polished = [_polish(net, individual, channel_limit, use_zib) for individual in population]
        scores = np.array(
            [fitness(net, individual, channel_limit, use_zib) for individual in polished]
        )
        order = np.argsort(scores, kind="mergesort")
        polished = [polished[int(i)] for i in order]
        scores = scores[order]
        if scores[0] <= net.n and int(polished[0].sum()) <= int(best.sum()):
            if is_observable(net, polished[0], channel_limit, use_zib):
                best = polished[0].copy()
        history.append(_best_count(best, channel_limit, use_zib, net))
        next_population = [individual.copy() for individual in polished[:GA_ELITISM]]
        while len(next_population) < population_size:
            first = polished[int(_tournament(scores, rng))]
            second = polished[int(_tournament(scores, rng))]
            child = first.copy()
            if rng.random() < GA_CROSSOVER:
                mask = rng.random(net.n) < 0.5
                child = np.where(mask, first, second).astype(int)
            flips = rng.random(net.n) < (1.0 / net.n)
            child[flips] = 1 - child[flips]
            next_population.append(child)
        population = next_population
    final = _polish(net, best, channel_limit, use_zib)
    if is_observable(net, final, channel_limit, use_zib) and (
        not is_observable(net, best, channel_limit, use_zib) or int(final.sum()) <= int(best.sum())
    ):
        best = final
    return best, history


def _tournament(scores: np.ndarray, rng: np.random.Generator) -> int:
    picks = rng.integers(0, len(scores), size=GA_TOURNAMENT)
    return int(picks[np.argmin(scores[picks])])


def particle_swarm(
    net: Network,
    rng: np.random.Generator,
    channel_limit: int | None = None,
    use_zib: bool = False,
    particles: int = PSO_PARTICLES,
    iterations: int = PSO_ITERATIONS,
) -> tuple[np.ndarray, list]:
    seed = prune(net, ppa(net, channel_limit, use_zib), channel_limit, use_zib)
    density = min(0.5, max(float(seed.sum()) / net.n, 2.0 / net.n))
    position = np.zeros((particles, net.n), dtype=int)
    position[0] = seed
    for p in range(1, particles):
        position[p] = (rng.random(net.n) < density).astype(int)
    position = np.vstack([_polish(net, row, channel_limit, use_zib) for row in position])
    velocity = rng.uniform(-1.0, 1.0, size=position.shape)
    personal = position.copy()
    personal_score = np.array(
        [fitness(net, row, channel_limit, use_zib) for row in personal]
    )
    global_index = int(np.argmin(personal_score))
    global_best = personal[global_index].copy()
    history = [_best_count(global_best, channel_limit, use_zib, net)]
    for _it in range(iterations):
        r1 = rng.random(position.shape)
        r2 = rng.random(position.shape)
        velocity = (
            PSO_INERTIA * velocity
            + PSO_COGNITIVE * r1 * (personal - position)
            + PSO_SOCIAL * r2 * (global_best - position)
        )
        np.clip(velocity, -PSO_VMAX, PSO_VMAX, out=velocity)
        probability = 1.0 / (1.0 + np.exp(-velocity))
        position = (rng.random(position.shape) < probability).astype(int)
        for p in range(particles):
            position[p] = _polish(net, position[p], channel_limit, use_zib)
            score = fitness(net, position[p], channel_limit, use_zib)
            if score < personal_score[p]:
                personal[p] = position[p]
                personal_score[p] = score
                if score < fitness(net, global_best, channel_limit, use_zib):
                    global_best = position[p].copy()
        history.append(_best_count(global_best, channel_limit, use_zib, net))
    return global_best, history


def simulated_annealing(
    net: Network,
    rng: np.random.Generator,
    channel_limit: int | None = None,
    use_zib: bool = False,
    t0: float = SA_T0,
    cooling: float = SA_COOLING,
    tmin: float = SA_TMIN,
    max_evals: int = SA_MAX_EVALS,
) -> tuple[np.ndarray, list]:
    current = prune(net, ppa(net, channel_limit, use_zib), channel_limit, use_zib)
    current_score = fitness(net, current, channel_limit, use_zib)
    best = current.copy()
    temperature = t0
    evaluations = 0
    history = [_best_count(best, channel_limit, use_zib, net)]
    while temperature > tmin and evaluations < max_evals:
        for _trial in range(net.n):
            if evaluations >= max_evals:
                break
            trial = current.copy()
            bit = int(rng.integers(0, net.n))
            trial[bit] = 1 - trial[bit]
            trial = _polish(net, trial, channel_limit, use_zib)
            trial_score = fitness(net, trial, channel_limit, use_zib)
            evaluations += 1
            delta = trial_score - current_score
            if delta <= 0 or rng.random() < np.exp(-delta / temperature):
                current = trial
                current_score = trial_score
                if trial_score < fitness(net, best, channel_limit, use_zib):
                    best = trial.copy()
        history.append(_best_count(best, channel_limit, use_zib, net))
        temperature *= cooling
    return best, history


def _milp_placement(c, constraint, integrality, time_limit: float):
    result = milp(
        c=c,
        integrality=integrality,
        bounds=Bounds(np.zeros(c.size), np.ones(c.size)),
        constraints=constraint,
        options={"time_limit": float(time_limit), "disp": False},
    )
    if result.x is None:
        return None, False, str(result.message)
    placement_ok = True
    return result, placement_ok, str(result.message)


def solve_domination(net: Network, time_limit: float = 60.0) -> tuple[np.ndarray | None, str]:
    n = net.n
    rows, cols, data = [], [], []
    for i in range(n):
        rows.append(i)
        cols.append(i)
        data.append(1.0)
        for j in net.adj[i]:
            rows.append(i)
            cols.append(int(j))
            data.append(1.0)
    matrix = coo_matrix((data, (rows, cols)), shape=(n, n)).tocsr()
    constraint = LinearConstraint(matrix, np.ones(n), np.full(n, np.inf))
    result, _flag, message = _milp_placement(np.ones(n), constraint, np.ones(n), time_limit)
    if result is None or result.x is None:
        return None, f"failed: {message}"
    placement = (result.x[:n] > 0.5).astype(int)
    status = "optimal" if result.success else "feasible_or_timeout"
    if not is_observable(net, placement, None, False):
        return placement, "solver_solution_not_observable"
    return placement, status if result.success else message


def solve_channels(net: Network, limit: int, time_limit: float = 120.0) -> tuple[np.ndarray | None, str, list]:
    n = net.n
    arcs = []
    for i, j in net.branches:
        arcs.append((i, j))
        arcs.append((j, i))
    n_var = n + len(arcs)
    # row builder
    rows, cols, data = [], [], []
    lower, upper = [], []

    def add(terms: list[tuple[int, float]], low: float, high: float) -> None:
        r = len(lower)
        for c, v in terms:
            rows.append(r)
            cols.append(c)
            data.append(v)
        lower.append(low)
        upper.append(high)

    for k, (src, dst) in enumerate(arcs):
        add([(n + k, 1.0), (src, -1.0)], -np.inf, 0.0)
    for i in range(n):
        terms = [(n + k, 1.0) for k, (src, _dst) in enumerate(arcs) if src == i]
        if terms:
            add(terms, -np.inf, float(limit))
    for bus in range(n):
        terms = [(bus, 1.0)]
        for k, (_src, dst) in enumerate(arcs):
            if dst == bus:
                terms.append((n + k, 1.0))
        add(terms, 1.0, np.inf)
    matrix = coo_matrix((data, (rows, cols)), shape=(len(lower), n_var)).tocsr()
    constraint = LinearConstraint(matrix, np.array(lower), np.array(upper))
    cost = np.zeros(n_var)
    cost[:n] = 1.0
    cost[n:] = 1e-4
    result, _flag, message = _milp_placement(cost, constraint, np.ones(n_var), time_limit)
    if result is None or result.x is None:
        return None, f"failed: {message}", []
    placement = (result.x[:n] > 0.5).astype(int)
    channels = [
        (int(src), int(dst))
        for k, (src, dst) in enumerate(arcs)
        if result.x[n + k] > 0.5
    ]
    observed = observe_channels(net, placement, channels, False)
    if not bool(observed.all()):
        return placement, "solver_solution_not_observable", channels
    status = "optimal" if result.success else message
    return placement, status, channels


def solve_zero_injection(
    net: Network,
    time_limit: float = 180.0,
    depth: int | None = None,
) -> tuple[np.ndarray | None, str]:
    """Depth-indexed linearization of the two topological rules.

    Each pass of the rules observes at least one new bus, so depth ``N`` is
    sufficient. On the IEEE networks the inference chains are short, and a
    depth of 12 already contains every chain used by the checker on those
    graphs. The returned placement is accepted only when the topological
    checker agrees. A HiGHS "optimal" status is a certificate for this depth.
    """
    n = net.n
    depth = n if depth is None else int(depth)
    if depth < 1 or depth > n:
        raise ValueError(f"depth must lie in 1..{n}")
    zibs = [int(z) for z in net.zibs if net.degrees[int(z)] > 0]

    def y_at(t: int, i: int) -> int:
        return n + t * n + i

    a_index: dict[tuple[int, int], int] = {}
    cursor = n + (depth + 1) * n
    for t in range(1, depth + 1):
        for z in zibs:
            a_index[(t, z)] = cursor
            cursor += 1
    b_index: dict[tuple[int, int, int], int] = {}
    neighbors_of = {z: [int(j) for j in net.adj[z]] for z in zibs}
    incoming: dict[int, list[tuple[int, int]]] = {i: [] for i in range(n)}
    for z, neighbors in neighbors_of.items():
        for i in neighbors:
            for t in range(1, depth + 1):
                b_index[(t, z, i)] = cursor
                cursor += 1
            incoming[i].append((z, i))
    n_var = cursor
    rows, cols, data = [], [], []
    lower, upper = [], []

    def add(terms: list[tuple[int, float]], low: float, high: float) -> None:
        r = len(lower)
        for c, v in terms:
            rows.append(r)
            cols.append(c)
            data.append(float(v))
        lower.append(low)
        upper.append(high)

    for i in range(n):
        terms = [(y_at(0, i), 1.0), (i, -1.0)]
        for j in net.adj[i]:
            terms.append((int(j), -1.0))
        add(terms, -np.inf, 0.0)
    for t in range(1, depth + 1):
        for i in range(n):
            terms = [(y_at(t, i), 1.0), (y_at(t - 1, i), -1.0)]
            if (t, i) in a_index:
                terms.append((a_index[(t, i)], -1.0))
            for z, _i in incoming[i]:
                terms.append((b_index[(t, z, i)], -1.0))
            add(terms, -np.inf, 0.0)
        for z, neighbors in neighbors_of.items():
            for j in neighbors:
                add([(a_index[(t, z)], 1.0), (y_at(t - 1, j), -1.0)], -np.inf, 0.0)
            for i in neighbors:
                add([(b_index[(t, z, i)], 1.0), (y_at(t - 1, z), -1.0)], -np.inf, 0.0)
                for k in neighbors:
                    if k == i:
                        continue
                    add(
                        [(b_index[(t, z, i)], 1.0), (y_at(t - 1, k), -1.0)],
                        -np.inf,
                        0.0,
                    )
    for i in range(n):
        add([(y_at(depth, i), 1.0)], 1.0, np.inf)
    matrix = coo_matrix((data, (rows, cols)), shape=(len(lower), n_var)).tocsr()
    constraint = LinearConstraint(matrix, np.array(lower, dtype=float), np.array(upper, dtype=float))
    cost = np.zeros(n_var)
    cost[:n] = 1.0
    result, _flag, message = _milp_placement(cost, constraint, np.ones(n_var), time_limit)
    if result is None or result.x is None:
        return None, f"failed: {message}"
    placement = (result.x[:n] > 0.5).astype(int)
    if not is_observable(net, placement, None, True):
        return placement, "solver_solution_not_observable"
    return placement, "optimal" if result.success else message


def run_timed(fn: Callable, *args, **kwargs):
    started = time.perf_counter()
    value = fn(*args, **kwargs)
    return value, time.perf_counter() - started
