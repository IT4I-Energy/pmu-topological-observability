"""Replace channel-limit ILP rows with solutions checked on the ILP channels.

The first benchmark pass judged those solutions with the greedy channel
rule. The integer program chooses its own channels, so the two checks
are not the same.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from pmu_tool.algorithms import run_timed, solve_channels
from pmu_tool.benchmarks import _write_tables
from pmu_tool.network import load_all
from pmu_tool.observability import observe_channels

SUMMARY = ROOT / "benchmarks" / "summary.json"


def main() -> None:
    summary = json.loads(SUMMARY.read_text(encoding="utf-8"))
    networks = {net.name: net for net in load_all()}
    for row in summary["runs"]:
        if row["method"] != "ILP" or row["channel_limit"] is None:
            continue
        net = networks[row["network"]]
        limit = int(row["channel_limit"])
        if row.get("channel_check") == "ilp_channels":
            print(f"{net.name} L={limit} already refreshed", flush=True)
            continue
        print(f"{net.name} L={limit}", flush=True)
        (placement, status, channels), seconds = run_timed(solve_channels, net, limit, 120)
        if placement is None:
            row["status"] = status
            row["observable"] = False
            row["n_pmu"] = None
            row["channel_check"] = "ilp_channels"
            SUMMARY.write_text(json.dumps(summary, indent=2), encoding="utf-8")
            print(f"  no placement: {status} {seconds:.2f}s", flush=True)
            continue
        covered = observe_channels(net, placement, channels, False)
        buses = [int(i) for i in range(net.n) if int(placement[i]) == 1]
        row.update(
            {
                "status": status,
                "time_s": round(float(seconds), 6),
                "optimal_certificate": status == "optimal",
                "observable": bool(covered.all()),
                "n_pmu": len(buses),
                "unobserved": int((~covered).sum()),
                "buses_0based": buses,
                "buses_1based": [i + 1 for i in buses],
                "channels_0based": [[int(a), int(b)] for a, b in channels],
                "channel_check": "ilp_channels",
            }
        )
        SUMMARY.write_text(json.dumps(summary, indent=2), encoding="utf-8")
        print(f"  pmu={len(buses)} obs={row['observable']} {status} {seconds:.2f}s", flush=True)
    SUMMARY.write_text(json.dumps(summary, indent=2), encoding="utf-8")
    _write_tables(summary)
    print(f"updated {SUMMARY}")


if __name__ == "__main__":
    main()
