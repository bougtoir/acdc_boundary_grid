import math
from dataclasses import dataclass
from itertools import product

import pandas as pd

from .data import Edge, Feeder
from .model import AC, DC, OptimizationDesign, Parameters, optimize_design

EXACTNESS_BOOLEAN_COLUMNS = (
    "objective_agreement",
    "assignment_supported",
    "conductor_scales_supported",
    "architecture_agreement_if_unique",
    "expected_architecture_agreement",
    "conductor_driven_change_verified",
    "tie_handling_verified",
)


@dataclass(frozen=True)
class ToyCase:
    name: str
    feeder: Feeder
    native_dc: dict[int, float]
    params: Parameters
    optimize_conductor: bool
    expected_architecture: str


@dataclass(frozen=True)
class EnumeratedSolution:
    assignment: dict[int, str]
    conductor_scales: dict[tuple[int, int], float]
    objective: float


def _toy_feeder() -> Feeder:
    edges = {
        (0, 1): Edge(
            parent=0,
            child=1,
            length_km=1.0,
            r_ohm_per_km=0.5,
            max_i_a=200.0,
            downstream_energy_kwh=4000.0,
            downstream_peak_kw=8.0,
            loss_hours=2000.0,
        ),
        (0, 2): Edge(
            parent=0,
            child=2,
            length_km=0.2,
            r_ohm_per_km=0.2,
            max_i_a=200.0,
            downstream_energy_kwh=8000.0,
            downstream_peak_kw=20.0,
            loss_hours=2500.0,
        ),
    }
    return Feeder(
        name="enumerated-star",
        code="toy",
        topology="enumerated",
        root=0,
        nodes=(0, 1, 2),
        children={0: (1, 2), 1: (), 2: ()},
        node_energy_kwh={0: 0.0, 1: 4000.0, 2: 8000.0},
        node_peak_kw={0: 0.0, 1: 8.0, 2: 20.0},
        coordinates={0: (0.0, 0.0), 1: (0.0, 1.0), 2: (1.0, 0.0)},
        edges=edges,
    )


def _tie_feeder() -> Feeder:
    edge = Edge(
        parent=0,
        child=1,
        length_km=0.0,
        r_ohm_per_km=0.0,
        max_i_a=200.0,
        downstream_energy_kwh=0.0,
        downstream_peak_kw=0.0,
        loss_hours=0.0,
    )
    return Feeder(
        name="enumerated-tie",
        code="toy",
        topology="enumerated",
        root=0,
        nodes=(0, 1),
        children={0: (1,), 1: ()},
        node_energy_kwh={0: 0.0, 1: 0.0},
        node_peak_kw={0: 0.0, 1: 0.0},
        coordinates={0: (0.0, 0.0), 1: (0.0, 1.0)},
        edges={(0, 1): edge},
    )


def _parameters(
    endpoint_efficiency: float,
    boundary_efficiency: float,
    standby_fraction: float,
    material_weight: float,
    converter_capacity_weight: float,
) -> Parameters:
    return Parameters(
        ac_voltage_v=400.0,
        dc_voltage_v=750.0,
        power_factor=0.95,
        endpoint_efficiency=endpoint_efficiency,
        boundary_efficiency=boundary_efficiency,
        standby_fraction=standby_fraction,
        material_weight=material_weight,
        converter_capacity_weight=converter_capacity_weight,
        conductor_scales=(1.0, 1.5, 2.0),
        energy_factor=1.0,
        peak_factor=1.0,
    )


def toy_cases() -> tuple[ToyCase, ...]:
    feeder = _toy_feeder()
    return (
        ToyCase(
            name="all_ac_optimum",
            feeder=feeder,
            native_dc={0: 0.0, 1: 0.0, 2: 0.0},
            params=_parameters(0.80, 0.90, 0.002, 3.0, 10.0),
            optimize_conductor=True,
            expected_architecture="all-AC",
        ),
        ToyCase(
            name="root_dc_optimum",
            feeder=feeder,
            native_dc={0: 0.0, 1: 1.0, 2: 1.0},
            params=_parameters(0.80, 1.00, 0.0, 0.0, 0.0),
            optimize_conductor=True,
            expected_architecture="root-converted DC",
        ),
        ToyCase(
            name="interior_hybrid_optimum",
            feeder=feeder,
            native_dc={0: 0.0, 1: 1.0, 2: 0.0},
            params=_parameters(0.80, 1.00, 0.0, 0.0, 0.0),
            optimize_conductor=True,
            expected_architecture="hybrid",
        ),
        ToyCase(
            name="high_converter_penalty",
            feeder=feeder,
            native_dc={0: 0.0, 1: 1.0, 2: 1.0},
            params=_parameters(0.96, 0.96, 0.002, 3.0, 1000.0),
            optimize_conductor=True,
            expected_architecture="all-AC",
        ),
        ToyCase(
            name="high_endpoint_mismatch",
            feeder=feeder,
            native_dc={0: 0.0, 1: 1.0, 2: 0.0},
            params=_parameters(0.50, 0.90, 0.0, 0.0, 0.0),
            optimize_conductor=True,
            expected_architecture="hybrid",
        ),
        ToyCase(
            name="conductor_driven_fixed",
            feeder=feeder,
            native_dc={0: 0.0, 1: 1.0, 2: 0.0},
            params=_parameters(0.90, 0.96, 0.0, 0.0, 50.0),
            optimize_conductor=False,
            expected_architecture="hybrid",
        ),
        ToyCase(
            name="conductor_driven_optimized",
            feeder=feeder,
            native_dc={0: 0.0, 1: 1.0, 2: 0.0},
            params=_parameters(0.90, 0.96, 0.0, 0.0, 50.0),
            optimize_conductor=True,
            expected_architecture="all-AC",
        ),
        ToyCase(
            name="explicit_tie",
            feeder=_tie_feeder(),
            native_dc={0: 0.0, 1: 0.0},
            params=_parameters(1.00, 1.00, 0.0, 0.0, 0.0),
            optimize_conductor=True,
            expected_architecture="all-AC",
        ),
    )


