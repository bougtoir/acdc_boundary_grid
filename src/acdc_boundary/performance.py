import importlib.metadata
import os
import platform
import resource
import sys
import time
from pathlib import Path

import pandas as pd

from .data import Edge, Feeder, load_feeder, native_dc_allocation
from .exactness import ToyCase, enumerate_solutions
from .model import Parameters, optimize_design, solve_case


def _parameters(config: dict, portfolio: dict, efficiency: float) -> Parameters:
    return Parameters(
        ac_voltage_v=float(config["ac_voltage_line_line_v"]),
        dc_voltage_v=float(config["dc_voltage_pole_to_pole_v"]),
        power_factor=float(config["power_factor"]),
        endpoint_efficiency=float(config["endpoint_efficiency"]),
        boundary_efficiency=efficiency,
        standby_fraction=float(config["converter_standby_fraction"]),
        material_weight=float(config["material_weight"]),
        converter_capacity_weight=float(config["converter_capacity_weight"]),
        conductor_scales=tuple(
            float(value) for value in config["conductor_scale_options"]
        ),
        energy_factor=float(portfolio["annual_energy_factor"]),
        peak_factor=float(portfolio["peak_factor"]),
    )


def feeder_runtime_benchmark(config: dict, repeats: int = 30) -> pd.DataFrame:
    rows = []
    portfolio = config["portfolios"]["K3"]
    params = _parameters(config, portfolio, 0.98)
    seed = min(config["spatial_seeds"])
    for feeder_name, code in config["feeders"].items():
        for topology in config["topologies"]:
            feeder = load_feeder(feeder_name, code, topology)
            native_dc = native_dc_allocation(feeder, 0.5, seed)
            solve_case(
                feeder,
                native_dc,
                params,
                allow_dc=True,
                optimize_conductor=True,
            )
            timings = []
            latest = None
            for _ in range(repeats):
                start = time.perf_counter()
                _, latest = solve_case(
                    feeder,
                    native_dc,
                    params,
                    allow_dc=True,
                    optimize_conductor=True,
                )
                timings.append((time.perf_counter() - start) * 1000.0)
            timing = pd.Series(timings)
            rows.append(
                {
                    "feeder": feeder_name,
                    "topology": topology,
                    "nodes": len(feeder.nodes),
                    "edges": len(feeder.edges),
                    "repeats": repeats,
                    "median_runtime_ms": float(timing.median()),
                    "minimum_runtime_ms": float(timing.min()),
                    "maximum_runtime_ms": float(timing.max()),
                    "state_evaluations": int(float(latest["state_evaluations"])),
                    "transition_evaluations": int(
                        float(latest["transition_evaluations"])
                    ),
                }
            )
    return pd.DataFrame(rows)


def _chain_case(nodes: int) -> ToyCase:
    node_ids = tuple(range(nodes))
    children = {
        node: ((node + 1,) if node < nodes - 1 else ())
        for node in node_ids
    }
    edges = {}
    for parent in range(nodes - 1):
        child = parent + 1
        downstream_nodes = nodes - child
        edges[(parent, child)] = Edge(
            parent=parent,
            child=child,
            length_km=0.1,
            r_ohm_per_km=0.3,
            max_i_a=200.0,
            downstream_energy_kwh=1000.0 * downstream_nodes,
            downstream_peak_kw=2.0 * downstream_nodes,
            loss_hours=1000.0,
        )
    feeder = Feeder(
        name=f"chain-{nodes}",
        code="toy",
        topology="enumerated",
        root=0,
        nodes=node_ids,
        children=children,
        node_energy_kwh={node: (0.0 if node == 0 else 1000.0) for node in node_ids},
        node_peak_kw={node: (0.0 if node == 0 else 2.0) for node in node_ids},
        coordinates={node: (0.0, float(node)) for node in node_ids},
        edges=edges,
    )
    params = Parameters(
        ac_voltage_v=400.0,
        dc_voltage_v=750.0,
        power_factor=0.95,
        endpoint_efficiency=0.90,
        boundary_efficiency=0.96,
        standby_fraction=0.001,
        material_weight=3.0,
        converter_capacity_weight=2.0,
        conductor_scales=(1.0, 2.0),
        energy_factor=1.0,
        peak_factor=1.0,
    )
    native_dc = {
        node: (0.0 if node == 0 else float(node % 2))
        for node in node_ids
    }
    return ToyCase(
        name=f"chain_{nodes}",
        feeder=feeder,
        native_dc=native_dc,
        params=params,
        optimize_conductor=True,
        expected_architecture="not-predeclared",
    )


