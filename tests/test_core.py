"""Correctness checks for observability, the Jacobian, and the ILP baselines."""

import unittest

import numpy as np

from pmu_tool.algorithms import solve_channels, solve_domination, solve_zero_injection
from pmu_tool.jacobian import measurement_jacobian
from pmu_tool.network import load_all, make_network, zib_clusters
from pmu_tool.observability import is_observable, observe


class ObservabilityTests(unittest.TestCase):
    def test_rule1_does_not_require_the_zib_to_be_observable(self):
        # PMUs at the leaves observe buses 1 and 2. Bus 0 is a zero-injection
        # bus and is not directly observed. Rule 1 observes it.
        net = make_network("rule1", 5, [(0, 1), (0, 2), (1, 3), (2, 4)], zibs=[0])
        placement = np.array([0, 0, 0, 1, 1])
        without, _channels = observe(net, placement, None, use_zib=False)
        with_rules, _channels = observe(net, placement, None, use_zib=True)
        self.assertFalse(without[0])
        self.assertTrue(with_rules.all())

    def test_rule2_requires_the_zib_itself(self):
        # One PMU at an end of a path whose middle bus is a zero injection.
        # Rule 2 propagates through that observed zero-injection bus.
        net = make_network("rule2", 3, [(0, 1), (1, 2)], zibs=[1])
        placement = np.array([1, 0, 0])
        self.assertFalse(is_observable(net, placement, None, False))
        self.assertTrue(is_observable(net, placement, None, True))
        # The same PMU does not observe the far bus when the middle bus is
        # not a zero injection.
        plain = make_network("plain", 3, [(0, 1), (1, 2)], zibs=[])
        self.assertFalse(is_observable(plain, placement, None, True))

    def test_channel_limit_blocks_unlimited_coverage(self):
        net = make_network("star", 4, [(0, 1), (0, 2), (0, 3)])
        placement = np.array([1, 0, 0, 0])
        self.assertTrue(is_observable(net, placement, None, False))
        self.assertFalse(is_observable(net, placement, 1, False))
        self.assertTrue(is_observable(net, placement, 3, False))

    def test_zero_injection_counts(self):
        nets = {net.name: net for net in load_all()}
        self.assertEqual(int(nets["IEEE14"].zibs.size), 1)
        self.assertEqual(int(nets["IEEE57"].zibs.size), 15)
        self.assertEqual(int(nets["IEEE118"].zibs.size), 10)
        self.assertEqual(int(nets["NCEII233"].zibs.size), 173)
        sizes = sorted((len(c) for c in zib_clusters(nets["NCEII233"])), reverse=True)
        self.assertEqual(sizes[0], 150)

    def test_ieee_unlimited_ilp_matches_standard_counts(self):
        expected = {"IEEE14": 4, "IEEE57": 17, "IEEE118": 32}
        for net in load_all():
            if net.name not in expected:
                continue
            placement, status = solve_domination(net, time_limit=60)
            self.assertIsNotNone(placement)
            self.assertEqual(status, "optimal")
            self.assertEqual(int(placement.sum()), expected[net.name])
            self.assertTrue(is_observable(net, placement, None, False))

    def test_ieee14_zero_injection_ilp_is_three(self):
        net = next(net for net in load_all() if net.name == "IEEE14")
        placement, status = solve_zero_injection(net, time_limit=60)
        self.assertEqual(status, "optimal", msg=status)
        self.assertEqual(int(placement.sum()), 3)
        self.assertTrue(is_observable(net, placement, None, True))

    def test_channel_ilp_on_a_star(self):
        net = make_network("star", 4, [(0, 1), (0, 2), (0, 3)])
        placement, status, _channels = solve_channels(net, limit=1, time_limit=30)
        self.assertEqual(status, "optimal")
        self.assertTrue(is_observable(net, placement, 1, False))
        # One channel cannot cover three leaves from the center alone.
        self.assertGreaterEqual(int(placement.sum()), 2)

    def test_jacobian_agrees_on_a_placement_without_zero_injections(self):
        net = make_network("path", 3, [(0, 1), (1, 2)])
        full = np.array([0, 1, 0])
        empty = np.array([0, 0, 0])
        self.assertTrue(measurement_jacobian(net, full, None, False)["full_rank"])
        self.assertFalse(measurement_jacobian(net, empty, None, False)["full_rank"])
        self.assertEqual(measurement_jacobian(net, full, None, False)["observed_buses"], 3)


if __name__ == "__main__":
    unittest.main()
