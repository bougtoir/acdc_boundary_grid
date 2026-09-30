from acdc_boundary.data import Edge, Feeder
import pytest

from acdc_boundary.exactness import (
    exactness_passes,
    require_exactness,
    validate_toy_cases,
)
from acdc_boundary.model import AC, DC, Parameters, line_metrics, solve_case


def parameters(boundary_efficiency=0.98):
    return Parameters(
        ac_voltage_v=400.0,
        dc_voltage_v=750.0,
        power_factor=0.95,
        endpoint_efficiency=0.96,
        boundary_efficiency=boundary_efficiency,
        standby_fraction=0.0,
        material_weight=0.0,
        converter_capacity_weight=0.0,
        conductor_scales=(1.0,),
        energy_factor=1.0,
        peak_factor=1.0,
    )


def toy_feeder():
    edge = Edge(0, 1, 0.1, 0.2, 200.0, 10000.0, 10.0, 2000.0)
    return Feeder(
        name="toy",
        code="toy",
        topology="original",
        root=0,
        nodes=(0, 1),
        children={0: (1,), 1: ()},
        node_energy_kwh={0: 0.0, 1: 10000.0},
        node_peak_kw={0: 0.0, 1: 10.0},
        coordinates={0: (0.0, 0.0), 1: (0.0, 0.001)},
        edges={(0, 1): edge},
    )


def test_line_loss_matches_analytical_formula():
    edge = toy_feeder().edges[(0, 1)]
    result = line_metrics(edge, AC, 1.0, parameters())
    current = 10000.0 / ((3.0**0.5) * 400.0 * 0.95)
    expected = 3.0 * current**2 * 0.02 / 1000.0 * 2000.0
    assert abs(result["line_loss_kwh"] - expected) < 1e-12


def test_conductor_scale_increases_ampacity_linearly():
    edge = toy_feeder().edges[(0, 1)]
    base = line_metrics(edge, AC, 1.0, parameters())
    doubled = line_metrics(edge, AC, 2.0, parameters())
    assert doubled["ampacity_fraction"] == base["ampacity_fraction"] / 2.0


def test_all_ac_constraint_is_respected():
    feeder = toy_feeder()
    assignment, result = solve_case(
        feeder,
        {0: 0.0, 1: 1.0},
        parameters(),
        allow_dc=False,
        optimize_conductor=False,
    )
    assert assignment == {0: AC, 1: AC}
    assert result["architecture"] == "all-AC"


def test_ideal_boundary_can_select_dc_for_dc_native_load():
    feeder = toy_feeder()
    assignment, _ = solve_case(
        feeder,
        {0: 0.0, 1: 1.0},
        parameters(boundary_efficiency=1.0),
        allow_dc=True,
        optimize_conductor=False,
    )
    assert assignment[1] == DC


def test_dynamic_program_matches_independent_brute_force():
    results = validate_toy_cases()
    assert results.objective_agreement.all()
    assert results.assignment_supported.all()
    assert results.conductor_scales_supported.all()
    assert results.architecture_agreement_if_unique.all()
    assert results.expected_architecture_agreement.all()


def test_conductor_selection_can_change_architecture():
    results = validate_toy_cases().set_index("case")
    assert results.at["conductor_driven_fixed", "dp_architecture"] == "hybrid"
    assert results.at["conductor_driven_optimized", "dp_architecture"] == "all-AC"
    assert results.loc[
        ["conductor_driven_fixed", "conductor_driven_optimized"],
        "conductor_driven_change_verified",
    ].all()


def test_explicit_ties_are_reported_and_supported():
    result = validate_toy_cases().set_index("case").loc["explicit_tie"]
    assert result["brute_force_optimum_count"] > 1
    assert result["dp_architecture"] == "all-AC"
    assert result["tie_handling_verified"]


def test_exactness_gate_rejects_a_failed_case():
    results = validate_toy_cases()
    results.loc[results.index[0], "objective_agreement"] = False
    assert not exactness_passes(results)
    with pytest.raises(RuntimeError, match="exactness validation failed"):
        require_exactness(results)
