"""Publication figures for the IEEE 118-bus and NCEII 233-bus networks."""

from __future__ import annotations

from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import networkx as nx
import numpy as np
import yaml

from .network import Network
from .observability import observe

ROOT = Path(__file__).resolve().parents[1]
FIGURES = ROOT / "figures"


def draw_network(
    net: Network,
    placement: np.ndarray,
    channel_limit: int | None,
    use_zib: bool,
    stem: str,
) -> dict:
    FIGURES.mkdir(parents=True, exist_ok=True)
    mask, _channels = observe(net, placement, channel_limit, use_zib)
    graph = nx.Graph()
    graph.add_nodes_from(range(net.n))
    graph.add_edges_from(net.branches)
    if nx.is_connected(graph):
        layout = nx.kamada_kawai_layout(graph)
    else:
        layout = nx.spring_layout(graph, seed=1)
    placement = np.asarray(placement, dtype=int)
    zset = set(int(z) for z in net.zibs)
    pmu_nodes = [i for i in range(net.n) if placement[i] == 1]
    zib_nodes = [i for i in range(net.n) if i in zset and placement[i] == 0 and mask[i]]
    unobs_nodes = [i for i in range(net.n) if not mask[i]]
    other = [i for i in range(net.n) if i not in set(pmu_nodes) | set(zib_nodes) | set(unobs_nodes)]
    side = 18 if net.n > 150 else 16
    fig, ax = plt.subplots(figsize=(side, side))
    nx.draw_networkx_edges(graph, layout, ax=ax, width=1.8, edge_color="#4B5563", alpha=0.85)
    nx.draw_networkx_nodes(graph, layout, nodelist=other, node_color="#E5E7EB", node_size=70, ax=ax, linewidths=0.4, edgecolors="#374151")
    nx.draw_networkx_nodes(graph, layout, nodelist=zib_nodes, node_color="#67E8F9", node_size=80, ax=ax, linewidths=0.4, edgecolors="#0E7490")
    nx.draw_networkx_nodes(graph, layout, nodelist=unobs_nodes, node_color="#FCA5A5", node_size=90, ax=ax, linewidths=0.6, edgecolors="#B91C1C")
    nx.draw_networkx_nodes(graph, layout, nodelist=pmu_nodes, node_color="#16A34A", node_size=220, ax=ax, linewidths=0.8, edgecolors="#14532D")
    labels = {i: str(i) for i in range(net.n)}
    font = 5.5 if net.n > 150 else 8
    nx.draw_networkx_labels(graph, layout, labels, font_size=font, font_color="#111827", ax=ax)
    ax.set_axis_off()
    title = f"{net.name}: {int(placement.sum())} PMUs, {int(mask.sum())}/{net.n} buses observed"
    ax.set_title(title, fontsize=14)
    fig.tight_layout()
    png = FIGURES / f"{stem}.png"
    pdf = FIGURES / f"{stem}.pdf"
    fig.savefig(png, dpi=200)
    fig.savefig(pdf)
    plt.close(fig)
    return {
        "stem": stem,
        "png": str(png.relative_to(ROOT)),
        "pdf": str(pdf.relative_to(ROOT)),
        "network": net.name,
        "pmus_0based": [int(i) for i in np.flatnonzero(placement)],
        "pmus_1based": [int(i) + 1 for i in np.flatnonzero(placement)],
        "observed_buses": int(mask.sum()),
        "buses": net.n,
        "zero_based_labels": True,
        "legend": "Green: PMU bus. Cyan: observed zero-injection bus. Red: unobserved bus. Grey: other observed bus. Labels are 0-based.",
    }


def write_manifest(entries: list[dict]) -> None:
    FIGURES.mkdir(parents=True, exist_ok=True)
    with open(FIGURES / "manifest.yml", "w", encoding="utf-8") as handle:
        yaml.safe_dump(entries, handle, sort_keys=False)
