import math
from dataclasses import dataclass

from .data import Edge, Feeder, scaled_edge


AC = "AC"
DC = "DC"


@dataclass(frozen=True)
class Parameters:
    ac_voltage_v: float
    dc_voltage_v: float
    power_factor: float
    endpoint_efficiency: float
    boundary_efficiency: float
    standby_fraction: float
    material_weight: float
    converter_capacity_weight: float
    conductor_scales: tuple[float, ...]
    energy_factor: float
    peak_factor: float


@dataclass(frozen=True)
class OptimizationDesign:
    assignment: dict[int, str]
    conductor_scales: dict[tuple[int, int], float]
    objective: float
    state_evaluations: int
    transition_evaluations: int


def line_metrics(edge: Edge, domain: str, scale: float, params: Parameters) -> dict[str, float]:
    resistance = edge.r_ohm_per_km * edge.length_km / scale
    peak_w = edge.downstream_peak_kw * 1000.0
    if domain == AC:
        current = peak_w / (math.sqrt(3.0) * params.ac_voltage_v * params.power_factor)
        peak_loss_kw = 3.0 * current * current * resistance / 1000.0
        conductors = 4.0
    else:
        current = peak_w / params.dc_voltage_v
        peak_loss_kw = 2.0 * current * current * resistance / 1000.0
        conductors = 3.0
    annual_loss = peak_loss_kw * edge.loss_hours
    material = conductors * edge.length_km * scale
    scaled_ampacity_a = edge.max_i_a * scale
    return {
        "line_loss_kwh": annual_loss,
        "material_index": material,
        "current_a": current,
        "ampacity_fraction": current / scaled_ampacity_a if scaled_ampacity_a else 0.0,
        "drop_pu": current * resistance / (
            params.ac_voltage_v / math.sqrt(3.0) if domain == AC else params.dc_voltage_v / 2.0
        ),
    }


def boundary_metrics(edge: Edge, params: Parameters) -> dict[str, float]:
    loss = edge.downstream_energy_kwh * (1.0 / params.boundary_efficiency - 1.0)
    standby = (
        params.standby_fraction * edge.downstream_peak_kw * 8760.0
    )
    return {
        "boundary_loss_kwh": loss + standby,
        "converter_capacity_kw": edge.downstream_peak_kw,
    }


def endpoint_loss(feeder: Feeder, node: int, domain: str, native_dc: dict[int, float], params: Parameters) -> float:
    energy = feeder.node_energy_kwh[node] * params.energy_factor
    dc_share = native_dc[node]
    mismatched = energy * ((1.0 - dc_share) if domain == DC else dc_share)
    return mismatched * (1.0 / params.endpoint_efficiency - 1.0)


def _edge_choice(edge: Edge, domain: str, params: Parameters, optimize_conductor: bool):
    choices = params.conductor_scales if optimize_conductor else (1.0,)
    return min(
        (
            params.material_weight * line_metrics(edge, domain, scale, params)["material_index"]
            + line_metrics(edge, domain, scale, params)["line_loss_kwh"],
            scale,
        )
        for scale in choices
    )


def optimize_design(
    feeder: Feeder,
    native_dc: dict[int, float],
    params: Parameters,
    allow_dc: bool,
    optimize_conductor: bool,
) -> OptimizationDesign:
    choices = (AC, DC) if allow_dc else (AC,)
    memo: dict[tuple[int, str], float] = {}
    decision: dict[tuple[int, str, int], tuple[str, float]] = {}
    transition_evaluations = 0

    def solve(node: int, domain: str) -> float:
        nonlocal transition_evaluations
        key = (node, domain)
        if key in memo:
            return memo[key]
        value = endpoint_loss(feeder, node, domain, native_dc, params)
        for child in feeder.children[node]:
            edge = scaled_edge(
                feeder.edges[(node, child)], params.energy_factor, params.peak_factor
            )
            alternatives = []
            for child_domain in choices:
                transition_evaluations += (
                    len(params.conductor_scales) if optimize_conductor else 1
                )
                edge_cost, scale = _edge_choice(edge, child_domain, params, optimize_conductor)
                transition = 0.0
                if domain != child_domain:
                    boundary = boundary_metrics(edge, params)
                    transition = (
                        boundary["boundary_loss_kwh"]
                        + params.converter_capacity_weight
                        * boundary["converter_capacity_kw"]
                    )
                alternatives.append(
                    (solve(child, child_domain) + edge_cost + transition, child_domain, scale)
                )
            best = min(alternatives, key=lambda item: item[0])
            value += best[0]
            decision[(node, domain, child)] = (best[1], best[2])
        memo[key] = value
        return value

    objective = solve(feeder.root, AC)
    assignment = {feeder.root: AC}
    conductor_scales: dict[tuple[int, int], float] = {}

    def recover(node: int, domain: str) -> None:
        for child in feeder.children[node]:
            child_domain, scale = decision[(node, domain, child)]
            assignment[child] = child_domain
            conductor_scales[(node, child)] = scale
            recover(child, child_domain)

    recover(feeder.root, AC)
    return OptimizationDesign(
        assignment=assignment,
        conductor_scales=conductor_scales,
        objective=objective,
        state_evaluations=len(memo),
        transition_evaluations=transition_evaluations,
    )


