"""Two-seed benchmark for the bundled networks.

Run from the repository root:

    python -m pmu_tool.benchmarks
"""

from __future__ import annotations

import json
import platform
import time
from importlib.metadata import version
from pathlib import Path

import numpy as np
import yaml

from .algorithms import (
    ILS_M,
    ILS_T,
    degree_greedy,
    genetic_algorithm,
    iterated_local_search,
    pagerank,
    parameters,
    particle_swarm,
    ppa,
    prune,
    random_start,
    run_timed,
    simulated_annealing,
    solve_channels,
    solve_domination,
    solve_zero_injection,
)
from .figures import draw_network, write_manifest
from .jacobian import measurement_jacobian
from .network import ROOT, load_all, zib_clusters
from .observability import is_observable, observe

SEEDS = (0, 1)
ZIB_ILP_DEPTH = 12
OUT = ROOT / "benchmarks"


def collect_environment() -> dict:
    mem_kb = None
    cpu = None
    try:
        for line in Path("/proc/meminfo").read_text().splitlines():
            if line.startswith("MemTotal"):
                mem_kb = int(line.split()[1])
        for line in Path("/proc/cpuinfo").read_text().splitlines():
            if line.lower().startswith("model name"):
                cpu = line.split(":", 1)[1].strip()
                break
    except OSError:
        pass
    packages = {}
    for name in ("numpy", "scipy", "pyyaml", "matplotlib", "networkx", "pandas"):
        packages[name] = version(name)
    return {
        "python": platform.python_version(),
        "platform": platform.platform(),
        "processor": cpu or platform.processor(),
        "machine": platform.machine(),
        "ram_gib": None if mem_kb is None else round(mem_kb / 1024 / 1024, 2),
        "conda_env": "PMU_env",
        "packages": packages,
    }


def _record(method, seed, placement, seconds, history, status, net, limit, use_zib, optimal):
    if placement is None:
        return {
            "method": method,
            "seed": seed,
            "status": status,
            "time_s": round(seconds, 6),
            "optimal_certificate": False,
            "observable": False,
            "n_pmu": None,
            "unobserved": None,
            "buses_0based": [],
            "buses_1based": [],
            "history": history or [],
        }
    mask, channels = observe(net, placement, limit, use_zib)
    buses = [int(i) for i in np.flatnonzero(placement)]
    channel_pairs = None if channels is None else [[int(a), int(b)] for a, b in channels]
    return {
        "method": method,
        "seed": seed,
        "status": status,
        "time_s": round(float(seconds), 6),
        "optimal_certificate": bool(optimal),
        "observable": bool(mask.all()),
        "n_pmu": len(buses),
        "unobserved": int((~mask).sum()),
        "buses_0based": buses,
        "buses_1based": [i + 1 for i in buses],
        "channels_0based": channel_pairs,
        "history": [None if value is None else int(value) for value in (history or [])],
    }


def _network_facts(net) -> dict:
    clusters = zib_clusters(net)
    return {
        "name": net.name,
        "buses": net.n,
        "branches": len(net.branches),
        "components": net.n_components,
        "zero_injections": int(net.zibs.size),
        "zero_injections_1based": [int(z) + 1 for z in net.zibs],
        "zero_injection_cluster_sizes": [len(c) for c in clusters],
        "largest_zero_injection_cluster": 0 if not clusters else len(clusters[0]),
    }


def _solve_exact(net, scenario, limit, use_zib):
    if use_zib:
        if net.name == "NCEII233":
            return None, 0.0, (
                "not_run: the largest zero-injection cluster has 150 buses; "
                "the depth-indexed ILP is reported for the IEEE cases only"
            ), False, None
        (placement, status), seconds = run_timed(
            solve_zero_injection, net, time_limit=90, depth=ZIB_ILP_DEPTH
        )
        proven = status == "optimal"
        return placement, seconds, status, proven, None
    if limit is None:
        (placement, status), seconds = run_timed(solve_domination, net, 60)
        return placement, seconds, status, status == "optimal", None
    (placement, status, channels), seconds = run_timed(solve_channels, net, limit, 120)
    return placement, seconds, status, status == "optimal", channels


def _heuristic(name, net, rng, limit, use_zib):
    if name == "ILS":
        return iterated_local_search(net, rng, limit, use_zib)
    if name == "GA":
        return genetic_algorithm(net, rng, limit, use_zib)
    if name == "PSO":
        return particle_swarm(net, rng, limit, use_zib)
    if name == "SA":
        return simulated_annealing(net, rng, limit, use_zib)
    raise KeyError(name)