def toy_scaling_benchmark(min_nodes: int = 2, max_nodes: int = 8) -> pd.DataFrame:
    rows = []
    for nodes in range(min_nodes, max_nodes + 1):
        case = _chain_case(nodes)
        start = time.perf_counter()
        design = optimize_design(
            case.feeder,
            case.native_dc,
            case.params,
            allow_dc=True,
            optimize_conductor=True,
        )
        dp_runtime_ms = (time.perf_counter() - start) * 1000.0
        start = time.perf_counter()
        enumerated = enumerate_solutions(case)
        brute_runtime_ms = (time.perf_counter() - start) * 1000.0
        brute_objective = min(solution.objective for solution in enumerated)
        rows.append(
            {
                "nodes": nodes,
                "edges": nodes - 1,
                "enumerated_designs": len(enumerated),
                "dp_state_evaluations": design.state_evaluations,
                "dp_transition_evaluations": design.transition_evaluations,
                "dp_runtime_ms": dp_runtime_ms,
                "brute_force_runtime_ms": brute_runtime_ms,
                "objective_absolute_error": abs(design.objective - brute_objective),
            }
        )
    return pd.DataFrame(rows)


def _linux_value(path: str, prefix: str) -> str:
    source = Path(path)
    if not source.exists():
        return "unavailable"
    for line in source.read_text(encoding="utf-8", errors="replace").splitlines():
        if line.startswith(prefix):
            return line.split(":", maxsplit=1)[-1].strip()
    return "unavailable"


def environment_record(
    scenario_runtime_s: float,
    ablation_runtime_s: float,
    elapsed_pipeline_s: float,
) -> pd.DataFrame:
    packages = (
        "numpy",
        "pandas",
        "networkx",
        "pandapower",
        "simbench",
        "python-docx",
        "matplotlib",
    )
    versions = []
    for package in packages:
        try:
            version = importlib.metadata.version(package)
        except importlib.metadata.PackageNotFoundError:
            version = "not-installed"
        versions.append(f"{package}={version}")
    peak_rss = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
    peak_rss_mb = peak_rss / 1024.0 if platform.system() == "Linux" else peak_rss / 1048576.0
    return pd.DataFrame(
        [
            {
                "platform": platform.platform(),
                "python": sys.version.split()[0],
                "processor": _linux_value("/proc/cpuinfo", "model name"),
                "logical_cpus": os.cpu_count() or 0,
                "memory_total": _linux_value("/proc/meminfo", "MemTotal"),
                "peak_process_rss_mb": peak_rss_mb,
                "software_versions": ";".join(versions),
                "factorial_scenario_runtime_s": scenario_runtime_s,
                "converter_ablation_runtime_s": ablation_runtime_s,
                "pipeline_elapsed_before_document_build_s": elapsed_pipeline_s,
            }
        ]
    )


def performance_report(
    environment: pd.DataFrame,
    feeder_benchmark: pd.DataFrame,
    toy_benchmark: pd.DataFrame,
) -> str:
    return "\n".join(
        [
            "# Computational Performance",
            "",
            "## Environment and total runs",
            "",
            "```csv",
            environment.to_csv(index=False).strip(),
            "```",
            "",
            "## Representative full-feeder solves",
            "",
            "```csv",
            feeder_benchmark.to_csv(index=False).strip(),
            "```",
            "",
            "## Independently enumerated toy scaling",
            "",
            "```csv",
            toy_benchmark.to_csv(index=False).strip(),
            "```",
            "",
            "The analytical DP work is O(|E||D|^2|S|), with |D| at most two and",
            "|S| at most three. Brute-force enumeration grows with every combined",
            "domain/conductor design. Timing illustrates this declared implementation",
            "on one VM; it is not used as an independent proof of asymptotic complexity.",
            "",
        ]
    )
