"""Topological observability used by every placement method.

Two zero-injection rules are applied to a fixed point. Rule 1 does not
require the zero-injection bus itself to be observable: if every neighbor
is observable, the zero-injection bus becomes observable. Rule 2 does
require it: if the zero-injection bus is observable and exactly one
neighbor is not, that neighbor becomes observable.
"""

from __future__ import annotations

import numpy as np

from .network import Network


def assign_channels(net: Network, placement: np.ndarray, limit: int) -> list[tuple[int, int]]:
    """Choose up to ``limit`` outgoing current channels at each PMU bus.

    PMU buses are visited by descending degree, then by ascending index.
    Each PMU spends a channel on its lowest-index neighbor that is still
    unobserved. The PMU bus itself is observed by its voltage channel and
    does not consume a current channel.
    """
    pmus = [int(i) for i in np.flatnonzero(placement)]
    pmus.sort(key=lambda i: (-int(net.degrees[i]), i))
    slots = {i: int(limit) for i in pmus}
    used: set[tuple[int, int]] = set()
    measured: list[tuple[int, int]] = []
    observed = np.zeros(net.n, dtype=bool)
    observed[pmus] = True
    for _ in range(max(int(limit), 1)):
        progress = False
        for i in pmus:
            if slots[i] <= 0:
                continue
            chosen = None
            for j in net.adj[i]:
                j = int(j)
                if (i, j) in used:
                    continue
                if not observed[j]:
                    chosen = j
                    break
            if chosen is None:
                continue
            measured.append((i, chosen))
            used.add((i, chosen))
            observed[chosen] = True
            slots[i] -= 1
            progress = True
        if not progress:
            break
    return measured


def propagate_zero_injections(net: Network, observed: np.ndarray) -> np.ndarray:
    """Iterate both zero-injection rules until no bus changes state."""
    observed = observed.copy()
    if net.zibs.size == 0:
        return observed
    for _ in range(net.n + 1):
        updated = observed.copy()
        changed = False
        for z in net.zibs:
            z = int(z)
            neighbors = net.adj[z]
            if neighbors.size == 0:
                continue
            neighbor_state = observed[neighbors]
            if (not observed[z]) and bool(neighbor_state.all()):
                updated[z] = True
                changed = True
            if observed[z] and int(neighbor_state.sum()) == neighbors.size - 1:
                missing = int(neighbors[~neighbor_state][0])
                if not updated[missing]:
                    updated[missing] = True
                    changed = True
        observed = updated
        if not changed:
            break
    return observed


def observe(
    net: Network,
    placement: np.ndarray,
    channel_limit: int | None = None,
    use_zib: bool = False,
) -> tuple[np.ndarray, list[tuple[int, int]] | None]:
    """Return the observability mask and the current channels actually used.

    ``channel_limit is None`` measures every branch incident to a PMU.
    """
    placement = np.asarray(placement, dtype=int).reshape(net.n)
    observed = np.zeros(net.n, dtype=bool)
    pmus = np.flatnonzero(placement)
    observed[pmus] = True
    channels: list[tuple[int, int]] | None
    if channel_limit is None:
        channels = None
        for i in pmus:
            observed[net.adj[int(i)]] = True
    else:
        channels = assign_channels(net, placement, channel_limit)
        for _i, j in channels:
            observed[j] = True
    if use_zib:
        observed = propagate_zero_injections(net, observed)
    return observed, channels


def observe_channels(
    net: Network,
    placement: np.ndarray,
    channels: list[tuple[int, int]],
    use_zib: bool = False,
) -> np.ndarray:
    """Observability for an explicit list of current channels.

    The ILP chooses the channels itself. The greedy assignment used by the
    heuristics is a different rule and must not be used to reject an ILP
    solution.
    """
    placement = np.asarray(placement, dtype=int).reshape(net.n)
    observed = np.zeros(net.n, dtype=bool)
    observed[np.flatnonzero(placement)] = True
    for src, dst in channels:
        observed[int(dst)] = True
    if use_zib:
        observed = propagate_zero_injections(net, observed)
    return observed


def is_observable(
    net: Network,
    placement: np.ndarray,
    channel_limit: int | None = None,
    use_zib: bool = False,
) -> bool:
    mask, _channels = observe(net, placement, channel_limit, use_zib)
    return bool(mask.all())


def unobserved_count(
    net: Network,
    placement: np.ndarray,
    channel_limit: int | None = None,
    use_zib: bool = False,
) -> int:
    mask, _channels = observe(net, placement, channel_limit, use_zib)
    return int((~mask).sum())


def fitness(
    net: Network,
    placement: np.ndarray,
    channel_limit: int | None = None,
    use_zib: bool = False,
) -> float:
    """Minimization score. Every observable placement beats every other one."""
    mask, _channels = observe(net, placement, channel_limit, use_zib)
    missing = int((~mask).sum())
    installed = int(np.asarray(placement).sum())
    if missing:
        return float(net.n + missing) + 1e-3 * installed
    return float(installed)