def _median_call(fn, repeats: int = 30, inner: int = 20) -> float:
    fn()
    samples = []
    for _ in range(repeats):
        started = time.perf_counter()
        for _inner in range(inner):
            fn()
        samples.append((time.perf_counter() - started) / inner)
    return float(np.median(samples))


def _jacobian_block(net, placement, limit, use_zib) -> dict:
    def topo():
        observe(net, placement, limit, use_zib)

    def numeric():
        measurement_jacobian(net, placement, limit, use_zib)

    topo_mask, _channels = observe(net, placement, limit, use_zib)
    numeric_result = measurement_jacobian(net, placement, limit, use_zib)
    return {
        "topological_observed": int(topo_mask.sum()),
        "topological_full": bool(topo_mask.all()),
        "jacobian_rank": int(numeric_result["rank"]),
        "jacobian_target": int(numeric_result["target_rank"]),
        "jacobian_full": bool(numeric_result["full_rank"]),
        "jacobian_observed": int(numeric_result["observed_buses"]),
        "agree_full": bool(topo_mask.all()) == bool(numeric_result["full_rank"]),
        "median_topological_s": _median_call(topo),
        "median_jacobian_s": _median_call(numeric, repeats=10, inner=5),
    }


def run() -> dict:
    OUT.mkdir(parents=True, exist_ok=True)
    networks = load_all()
    scenarios = [
        ("unlimited", None, False),
        ("zero_injection", None, True),
        ("channels_1", 1, False),
        ("channels_2", 2, False),
        ("channels_3", 3, False),
    ]
    summary = {
        "environment": collect_environment(),
        "parameters": parameters(),
        "zero_injection_ilp_depth": ZIB_ILP_DEPTH,
        "seeds": list(SEEDS),
        "networks": [_network_facts(net) for net in networks],
        "runs": [],
        "initialization": [],
        "jacobian": [],
    }
    best_draw = {}
    for net in networks:
        for scenario, limit, use_zib in scenarios:
            print(f"{net.name} {scenario} exact", flush=True)
            placement, seconds, status, proven, exact_channels = _solve_exact(net, scenario, limit, use_zib)
            record = _record("ILP", None, placement, seconds, [], status, net, limit, use_zib, proven)
            if exact_channels is not None and placement is not None:
                from .observability import observe_channels

                record["channels_0based"] = [[int(a), int(b)] for a, b in exact_channels]
                covered = observe_channels(net, placement, exact_channels, False)
                record["observable"] = bool(covered.all())
                record["unobserved"] = int((~covered).sum())
            record.update({"network": net.name, "scenario": scenario, "channel_limit": limit, "use_zib": use_zib})
            summary["runs"].append(record)
            if placement is not None and record["observable"]:
                best_draw[(net.name, scenario)] = placement
            print(f"  ILP pmu={record['n_pmu']} status={status} {seconds:.2f}s", flush=True)

            started = time.perf_counter()
            ppa_placement = ppa(net, limit, use_zib)
            ppa_record = _record(
                "PPA",
                None,
                ppa_placement,
                time.perf_counter() - started,
                [],
                "deterministic",
                net,
                limit,
                use_zib,
                False,
            )
            ppa_record.update({"network": net.name, "scenario": scenario, "channel_limit": limit, "use_zib": use_zib})
            summary["runs"].append(ppa_record)
            print(f"  PPA pmu={ppa_record['n_pmu']} obs={ppa_record['observable']}", flush=True)

            for seed in SEEDS:
                for method in ("ILS", "GA", "PSO", "SA"):
                    print(f"  {method} seed {seed}", flush=True)
                    rng = np.random.default_rng(seed)
                    (found, history), seconds = run_timed(_heuristic, method, net, rng, limit, use_zib)
                    row = _record(method, seed, found, seconds, history, "completed", net, limit, use_zib, False)
                    row.update({"network": net.name, "scenario": scenario, "channel_limit": limit, "use_zib": use_zib})
                    summary["runs"].append(row)
                    print(
                        f"    pmu={row['n_pmu']} obs={row['observable']} unobs={row['unobserved']} {seconds:.2f}s",
                        flush=True,
                    )
                    key = (net.name, scenario)
                    if row["observable"] and (
                        key not in best_draw or row["n_pmu"] < int(np.sum(best_draw[key]))
                    ):
                        best_draw[key] = found.copy()

        print(f"{net.name} initialization", flush=True)
        for seed in SEEDS:
            for init_name, builder in (
                ("pagerank", lambda rng: ppa(net, None, False)),
                ("degree", lambda rng: degree_greedy(net, None, False)),
                ("random", lambda rng: random_start(net, rng, None, False)),
            ):
                rng = np.random.default_rng(seed)
                initial = prune(net, builder(rng), None, False)
                initial_count = int(np.sum(initial))
                (found, _history), seconds = run_timed(
                    iterated_local_search,
                    net,
                    rng,
                    None,
                    False,
                    ILS_T,
                    ILS_M,
                    initial,
                )
                summary["initialization"].append(
                    {
                        "network": net.name,
                        "seed": seed,
                        "initialization": init_name,
                        "initial_pmus": initial_count,
                        "final_pmus": int(np.sum(found)),
                        "observable": is_observable(net, found, None, False),
                        "time_s": round(seconds, 6),
                    }
                )
                print(
                    f"  {init_name} seed {seed}: {initial_count} -> {int(np.sum(found))} in {seconds:.2f}s",
                    flush=True,
                )

        reference = best_draw.get((net.name, "unlimited"))
        if reference is None:
            reference = ppa(net, None, False)
        zib_reference = best_draw.get((net.name, "zero_injection"))
        print(f"{net.name} jacobian", flush=True)
        for label, placement, limit, use_zib in (
            ("unlimited_best", reference, None, False),
            ("zero_injection_best", zib_reference, None, True),
        ):
            if placement is None:
                continue
            block = _jacobian_block(net, placement, limit, use_zib)
            block.update({"network": net.name, "placement": label, "n_pmu": int(np.sum(placement))})
            summary["jacobian"].append(block)
            print(
                f"  {label}: topo {block['topological_observed']} jac {block['jacobian_observed']} "
                f"times {block['median_topological_s']:.6f}s vs {block['median_jacobian_s']:.6f}s",
                flush=True,
            )

    figures = []
    for net in networks:
        if net.name not in {"IEEE118", "NCEII233"}:
            continue
        for scenario, limit, use_zib, stem in (
            ("unlimited", None, False, f"{net.name}_unlimited"),
            ("zero_injection", None, True, f"{net.name}_zero_injection"),
        ):
            placement = best_draw.get((net.name, scenario))
            if placement is None:
                continue
            figures.append(draw_network(net, placement, limit, use_zib, stem))
    write_manifest(figures)
    summary["figures"] = figures

    # PageRank vector is deterministic; store nothing bulky beyond scores' spread.
    summary["pagerank_check"] = {
        net.name: {
            "min": float(np.min(pagerank(net))),
            "max": float(np.max(pagerank(net))),
        }
        for net in networks
    }
    json_path = OUT / "summary.json"
    with open(json_path, "w", encoding="utf-8") as handle:
        json.dump(summary, handle, indent=2)
    _write_tables(summary)
    print(f"wrote {json_path}", flush=True)
    return summary


