"""Adversarial metamorphic/property tests added in the hostile-review round.

These tests exercise invariants of the optimization and evaluation pipeline that
do not depend on any particular scenario outcome.
"""
import itertools
import random

import pytest
from dataclasses import replace

from acdc_boundary.data import Edge, Feeder, scaled_edge
from acdc_boundary.model import (
    AC,
    DC,
    Parameters,
    boundary_metrics,
    endpoint_loss,
    evaluate,
    line_metrics,
    optimize_design,
    solve_case,
)


def base_parameters(**overrides):
    params = Parameters(
        ac_voltage_v=400.0,
        dc_voltage_v=750.0,
        power_factor=0.95,
        endpoint_efficiency=0.96,
        boundary_efficiency=0.98,
        standby_fraction=0.002,
        material_weight=3.0,
        converter_capacity_weight=2.0,
        conductor_scales=(1.0, 1.5, 2.0),
        energy_factor=1.0,
        peak_factor=1.0,
    )
    return replace(params, **overrides)


def chain_feeder(n: int, seed: int = 0) -> Feeder:
    rng = random.Random(seed)
    nodes = tuple(range(n))
    children = {i: (i + 1,) for i in range(n - 1)}
    children[n - 1] = ()
    edges = {}
    energy, peak, coords = {}, {}, {}
    for i in nodes:
        energy[i] = 0.0 if i == 0 else 1000.0 * (1 + rng.random() * 9)
        peak[i] = 0.0 if i == 0 else energy[i] / 1000.0
        coords[i] = (0.0, 0.001 * i)
    for i in range(n - 1):
        edges[(i, i + 1)] = Edge(
            i,
            i + 1,
            0.05 + 0.05 * rng.random(),
            0.1 + 0.1 * rng.random(),
            200.0,
            sum(energy[j] for j in range(i + 1, n)),
            sum(peak[j] for j in range(i + 1, n)),
            2000.0,
        )
    return Feeder(
        name="chain",
        code="chain",
        topology="original",
        root=0,
        nodes=nodes,
        children=children,
        node_energy_kwh=energy,
        node_peak_kw=peak,
        coordinates=coords,
        edges=edges,
    )


def brute_force_objective(feeder, native_dc, params, allow_dc):
    """Independent enumerator: every domain assignment x every scale combo."""
    edges = list(feeder.edges.values())
    nonroot = [n for n in feeder.nodes if n != feeder.root]
    domains = [AC, DC] if allow_dc else [AC]
    best = float("inf")
    for assignment_domains in itertools.product(domains, repeat=len(nonroot)):
        assignment = dict(zip(nonroot, assignment_domains))
        assignment[feeder.root] = AC
        for scales in itertools.product(params.conductor_scales, repeat=len(edges)):
            total = sum(
                endpoint_loss(feeder, n, assignment[n], native_dc, params)
                for n in feeder.nodes
            )
            for (edge, scale) in zip(edges, scales):
                parent, child = edge.parent, edge.child
                scaled = scaled_edge(edge, params.energy_factor, params.peak_factor)
                line = line_metrics(scaled, assignment[child], scale, params)
                total += (
                    line["line_loss_kwh"]
                    + params.material_weight * line["material_index"]
                )
                if assignment[parent] != assignment[child]:
                    boundary = boundary_metrics(scaled, params)
                    total += (
                        boundary["boundary_loss_kwh"]
                        + params.converter_capacity_weight
                        * boundary["converter_capacity_kw"]
                    )
            best = min(best, total)
    return best


@pytest.mark.parametrize("seed", range(4))
def test_dp_matches_brute_force_on_random_chains(seed):
    feeder = chain_feeder(4, seed)
    params = base_parameters()
    native = {n: 0.5 for n in feeder.nodes}
    design = optimize_design(feeder, native, params, allow_dc=True, optimize_conductor=True)
    bf = brute_force_objective(feeder, native, params, allow_dc=True)
    assert design.objective == pytest.approx(bf, rel=1e-9, abs=1e-9)


def test_optional_dc_cannot_worsen_objective():
    for share in (0.0, 0.25, 0.5, 0.75, 1.0):
        feeder = chain_feeder(4, seed=1)
        params = base_parameters()
        native = {n: share for n in feeder.nodes}
        ac_obj = optimize_design(
            feeder, native, params, allow_dc=False, optimize_conductor=True
        ).objective
        joint_obj = optimize_design(
            feeder, native, params, allow_dc=True, optimize_conductor=True
        ).objective
        assert joint_obj <= ac_obj + 1e-9


def test_conductor_optimization_cannot_worsen_objective():
    feeder = chain_feeder(4, seed=2)
    params = base_parameters()
    native = {n: 0.5 for n in feeder.nodes}
    fixed = optimize_design(
        feeder, native, params, allow_dc=True, optimize_conductor=False
    ).objective
    joint = optimize_design(
        feeder, native, params, allow_dc=True, optimize_conductor=True
    ).objective
    assert joint <= fixed + 1e-9


def test_determinism():
    feeder = chain_feeder(5, seed=3)
    params = base_parameters()
    native = {n: 0.5 for n in feeder.nodes}
    a1, r1 = solve_case(feeder, native, params, True, True)
    a2, r2 = solve_case(feeder, native, params, True, True)
    assert a1 == a2
    assert r1 == r2


def test_loss_components_nonnegative():
    feeder = chain_feeder(4, seed=4)
    params = base_parameters()
    for share in (0.0, 1.0):
        native = {n: share for n in feeder.nodes}
        _, result = solve_case(feeder, native, params, True, True)
        for key in (
            "line_loss_kwh",
            "endpoint_loss_kwh",
            "boundary_loss_kwh",
            "total_loss_kwh",
            "material_index",
            "converter_capacity_kw",
        ):
            assert result[key] >= 0.0, key
        assert 0.0 <= result["dc_energy_fraction"] <= 1.0
        assert 0.0 <= result["dc_node_fraction"] <= 1.0
        assert result["max_ampacity_fraction"] >= 0.0
        assert result["max_single_edge_drop_pu"] >= 0.0