def _independent_objective(
    feeder: Feeder,
    assignment: dict[int, str],
    conductor_scales: dict[tuple[int, int], float],
    native_dc: dict[int, float],
    params: Parameters,
) -> float:
    endpoint = 0.0
    line = 0.0
    boundary = 0.0
    material = 0.0
    converter_capacity = 0.0
    for node in feeder.nodes:
        energy = feeder.node_energy_kwh[node] * params.energy_factor
        mismatch_share = (
            1.0 - native_dc[node] if assignment[node] == DC else native_dc[node]
        )
        endpoint += (
            energy
            * mismatch_share
            * (1.0 / params.endpoint_efficiency - 1.0)
        )
    for edge_key, base_edge in feeder.edges.items():
        parent, child = edge_key
        scale = conductor_scales[edge_key]
        domain = assignment[child]
        peak_w = base_edge.downstream_peak_kw * params.peak_factor * 1000.0
        resistance = base_edge.r_ohm_per_km * base_edge.length_km / scale
        if domain == AC:
            current = peak_w / (
                math.sqrt(3.0) * params.ac_voltage_v * params.power_factor
            )
            conductor_count = 4.0
            peak_loss_kw = 3.0 * current * current * resistance / 1000.0
        else:
            current = peak_w / params.dc_voltage_v
            conductor_count = 3.0
            peak_loss_kw = 2.0 * current * current * resistance / 1000.0
        line += peak_loss_kw * base_edge.loss_hours
        material += conductor_count * base_edge.length_km * scale
        if assignment[parent] != domain:
            downstream_energy = base_edge.downstream_energy_kwh * params.energy_factor
            downstream_peak = base_edge.downstream_peak_kw * params.peak_factor
            boundary += downstream_energy * (
                1.0 / params.boundary_efficiency - 1.0
            )
            boundary += params.standby_fraction * downstream_peak * 8760.0
            converter_capacity += downstream_peak
    return (
        line
        + endpoint
        + boundary
        + params.material_weight * material
        + params.converter_capacity_weight * converter_capacity
    )


def enumerate_solutions(case: ToyCase) -> tuple[EnumeratedSolution, ...]:
    nonroot_nodes = tuple(node for node in case.feeder.nodes if node != case.feeder.root)
    edge_keys = tuple(case.feeder.edges)
    scales = case.params.conductor_scales if case.optimize_conductor else (1.0,)
    solutions = []
    for domains in product((AC, DC), repeat=len(nonroot_nodes)):
        assignment = {case.feeder.root: AC}
        assignment.update(dict(zip(nonroot_nodes, domains, strict=True)))
        for scale_values in product(scales, repeat=len(edge_keys)):
            conductor_scales = dict(zip(edge_keys, scale_values, strict=True))
            solutions.append(
                EnumeratedSolution(
                    assignment=assignment.copy(),
                    conductor_scales=conductor_scales,
                    objective=_independent_objective(
                        case.feeder,
                        assignment,
                        conductor_scales,
                        case.native_dc,
                        case.params,
                    ),
                )
            )
    return tuple(solutions)


def _architecture(feeder: Feeder, assignment: dict[int, str]) -> str:
    dc_nodes = sum(
        assignment[node] == DC for node in feeder.nodes if node != feeder.root
    )
    if dc_nodes == 0:
        return "all-AC"
    if dc_nodes == len(feeder.nodes) - 1:
        return "root-converted DC"
    return "hybrid"


