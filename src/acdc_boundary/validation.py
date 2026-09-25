import warnings

import pandapower as pp
import pandas as pd
import simbench as sb

from .data import load_feeder
from .paths import RESULTS


def _calculate_all_ac_stress(
    feeders: dict[str, str],
    power_factor: float,
    voltage: float,
    load_factors: dict[str, float],
) -> pd.DataFrame:
    rows = []
    for name, code in feeders.items():
        feeder = load_feeder(name, code)
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", FutureWarning)
            source_net = sb.get_simbench_net(code)
            profiles = sb.get_absolute_values(
                source_net, profiles_instead_of_study_cases=True
            )[("load", "p_mw")]
        timestamp = profiles.sum(axis=1).idxmax()
        node_power_kw = {node: 0.0 for node in feeder.nodes}
        for load_index, load in source_net.load.iterrows():
            bus = int(load.bus)
            if bus in node_power_kw and load_index in profiles.columns:
                node_power_kw[bus] += float(profiles.at[timestamp, load_index] * 1000.0)
        for stress_case, load_factor in load_factors.items():
            net = pp.create_empty_network(sn_mva=1.0)
            buses = {
                node: pp.create_bus(net, vn_kv=voltage / 1000.0, name=f"bus-{node}")
                for node in feeder.nodes
            }
            pp.create_ext_grid(net, buses[feeder.root], vm_pu=1.0)
            for edge in feeder.edges.values():
                pp.create_line_from_parameters(
                    net,
                    buses[edge.parent],
                    buses[edge.child],
                    length_km=edge.length_km,
                    r_ohm_per_km=edge.r_ohm_per_km,
                    x_ohm_per_km=edge.x_ohm_per_km,
                    c_nf_per_km=0.0,
                    max_i_ka=edge.max_i_a / 1000.0,
                )
            reactive_ratio = (1.0 / power_factor**2 - 1.0) ** 0.5
            for node in feeder.nodes:
                peak_mw = node_power_kw[node] * load_factor / 1000.0
                if peak_mw > 0:
                    pp.create_load(
                        net,
                        buses[node],
                        p_mw=peak_mw,
                        q_mvar=peak_mw * reactive_ratio,
                    )
            with warnings.catch_warnings():
                warnings.simplefilter("ignore")
                pp.runpp(net, calculate_voltage_angles=False, numba=False)
            pandapower_loss_kw = float(net.res_line.pl_mw.sum() * 1000.0)
            approximate = 0.0
            for edge in feeder.edges.values():
                descendants = [edge.child]
                cursor = 0
                while cursor < len(descendants):
                    descendants.extend(feeder.children[descendants[cursor]])
                    cursor += 1
                downstream_kw = (
                    sum(node_power_kw[node] for node in descendants) * load_factor
                )
                resistance = edge.r_ohm_per_km * edge.length_km
                current = (
                    downstream_kw
                    * 1000.0
                    / (3.0**0.5 * voltage * power_factor)
                )
                approximate += 3.0 * current * current * resistance / 1000.0
            rows.append(
                {
                    "feeder": name,
                    "stress_case": stress_case,
                    "load_factor": load_factor,
                    "pandapower_loss_kw": pandapower_loss_kw,
                    "approximate_loss_kw": approximate,
                    "relative_error": (
                        abs(approximate - pandapower_loss_kw) / pandapower_loss_kw
                        if pandapower_loss_kw
                        else 0.0
                    ),
                    "minimum_voltage_pu": float(net.res_bus.vm_pu.min()),
                    "maximum_line_loading_pct": float(net.res_line.loading_percent.max()),
                    "pandapower_converged": bool(net.converged),
                }
            )
    return pd.DataFrame(rows)


def validate_all_ac_stress(
    feeders: dict[str, str],
    power_factor: float,
    voltage: float,
    load_factors: dict[str, float],
) -> pd.DataFrame:
    result = _calculate_all_ac_stress(
        feeders,
        power_factor,
        voltage,
        load_factors,
    )
    RESULTS.mkdir(parents=True, exist_ok=True)
    result.to_csv(RESULTS / "validation_stress_results.csv", index=False)
    return result


def validate_all_ac(feeders: dict[str, str], power_factor: float, voltage: float) -> pd.DataFrame:
    stress = _calculate_all_ac_stress(
        feeders,
        power_factor,
        voltage,
        {"benchmark_peak": 1.0},
    )
    result = stress.drop(columns=["stress_case", "load_factor"]).copy()
    result.to_csv(RESULTS / "validation_results.csv", index=False)
    return result


def feeder_counts(feeders: dict[str, str]) -> pd.DataFrame:
    rows = []
    for name, code in feeders.items():
        feeder = load_feeder(name, code)
        rows.append({"feeder": name, "nodes": len(feeder.nodes), "edges": len(feeder.edges)})
    return pd.DataFrame(rows)


def validation_stress_report(frame: pd.DataFrame) -> str:
    maximum_error = float(frame.relative_error.max() * 100.0)
    return "\n".join(
        [
            "# Nonlinear All-AC Validation Stress Check",
            "",
            "```csv",
            frame.to_csv(index=False).strip(),
            "```",
            "",
            f"All {len(frame)} feeder/portfolio peak-factor cases converged. The maximum",
            f"absolute relative line-loss discrepancy was {maximum_error:.3f}%.",
            "This technically valid stress check scales the same balanced load snapshot",
            "used by both models. It does not validate hybrid AC/DC operation, converter",
            "controls, unbalance, harmonics, grounding, or protection. No hybrid OPF was",
            "added because no independently validated implementation is available here.",
            "",
        ]
    )