def test_endpoint_mismatch_is_symmetric():
    feeder = chain_feeder(2)
    params = base_parameters()
    energy = feeder.node_energy_kwh[1]
    eta = params.endpoint_efficiency
    zero_dc = {0: 0.0, 1: 0.0}
    full_dc = {0: 0.0, 1: 1.0}
    # share 0: a DC node converts ALL its energy
    assert endpoint_loss(feeder, 1, DC, zero_dc, params) == pytest.approx(
        energy * (1 / eta - 1)
    )
    # share 1: an AC node converts all its energy
    assert endpoint_loss(feeder, 1, AC, full_dc, params) == pytest.approx(
        energy * (1 / eta - 1)
    )
    # share 1 on DC, share 0 on AC: no mismatch
    assert endpoint_loss(feeder, 1, DC, full_dc, params) == 0.0
    assert endpoint_loss(feeder, 1, AC, zero_dc, params) == 0.0


def test_zero_native_dc_penalizes_every_dc_node():
    feeder = chain_feeder(3)
    params = base_parameters()
    native = {n: 0.0 for n in feeder.nodes}
    design = optimize_design(feeder, native, params, allow_dc=True, optimize_conductor=True)
    for node in feeder.nodes:
        if design.assignment[node] == DC:
            assert endpoint_loss(feeder, node, DC, native, params) > 0


def test_nonnegative_penalties_cannot_reduce_fixed_design_objective():
    feeder = chain_feeder(4, seed=5)
    params = base_parameters()
    native = {n: 0.5 for n in feeder.nodes}
    design = optimize_design(feeder, native, params, allow_dc=True, optimize_conductor=True)
    heavier = replace(
        params,
        material_weight=params.material_weight * 2,
        converter_capacity_weight=params.converter_capacity_weight * 2,
    )
    base_obj = evaluate(
        feeder, native, params, design.assignment, True,
        conductor_scales=design.conductor_scales,
    )["objective"]
    heavier_obj = evaluate(
        feeder, native, heavier, design.assignment, True,
        conductor_scales=design.conductor_scales,
    )["objective"]
    assert heavier_obj >= base_obj


def test_config_propagation_endpoint_efficiency():
    feeder = chain_feeder(2)
    native = {0: 0.0, 1: 0.0}
    e1 = endpoint_loss(feeder, 1, DC, native, base_parameters(endpoint_efficiency=0.90))
    e2 = endpoint_loss(feeder, 1, DC, native, base_parameters(endpoint_efficiency=0.96))
    assert e1 > e2  # lower efficiency => larger conversion loss on a DC node


def test_boundary_loss_monotone_in_efficiency():
    feeder = chain_feeder(2)
    edge = scaled_edge(feeder.edges[(0, 1)], 1.0, 1.0)
    b_low = boundary_metrics(edge, base_parameters(boundary_efficiency=0.94))
    b_high = boundary_metrics(edge, base_parameters(boundary_efficiency=0.99))
    assert b_low["boundary_loss_kwh"] > b_high["boundary_loss_kwh"]


def test_conductor_counts_enter_only_material_index():
    """Conductor-count bookkeeping must not alter electrical loss terms."""
    feeder = chain_feeder(3)
    edge = scaled_edge(feeder.edges[(0, 1)], 1.0, 1.0)
    for domain in (AC, DC):
        base = line_metrics(edge, domain, 1.5, base_parameters())
        other = line_metrics(
            edge,
            domain,
            1.5,
            base_parameters(ac_conductor_count=3.0, dc_conductor_count=2.0),
        )
        assert base["line_loss_kwh"] == other["line_loss_kwh"]
        assert base["current_a"] == other["current_a"]
        assert base["ampacity_fraction"] == other["ampacity_fraction"]
        assert base["drop_pu"] == other["drop_pu"]
        assert base["material_index"] != other["material_index"]


def test_conductor_count_scales_material_linearly():
    feeder = chain_feeder(3)
    edge = scaled_edge(feeder.edges[(0, 1)], 1.0, 1.0)
    four = line_metrics(edge, AC, 1.0, base_parameters(ac_conductor_count=4.0))
    two = line_metrics(edge, AC, 1.0, base_parameters(ac_conductor_count=2.0))
    assert four["material_index"] == 2.0 * two["material_index"]
    dc_three = line_metrics(edge, DC, 1.0, base_parameters(dc_conductor_count=3.0))
    dc_two = line_metrics(edge, DC, 1.0, base_parameters(dc_conductor_count=2.0))
    assert dc_three["material_index"] == 1.5 * dc_two["material_index"]


def test_objective_without_material_weight_ignores_conductor_counts():
    """With material_weight=0 the counts cannot change the optimal design."""
    feeder = chain_feeder(4)
    native = {i: 0.5 for i in feeder.nodes}
    base = solve_case(
        feeder,
        native,
        base_parameters(material_weight=0.0),
        allow_dc=True,
        optimize_conductor=True,
    )[1]
    alt = solve_case(
        feeder,
        native,
        base_parameters(
            material_weight=0.0, ac_conductor_count=1.0, dc_conductor_count=1.0
        ),
        allow_dc=True,
        optimize_conductor=True,
    )[1]
    assert base["architecture"] == alt["architecture"]
    assert base["total_loss_kwh"] == alt["total_loss_kwh"]
    assert base["dc_node_fraction"] == alt["dc_node_fraction"]