def _validate_case(case: ToyCase, tolerance: float) -> dict[str, float | str | bool | int]:
    design: OptimizationDesign = optimize_design(
        case.feeder,
        case.native_dc,
        case.params,
        allow_dc=True,
        optimize_conductor=case.optimize_conductor,
    )
    enumerated = enumerate_solutions(case)
    optimum = min(solution.objective for solution in enumerated)
    scale = max(1.0, abs(optimum))
    objective_tolerance = tolerance * scale
    optima = tuple(
        solution
        for solution in enumerated
        if abs(solution.objective - optimum) <= objective_tolerance
    )
    assignment_supported = any(
        design.assignment == solution.assignment for solution in optima
    )
    scales_supported = any(
        design.assignment == solution.assignment
        and design.conductor_scales == solution.conductor_scales
        for solution in optima
    )
    dp_architecture = _architecture(case.feeder, design.assignment)
    optimum_architectures = sorted(
        {_architecture(case.feeder, solution.assignment) for solution in optima}
    )
    unique_optimum = len(optima) == 1
    return {
        "case": case.name,
        "optimize_conductor": case.optimize_conductor,
        "expected_architecture": case.expected_architecture,
        "dp_architecture": dp_architecture,
        "brute_force_architectures": "|".join(optimum_architectures),
        "enumerated_designs": len(enumerated),
        "brute_force_optimum_count": len(optima),
        "unique_optimum": unique_optimum,
        "dp_objective": design.objective,
        "brute_force_objective": optimum,
        "absolute_objective_error": abs(design.objective - optimum),
        "objective_tolerance": objective_tolerance,
        "objective_agreement": abs(design.objective - optimum) <= objective_tolerance,
        "assignment_supported": assignment_supported,
        "conductor_scales_supported": scales_supported,
        "architecture_agreement_if_unique": (
            not unique_optimum
            or dp_architecture == _architecture(case.feeder, optima[0].assignment)
        ),
        "expected_architecture_agreement": dp_architecture
        == case.expected_architecture,
        "state_evaluations": design.state_evaluations,
        "transition_evaluations": design.transition_evaluations,
    }


def validate_toy_cases(tolerance: float = 1e-10) -> pd.DataFrame:
    frame = pd.DataFrame(
        [_validate_case(case, tolerance) for case in toy_cases()]
    )
    fixed = frame.loc[frame.case == "conductor_driven_fixed", "dp_architecture"].item()
    optimized = frame.loc[
        frame.case == "conductor_driven_optimized", "dp_architecture"
    ].item()
    frame["conductor_driven_change_verified"] = True
    frame.loc[
        frame.case.isin(("conductor_driven_fixed", "conductor_driven_optimized")),
        "conductor_driven_change_verified",
    ] = fixed != optimized
    frame["tie_handling_verified"] = True
    tie = frame.case == "explicit_tie"
    frame.loc[tie, "tie_handling_verified"] = (
        (frame.loc[tie, "brute_force_optimum_count"] > 1)
        & (frame.loc[tie, "dp_architecture"] == "all-AC")
        & frame.loc[tie, "assignment_supported"]
        & frame.loc[tie, "conductor_scales_supported"]
    )
    return frame


def exactness_passes(frame: pd.DataFrame) -> bool:
    expected_cases = {case.name for case in toy_cases()}
    if (
        frame.empty
        or "case" not in frame
        or len(frame) != len(expected_cases)
        or set(frame["case"]) != expected_cases
    ):
        return False
    if any(column not in frame for column in EXACTNESS_BOOLEAN_COLUMNS):
        return False
    for column in EXACTNESS_BOOLEAN_COLUMNS:
        values = frame[column].map(
            lambda value: value
            if isinstance(value, bool)
            else str(value).strip().casefold() == "true"
        )
        if not values.all():
            return False
    return True


def require_exactness(frame: pd.DataFrame) -> None:
    if not exactness_passes(frame):
        raise RuntimeError("Dynamic-programming exactness validation failed")


def exactness_report(frame: pd.DataFrame) -> str:
    columns = [
        "case",
        "enumerated_designs",
        "brute_force_optimum_count",
        "dp_architecture",
        "brute_force_architectures",
        "absolute_objective_error",
        "objective_tolerance",
    ]
    lines = [
        "# Dynamic-Programming Exactness Validation",
        "",
        "The production dynamic program was compared with an independently coded",
        "exhaustive enumerator over every permitted bus-domain assignment and conductor",
        "combination. The enumerator does not call the production line, endpoint, boundary,",
        "or evaluation functions.",
        "",
        "```csv",
        frame[columns].to_csv(index=False).strip(),
        "```",
        "",
        f"- Cases: {len(frame)}",
        f"- Objective agreements: {int(frame.objective_agreement.sum())}/{len(frame)}",
        f"- DP assignments contained in brute-force optimum sets: "
        f"{int(frame.assignment_supported.sum())}/{len(frame)}",
        f"- DP conductor selections contained in brute-force optimum sets: "
        f"{int(frame.conductor_scales_supported.sum())}/{len(frame)}",
        f"- Unique-optimum architecture checks: "
        f"{int(frame.architecture_agreement_if_unique.sum())}/{len(frame)}",
        "- Numerical tolerance: 1e-10 times max(1, absolute optimum objective).",
        "- Exact floating-point ties in the production iteration order prefer AC and then",
        "  the smallest conductor multiplier. The explicit zero-cost tie case verifies that",
        "  this selected solution belongs to the complete brute-force optimum set.",
        "- The fixed- versus optimized-conductor pair verifies that conductor selection can",
        "  change the architecture rather than merely its objective value.",
        "",
        "Decision: **PASS**" if exactness_passes(frame) else "Decision: **FAIL**",
        "",
    ]
    return "\n".join(lines)
