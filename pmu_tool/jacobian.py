"""DC measurement-Jacobian rank from topology alone.

Line resistances and reactances are not stored in the repository. Each
branch receives a distinct positive susceptance derived from its position
in the branch list, so the rank is the generic rank for nonzero
susceptances. PMU voltage angles are absolute because the measurements
are synchronized. A current channel on a branch contributes the scaled
angle difference. A zero-injection bus contributes its Kirchhoff current
equation. Bus ``k`` is numerically observable when the unit vector ``e_k``
lies in the row space of ``H``.
"""

from __future__ import annotations

import numpy as np

from .network import Network
from .observability import assign_channels


def measurement_jacobian(
    net: Network,
    placement: np.ndarray,
    channel_limit: int | None = None,
    use_zib: bool = False,
    tol_scale: float = 1e-8,
) -> dict:
    placement = np.asarray(placement, dtype=int).reshape(net.n)
    rows: list[np.ndarray] = []
    pmus = [int(i) for i in np.flatnonzero(placement)]
    for i in pmus:
        row = np.zeros(net.n, dtype=float)
        row[i] = 1.0
        rows.append(row)

    if channel_limit is None:
        channels = []
        for i in pmus:
            for j in net.adj[i]:
                j = int(j)
                channels.append((i, j))
    else:
        channels = assign_channels(net, placement, channel_limit)

    for i, j in channels:
        a, b = (i, j) if i < j else (j, i)
        susceptance = net.susceptance[(a, b)]
        row = np.zeros(net.n, dtype=float)
        row[i] = susceptance
        row[j] = -susceptance
        rows.append(row)

    if use_zib:
        for z in net.zibs:
            z = int(z)
            row = np.zeros(net.n, dtype=float)
            for j in net.adj[z]:
                j = int(j)
                a, b = (z, j) if z < j else (j, z)
                susceptance = net.susceptance[(a, b)]
                row[z] += susceptance
                row[j] -= susceptance
            if np.any(row):
                rows.append(row)

    if not rows:
        return {
            "rank": 0,
            "target_rank": net.n,
            "full_rank": False,
            "observed_buses": 0,
            "observed_mask": np.zeros(net.n, dtype=bool),
            "n_rows": 0,
        }

    matrix = np.vstack(rows)
    _u, singular, vt = np.linalg.svd(matrix, full_matrices=False)
    scale = float(singular[0]) if singular.size else 0.0
    tol = tol_scale * scale if scale else 0.0
    rank = int(np.sum(singular > tol))
    if rank == 0:
        mask = np.zeros(net.n, dtype=bool)
    else:
        basis = vt[:rank].T
        projected = np.sum(basis * basis, axis=1)
        mask = projected > 1.0 - 1e-6
    return {
        "rank": rank,
        "target_rank": net.n,
        "full_rank": rank == net.n,
        "observed_buses": int(mask.sum()),
        "observed_mask": mask,
        "n_rows": int(matrix.shape[0]),
    }