def _write_tables(summary: dict) -> None:
    def rows(scenario):
        selected = [row for row in summary["runs"] if row["scenario"] == scenario]
        lines = ["network,method,seed,n_pmu,observable,unobserved,time_s,status,optimal_certificate,buses_1based"]
        for row in selected:
            buses = " ".join(str(b) for b in row["buses_1based"])
            lines.append(
                ",".join(
                    [
                        row["network"],
                        row["method"],
                        "" if row["seed"] is None else str(row["seed"]),
                        "" if row["n_pmu"] is None else str(row["n_pmu"]),
                        str(row["observable"]),
                        "" if row["unobserved"] is None else str(row["unobserved"]),
                        str(row["time_s"]),
                        str(row["status"]).replace(",", ";"),
                        str(row["optimal_certificate"]),
                        buses,
                    ]
                )
            )
        return "\n".join(lines) + "\n"

    for scenario in ("unlimited", "zero_injection", "channels_1", "channels_2", "channels_3"):
        (OUT / f"{scenario}.csv").write_text(rows(scenario), encoding="utf-8")
    init_lines = ["network,seed,initialization,initial_pmus,final_pmus,observable,time_s"]
    for row in summary["initialization"]:
        init_lines.append(
            f"{row['network']},{row['seed']},{row['initialization']},{row['initial_pmus']},{row['final_pmus']},{row['observable']},{row['time_s']}"
        )
    (OUT / "initialization.csv").write_text("\n".join(init_lines) + "\n", encoding="utf-8")
    with open(OUT / "placements.yml", "w", encoding="utf-8") as handle:
        compact = []
        for row in summary["runs"]:
            if row["method"] == "PPA" or row["n_pmu"] is None:
                continue
            compact.append(
                {
                    "network": row["network"],
                    "scenario": row["scenario"],
                    "method": row["method"],
                    "seed": row["seed"],
                    "n_pmu": row["n_pmu"],
                    "observable": row["observable"],
                    "buses_1based": row["buses_1based"],
                    "channels_0based": row.get("channels_0based"),
                }
            )
        yaml.safe_dump(compact, handle, sort_keys=False)


if __name__ == "__main__":
    run()