def optimize_domains(
    feeder: Feeder,
    native_dc: dict[int, float],
    params: Parameters,
    allow_dc: bool,
    optimize_conductor: bool,
) -> dict[int, str]:
    return optimize_design(
        feeder,
        native_dc,
        params,
        allow_dc,
        optimize_conductor,
    ).assignment


def evaluate(
    feeder: Feeder,
    native_dc: dict[int, float],
    params: Parameters,
    assignment: dict[int, str],
    optimize_conductor: bool,
) -> dict[str, float | str]:
    result = {
        "line_loss_kwh": 0.0,
        "endpoint_loss_kwh": 0.0,
        "boundary_loss_kwh": 0.0,
        "material_index": 0.0,
        "converter_capacity_kw": 0.0,
        "converter_count": 0,
        "max_ampacity_fraction": 0.0,
        "max_single_edge_drop_pu": 0.0,
    }
    boundary_edges = []
    conductor_scales = []
    for node in feeder.nodes:
        result["endpoint_loss_kwh"] += endpoint_loss(
            feeder, node, assignment[node], native_dc, params
        )
    for (parent, child), base_edge in feeder.edges.items():
        edge = scaled_edge(base_edge, params.energy_factor, params.peak_factor)
        domain = assignment[child]
        _, scale = _edge_choice(edge, domain, params, optimize_conductor)
        conductor_scales.append(f"{parent}-{child}:{scale:g}")
        line = line_metrics(edge, domain, scale, params)
        for key in ("line_loss_kwh", "material_index"):
            result[key] += line[key]
        result["max_ampacity_fraction"] = max(
            result["max_ampacity_fraction"], line["ampacity_fraction"]
        )
        result["max_single_edge_drop_pu"] = max(
            result["max_single_edge_drop_pu"], line["drop_pu"]
        )
        if assignment[parent] != assignment[child]:
            boundary_edges.append(f"{parent}-{child}")
            boundary = boundary_metrics(edge, params)
            result["boundary_loss_kwh"] += boundary["boundary_loss_kwh"]
            result["converter_capacity_kw"] += boundary["converter_capacity_kw"]
            result["converter_count"] += 1
    result["total_loss_kwh"] = (
        result["line_loss_kwh"]
        + result["endpoint_loss_kwh"]
        + result["boundary_loss_kwh"]
    )
    result["objective"] = (
        result["total_loss_kwh"]
        + params.material_weight * result["material_index"]
        + params.converter_capacity_weight * result["converter_capacity_kw"]
    )
    dc_nodes = sum(assignment[node] == DC for node in feeder.nodes if node != feeder.root)
    result["dc_node_fraction"] = dc_nodes / max(1, len(feeder.nodes) - 1)
    nonroot_energy = sum(
        feeder.node_energy_kwh[node]
        for node in feeder.nodes
        if node != feeder.root
    )
    dc_energy = sum(
        feeder.node_energy_kwh[node]
        for node in feeder.nodes
        if node != feeder.root and assignment[node] == DC
    )
    result["dc_energy_fraction"] = dc_energy / nonroot_energy if nonroot_energy else 0.0
    result["dc_bus_signature"] = "|".join(
        str(node)
        for node in feeder.nodes
        if node != feeder.root and assignment[node] == DC
    )
    result["boundary_signature"] = "|".join(boundary_edges)
    result["conductor_scale_signature"] = "|".join(conductor_scales)
    if dc_nodes == 0:
        result["architecture"] = "all-AC"
    elif dc_nodes == len(feeder.nodes) - 1:
        result["architecture"] = "root-converted DC"
    else:
        result["architecture"] = "hybrid"
    return result


def solve_case(
    feeder: Feeder,
    native_dc: dict[int, float],
    params: Parameters,
    allow_dc: bool,
    optimize_conductor: bool,
) -> tuple[dict[int, str], dict[str, float | str]]:
    design = optimize_design(
        feeder, native_dc, params, allow_dc=allow_dc, optimize_conductor=optimize_conductor
    )
    result = evaluate(
        feeder,
        native_dc,
        params,
        design.assignment,
        optimize_conductor,
    )
    result["state_evaluations"] = float(design.state_evaluations)
    result["transition_evaluations"] = float(design.transition_evaluations)
    return design.assignment, result
