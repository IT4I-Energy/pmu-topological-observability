# Topological observability framework for optimal PMU placement

Open Python code for placing phasor measurement units (PMUs) so that a power network is fully observable. The supported release is the `pmu_tool` package in this folder. The files in `legacy/` are the archived scripts from [mhurtgen/PMU](https://github.com/mhurtgen/PMU), kept so the earlier experiments can be read. New runs should use `pmu_tool`.

The code covers three placement settings:

- unlimited current channels, with and without zero-injection buses
- a limit of L current channels on each PMU
- the IEEE 14-bus, 57-bus, and 118-bus systems, and the 233-bus Czech NCEII network bundled with the repository

Bus indices inside the code and in the figure labels are **0-based**. The result tables also list the **1-based** bus numbers used by MATPOWER.

## Measured results

The bundled experiment uses seeds 0 and 1 in the conda environment `PMU_env` (Python 3.11.18, Intel Core Ultra 9 185H, 30.45 GiB RAM). Two seeds are a reproducibility check. They are not a sample for a mean or a confidence interval. Every count below is copied from `benchmarks/summary.json`. Bus lists are in `benchmarks/placements.yml`.

An integer-program count is certified only when HiGHS returns an optimal status and the topological checker accepts the placement. Heuristic searches stop at a fixed budget.

**Unlimited channels, no zero-injection rules.** Certified minima: IEEE 14 = 4, IEEE 57 = 17, IEEE 118 = 32, NCEII 233 = 84. Iterated local search matches those counts on both seeds, except IEEE 118 seed 1, which returns 33. On IEEE 14 and IEEE 57, PageRank, degree, and random starts all finish at the certified minimum. On IEEE 118 the three starts finish at 32 or 33. On NCEII the pruned starts contain 89, 87, and 98 or 100 PMUs, and local search reduces each of them to 84.

**Zero-injection buses, unlimited channels.** The depth-12 integer program certifies IEEE 14 = 3, IEEE 57 = 11, and IEEE 118 = 29. Iterated local search matches those counts on both seeds. The NCEII list in `legacy/getinfoNCEII.py` contains 173 zero-injection buses in five clusters, the largest of size 150. The depth-indexed integer program was not run on that cluster. Iterated local search observes every NCEII bus with 26 PMUs on both seeds. That 26 is a feasible count. The genetic algorithm returns 31, particle swarm returns 28 and 29, simulated annealing returns 32, and the PageRank start returns 60.

**At most L current channels, no zero-injection rules.** The integer program chooses the directed channels. The heuristics then assign channels with the greedy rule, so a heuristic count can be higher. Certified counts for L = 1, 2, and 3:

| Network | L = 1 | L = 2 | L = 3 |
|---|---:|---:|---:|
| IEEE 14 | 7 | 5 | 4 |
| IEEE 57 | 29 | 19 | 17 |
| IEEE 118 | 61 | 41 | 33 |
| NCEII 233 | 121 | 87 | 84 |

**Topological check versus the DC Jacobian.** On the best unlimited placement and the best zero-injection placement, both checks observe every bus. The median Jacobian time divided by the median topological time is 21.0, 91.1, 344.4, and 273.2 on IEEE 14, 57, 118, and NCEII for the unlimited placements, and 8.3, 10.3, 131.3, and 4.5 for the zero-injection placements. Branch susceptances are distinct positive values assigned from the branch-list order, because the repository stores endpoints only.

## Install

The tests in this release were run in a conda environment named `PMU_env`.

```bash
conda env create -f environment.yml
conda activate PMU_env
python -m unittest tests.test_core -v
python -m pmu_tool.benchmarks
```

`environment.yml` pins the versions used for the bundled benchmark. A pip-style list of the same packages is in `requirements.txt`.

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
```

No commercial solver and no MATLAB licence are required. Integer programs are solved by HiGHS through `scipy.optimize.milp`.

## What a PMU observes

The network is an undirected graph. Branch data in this repository are the two endpoints of each branch. Line impedances are not included.

**Unlimited channels.** A binary variable `x_i` is 1 when a PMU is installed at bus `i`. That PMU observes bus `i` and every adjacent bus. Full observability is `(A + I) x >= 1`, and the objective is the number of PMUs. `Graph.getPDS` in the legacy code solves the same model.

**Limited channels.** The PMU still measures the voltage at its own bus. It may also measure at most `L` incident branches. A neighbor is observed only when one of those current channels points at it. The integer program chooses the PMU buses and the directed channels together. The heuristics search the PMU buses and then assign channels with a fixed greedy rule: visit PMU buses by descending degree, and spend each channel on the lowest-index neighbor that is still unobserved.

**Zero-injection buses.** A bus with zero active load, zero reactive load, and no generator is a zero-injection bus. On the bundled IEEE pickles that definition gives 1 bus (IEEE 14, bus 7 in 1-based numbering), 15 buses (IEEE 57), and 10 buses (IEEE 118). The NCEII list shipped in `legacy/getinfoNCEII.py` contains 173 zero-injection buses, in five clusters, the largest of which has 150 buses.

Two rules are applied until no bus changes state:

1. If every neighbor of a zero-injection bus is observable, the zero-injection bus becomes observable. The zero-injection bus does not have to be observable before this rule runs.
2. If a zero-injection bus is observable and exactly one of its neighbors is not, that neighbor becomes observable.

Rule 1 does not require the zero-injection bus to be observable before it runs. Rule 2 does: the zero-injection bus is already observable, and exactly one neighbor is not.

## Algorithms

| Method | Role | Where |
|---|---|---|
| ILP | Certified minimum for unlimited channels, for a channel limit, and for IEEE zero-injection instances at propagation depth 12 | `solve_domination`, `solve_channels`, `solve_zero_injection` |
| PPA | PageRank start: a PMU at the neighbor of each leaf, then PMUs at unobserved buses in PageRank order | `ppa` |
| ILS | Move one PMU to an adjacent bus when observability is kept, delete redundant PMUs, add two PMUs, repeat | `iterated_local_search` |
| GA | Binary genetic algorithm, tournament 3, uniform crossover 0.8, bit-flip probability 1/N | `genetic_algorithm` |
| PSO | Binary particle swarm, sigmoid transfer, inertia 0.7, coefficients 1.5 and 1.5 | `particle_swarm` |
| SA | Bit-flip Metropolis search, geometric cooling | `simulated_annealing` |

Every feasible heuristic placement is reduced by deleting PMUs that are not required. The search stops because the iteration budget is exhausted, not because a gap to the optimum has been proved. Seeds used in the bundled benchmark are 0 and 1.

Default budgets, also printed in `benchmarks/summary.json`:

| Search | Budget |
|---|---|
| ILS | 20 local moves inside each of 30 outer iterations; restart adds 2 PMUs |
| GA | population 30, 40 generations, elitism 2 |
| PSO | 30 particles, 40 iterations, velocity clamped to [-4, 4] |
| SA | start temperature 2, cooling 0.95, stop at temperature 0.05 or 4000 evaluations |
| PageRank | damping 0.85, 60 power iterations |

Complexity of one topological check is `O(N (N + M))` in the worst case, because the rules may be repeated once per bus on a dense scan. These grids are sparse, so a check is a short walk over the PMU neighborhoods. PageRank is 60 sparse iterations. The Jacobian check is one singular-value decomposition of a matrix with one row per voltage, current, and zero-injection equation.

## Numerical Jacobian

`pmu_tool.jacobian` builds a DC measurement Jacobian without line data. Branch `k` gets the susceptance `1 + 0.001 (k + 1)`, so the values are positive and distinct and the rank is the generic rank for nonzero susceptances. States are absolute voltage angles, because a PMU is synchronized. A bus is numerically observable when its unit vector lies in the row space of `H`.

The timing comparison in the measured results uses this Jacobian. The branch files store endpoints only, so the susceptances are these generic positive values.

## Run one case

```python
from pmu_tool.algorithms import iterated_local_search, solve_domination
from pmu_tool.network import load_named
import numpy as np

net = load_named("IEEE14")
placement, status = solve_domination(net)
print(status, int(placement.sum()))

rng = np.random.default_rng(0)
found, history = iterated_local_search(net, rng)
print(int(found.sum()), history)
```

Channel limit and zero-injection rules are arguments:

```python
from pmu_tool.algorithms import solve_channels, solve_zero_injection

placement, status, channels = solve_channels(net, limit=1)
placement, status = solve_zero_injection(net, depth=12)
```

`load_named` accepts `IEEE14`, `IEEE57`, `IEEE118`, and `NCEII233`.

## Benchmark outputs

`python -m pmu_tool.benchmarks` writes:

| Path | Contents |
|---|---|
| `benchmarks/summary.json` | Environment, parameters, every run, Jacobian timings |
| `benchmarks/unlimited.csv` | Unlimited-channel counts |
| `benchmarks/zero_injection.csv` | Zero-injection counts |
| `benchmarks/channels_1.csv`, `channels_2.csv`, `channels_3.csv` | Channel-limit counts |
| `benchmarks/initialization.csv` | PageRank, degree, and random starts |
| `benchmarks/placements.yml` | 1-based bus lists and current channels |
| `figures/` | IEEE 118 and NCEII drawings, PDF and PNG, plus `manifest.yml` |
| `tools/refresh_channel_ilp.py` | Recomputes the channel-limit integer programs and rewrites their rows |

## Figures

Green nodes are PMU buses. Cyan nodes are observed zero-injection buses. Red nodes are unobserved. Labels are 0-based. The drawings use a Kamada-Kawai layout, thicker edges, and a large canvas so the IEEE 118 and NCEII 233 labels can be read when the PDF is enlarged. `figures/manifest.yml` records which file belongs to which network and lists the PMU buses.

## Legacy code

`legacy/` includes the original modules, `CITATION.cff`, the upstream README, and `Figure.zip`. Several of those scripts open a `Grids/` directory that is not in the current layout, and `OptPlacementPMU_constr.ILS` calls `ILS_constr` with the wrong number of arguments. `pmu_tool` is the version that the tests use. Do not load the pickle files from an untrusted source.

## Citation

M. Hurtgen and P. Praks. *PMU: Topological observability framework for optimal PMU placement.* Software, 2026. https://github.com/IT4I-Energy/pmu-topological-observability

Machine-readable metadata is in `CITATION.cff`. The software licence is CC BY 4.0; see `LICENSE`.

## Repository map

```text
pmu_tool/            supported placement code
tests/test_core.py   observability, Jacobian, and ILP checks
tools/               channel-limit integer-program refresh
benchmarks/          results of the two-seed run
figures/             network drawings
data/                IEEE pickles, NCEII specifications, archived results
legacy/              earlier Python scripts
environment.yml      conda environment PMU_env
```
