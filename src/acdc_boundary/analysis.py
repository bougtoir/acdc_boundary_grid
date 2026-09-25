from dataclasses import replace

import pandas as pd

from .data import load_feeder, native_dc_allocation
from .model import Parameters, solve_case


PAIRING_KEYS = [
    "feeder",
    "topology",
    "portfolio",
    "native_dc_share",
    "seed",
    "converter_efficiency",
]


def _percent_change(value: float, reference: float) -> float:
    return (value - reference) / reference * 100.0 if reference else 0.0


def feeder_attribution(scenarios: pd.DataFrame, config: dict) -> pd.DataFrame:
    central = scenarios[
        (scenarios.portfolio == "K3")
        & (scenarios.native_dc_share == 0.5)
        & (scenarios.seed == min(config["spatial_seeds"]))
        & (scenarios.converter_efficiency == 0.98)
    ].copy()
    rows = []
    for (feeder, topology), frame in central.groupby(["feeder", "topology"]):
        lookup = frame.set_index("case")
        inherited = float(lookup.at["all_ac_fixed", "total_loss_kwh"])
        ac_conductor = float(lookup.at["all_ac_conductor", "total_loss_kwh"])
        fixed_hybrid = float(lookup.at["hybrid_fixed", "total_loss_kwh"])
        joint_hybrid = float(lookup.at["hybrid_joint", "total_loss_kwh"])
        ideal_hybrid = float(lookup.at["hybrid_ideal", "total_loss_kwh"])
        rows.append(
            {
                "feeder": feeder,
                "topology": topology,
                "inherited_ac_loss_kwh": inherited,
                "conductor_optimized_ac_loss_kwh": ac_conductor,
                "fixed_conductor_hybrid_loss_kwh": fixed_hybrid,
                "joint_hybrid_loss_kwh": joint_hybrid,
                "electrical_ideal_hybrid_loss_kwh": ideal_hybrid,
                "conductor_contrast_pct": _percent_change(
                    ac_conductor,
                    inherited,
                ),
                "fixed_design_dc_permission_contrast_pct": _percent_change(
                    fixed_hybrid,
                    inherited,
                ),
                "joint_incremental_architecture_contrast_pct": _percent_change(
                    joint_hybrid,
                    ac_conductor,
                ),
                "ideal_conversion_upper_bound_contrast_pct": _percent_change(
                    ideal_hybrid,
                    ac_conductor,
                ),
                "joint_architecture": lookup.at["hybrid_joint", "architecture"],
                "joint_dc_bus_fraction": float(
                    lookup.at["hybrid_joint", "dc_node_fraction"]
                ),
                "joint_dc_energy_fraction": float(
                    lookup.at["hybrid_joint", "dc_energy_fraction"]
                ),
                "joint_boundary_count": int(
                    lookup.at["hybrid_joint", "converter_count"]
                ),
                "joint_boundary_signature": lookup.at[
                    "hybrid_joint", "boundary_signature"
                ],
                "joint_objective": float(lookup.at["hybrid_joint", "objective"]),
                "joint_material_index": float(
                    lookup.at["hybrid_joint", "material_index"]
                ),
                "joint_converter_capacity_kw": float(
                    lookup.at["hybrid_joint", "converter_capacity_kw"]
                ),
            }
        )
    result = pd.DataFrame(rows)
    original = (
        result[result.topology == "original"]
        .set_index("feeder")["joint_hybrid_loss_kwh"]
        .to_dict()
    )
    result["topology_sensitivity_vs_original_joint_pct"] = result.apply(
        lambda row: _percent_change(
            float(row.joint_hybrid_loss_kwh),
            float(original[row.feeder]),
        ),
        axis=1,
    )
    return result


def paired_joint_results(scenarios: pd.DataFrame) -> pd.DataFrame:
    joint = scenarios[scenarios.case == "hybrid_joint"].copy()
    ac = scenarios[scenarios.case == "all_ac_conductor"][
        PAIRING_KEYS + ["total_loss_kwh", "objective"]
    ].rename(
        columns={
            "total_loss_kwh": "ac_total_loss_kwh",
            "objective": "ac_objective",
        }
    )
    paired = joint.merge(ac, on=PAIRING_KEYS, validate="one_to_one")
    paired["loss_change_pct"] = (
        (paired.total_loss_kwh - paired.ac_total_loss_kwh)
        / paired.ac_total_loss_kwh
        * 100.0
    )
    paired["objective_change_pct"] = (
        (paired.objective - paired.ac_objective) / paired.ac_objective * 100.0
    )
    return paired


def factorial_summaries(
    scenarios: pd.DataFrame,
) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    paired = paired_joint_results(scenarios)
    grouping = [
        "feeder",
        "topology",
        "portfolio",
        "native_dc_share",
        "converter_efficiency",
    ]
    summary = paired.groupby(grouping, as_index=False).agg(
        spatial_allocations=("seed", "size"),
        all_ac_count=("architecture", lambda values: int((values == "all-AC").sum())),
        hybrid_count=("architecture", lambda values: int((values == "hybrid").sum())),
        root_dc_count=(
            "architecture",
            lambda values: int((values == "root-converted DC").sum()),
        ),
        mean_dc_bus_fraction=("dc_node_fraction", "mean"),
        mean_dc_energy_fraction=("dc_energy_fraction", "mean"),
        mean_loss_change_pct=("loss_change_pct", "mean"),
        median_loss_change_pct=("loss_change_pct", "median"),
        minimum_loss_change_pct=("loss_change_pct", "min"),
        maximum_loss_change_pct=("loss_change_pct", "max"),
        distinct_boundary_signatures=("boundary_signature", "nunique"),
    )
    for architecture in ("all_ac", "hybrid", "root_dc"):
        summary[f"{architecture}_pct"] = (
            summary[f"{architecture}_count"] / summary.spatial_allocations * 100.0
        )

    transition_rows = []
    transition_group = [
        "feeder",
        "topology",
        "portfolio",
        "seed",
        "converter_efficiency",
    ]
    for keys, frame in paired.groupby(transition_group):
        ordered = frame.sort_values("native_dc_share")
        non_ac = ordered[ordered.architecture != "all-AC"]
        root_dc = ordered[ordered.architecture == "root-converted DC"]
        transition_rows.append(
            {
                **dict(zip(transition_group, keys, strict=True)),
                "first_non_ac_native_dc_share": (
                    float(non_ac.native_dc_share.min()) if not non_ac.empty else float("nan")
                ),
                "first_root_dc_native_dc_share": (
                    float(root_dc.native_dc_share.min())
                    if not root_dc.empty
                    else float("nan")
                ),
                "architecture_sequence": "|".join(
                    f"{share:g}:{architecture}"
                    for share, architecture in zip(
                        ordered.native_dc_share,
                        ordered.architecture,
                        strict=True,
                    )
                ),
                "boundary_sequence": "|".join(
                    f"{share:g}:{signature or 'none'}"
                    for share, signature in zip(
                        ordered.native_dc_share,
                        ordered.boundary_signature,
                        strict=True,
                    )
                ),
            }
        )
    transitions = pd.DataFrame(transition_rows)

    outcome_columns = [
        "architecture",
        "dc_node_fraction",
        "dc_energy_fraction",
        "boundary_signature",
        "total_loss_kwh",
        "objective",
    ]
    duplicate_mask = paired.duplicated(
        [
            "feeder",
            "topology",
            "portfolio",
            "native_dc_share",
            "converter_efficiency",
            *outcome_columns,
        ],
        keep=False,
    )
    structure = pd.DataFrame(
        [
            {
                "total_result_rows": len(scenarios),
                "design_cases": scenarios.case.nunique(),
                "joint_optimization_rows": len(paired),
                "spatial_seed_values": paired.seed.nunique(),
                "joint_rows_in_repeated_outcome_groups": int(duplicate_mask.sum()),
                "joint_unique_outcome_rows_excluding_seed": int(
                    paired.drop_duplicates(
                        [
                            "feeder",
                            "topology",
                            "portfolio",
                            "native_dc_share",
                            "converter_efficiency",
                            *outcome_columns,
                        ]
                    ).shape[0]
                ),
                "interpretation": (
                    "Design-grid frequencies and frozen spatial allocations; "
                    "not independent real-world replications or probabilities."
                ),
            }
        ]
    )
    return summary, transitions, structure


def classify_model_discrepancy(
    scenarios: pd.DataFrame,
    validation: pd.DataFrame,
    numerical_tolerance_pct: float = 1e-9,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    paired = paired_joint_results(scenarios)
    threshold = validation[["feeder", "relative_error"]].copy()
    threshold["feeder_threshold_pct"] = threshold.relative_error.abs() * 100.0
    paired = paired.merge(
        threshold[["feeder", "feeder_threshold_pct"]],
        on="feeder",
        validate="many_to_one",
    )
    global_threshold = float(threshold.feeder_threshold_pct.max())
    paired["global_max_threshold_pct"] = global_threshold
    paired["double_feeder_threshold_pct"] = 2.0 * paired.feeder_threshold_pct

    def category(row: pd.Series, threshold_column: str) -> str:
        if (
            row.architecture == "all-AC"
            or row.loss_change_pct >= -numerical_tolerance_pct
        ):
            return "no modeled loss benefit/AC retained"
        if -row.loss_change_pct > row[threshold_column]:
            return "robustly material under screening rule"
        return "indeterminate relative to model discrepancy"

    paired["classification_feeder_threshold"] = paired.apply(
        category,
        axis=1,
        threshold_column="feeder_threshold_pct",
    )
    paired["classification_global_max_threshold"] = paired.apply(
        category,
        axis=1,
        threshold_column="global_max_threshold_pct",
    )
    paired["classification_double_feeder_threshold"] = paired.apply(
        category,
        axis=1,
        threshold_column="double_feeder_threshold_pct",
    )
    grouping = ["feeder", "topology", "portfolio"]
    counts = (
        paired.groupby(grouping + ["classification_feeder_threshold"])
        .size()
        .rename("cells")
        .reset_index()
    )
    totals = paired.groupby(grouping).size().rename("total_cells").reset_index()
    summary = counts.merge(totals, on=grouping, validate="many_to_one")
    summary["proportion"] = summary.cells / summary.total_cells
    return paired, summary


def _parameters(config: dict, portfolio: dict, efficiency: float) -> Parameters:
    return Parameters(
        ac_voltage_v=float(config["ac_voltage_line_line_v"]),
        dc_voltage_v=float(config["dc_voltage_pole_to_pole_v"]),
        power_factor=float(config["power_factor"]),
        endpoint_efficiency=float(config["endpoint_efficiency"]),
        boundary_efficiency=float(efficiency),
        standby_fraction=float(config["converter_standby_fraction"]),
        material_weight=float(config["material_weight"]),
        converter_capacity_weight=float(config["converter_capacity_weight"]),
        conductor_scales=tuple(
            float(value) for value in config["conductor_scale_options"]
        ),
        energy_factor=float(portfolio["annual_energy_factor"]),
        peak_factor=float(portfolio["peak_factor"]),
    )


def converter_ablations(config: dict) -> tuple[pd.DataFrame, pd.DataFrame]:
    specifications = {
        "baseline": {},
        "no_boundary_efficiency_loss": {"boundary_efficiency": 1.0},
        "no_standby_loss": {"standby_fraction": 0.0},
        "no_capacity_regularizer": {"converter_capacity_weight": 0.0},
        "no_endpoint_mismatch_loss": {"endpoint_efficiency": 1.0},
        "no_boundary_electrical_loss": {
            "boundary_efficiency": 1.0,
            "standby_fraction": 0.0,
        },
        "electrical_ideal_conversion": {
            "boundary_efficiency": 1.0,
            "endpoint_efficiency": 1.0,
            "standby_fraction": 0.0,
        },
        "full_ideal_converter": {
            "boundary_efficiency": 1.0,
            "endpoint_efficiency": 1.0,
            "standby_fraction": 0.0,
            "converter_capacity_weight": 0.0,
        },
    }
    rows = []
    for feeder_name, code in config["feeders"].items():
        for topology in config["topologies"]:
            feeder = load_feeder(feeder_name, code, topology)
            for portfolio_name, portfolio in config["portfolios"].items():
                for share in config["native_dc_shares"]:
                    for seed in config["spatial_seeds"]:
                        native_dc = native_dc_allocation(
                            feeder,
                            float(share),
                            int(seed),
                        )
                        for efficiency in config["converter_efficiencies"]:
                            base = _parameters(config, portfolio, float(efficiency))
                            for name, changes in specifications.items():
                                params = replace(base, **changes)
                                _, hybrid = solve_case(
                                    feeder,
                                    native_dc,
                                    params,
                                    allow_dc=True,
                                    optimize_conductor=True,
                                )
                                _, ac = solve_case(
                                    feeder,
                                    native_dc,
                                    params,
                                    allow_dc=False,
                                    optimize_conductor=True,
                                )
                                rows.append(
                                    {
                                        "feeder": feeder_name,
                                        "topology": topology,
                                        "portfolio": portfolio_name,
                                        "native_dc_share": float(share),
                                        "seed": int(seed),
                                        "converter_efficiency": float(efficiency),
                                        "ablation": name,
                                        **hybrid,
                                        "ac_total_loss_kwh": ac["total_loss_kwh"],
                                        "ac_objective": ac["objective"],
                                        "loss_change_pct": _percent_change(
                                            float(hybrid["total_loss_kwh"]),
                                            float(ac["total_loss_kwh"]),
                                        ),
                                    }
                                )
    detailed = pd.DataFrame(rows)
    baseline = detailed[detailed.ablation == "baseline"][
        PAIRING_KEYS
        + [
            "architecture",
            "boundary_signature",
            "converter_count",
            "dc_node_fraction",
            "dc_energy_fraction",
            "loss_change_pct",
        ]
    ].rename(
        columns={
            "architecture": "baseline_architecture",
            "boundary_signature": "baseline_boundary_signature",
            "converter_count": "baseline_converter_count",
            "dc_node_fraction": "baseline_dc_node_fraction",
            "dc_energy_fraction": "baseline_dc_energy_fraction",
            "loss_change_pct": "baseline_loss_change_pct",
        }
    )
    detailed = detailed.merge(baseline, on=PAIRING_KEYS, validate="many_to_one")
    detailed["architecture_changed_vs_baseline"] = (
        detailed.architecture != detailed.baseline_architecture
    )
    detailed["boundary_changed_vs_baseline"] = (
        detailed.boundary_signature != detailed.baseline_boundary_signature
    )
    detailed["converter_count_change_vs_baseline"] = (
        detailed.converter_count - detailed.baseline_converter_count
    )
    detailed["dc_bus_fraction_change_vs_baseline"] = (
        detailed.dc_node_fraction - detailed.baseline_dc_node_fraction
    )
    detailed["dc_energy_fraction_change_vs_baseline"] = (
        detailed.dc_energy_fraction - detailed.baseline_dc_energy_fraction
    )
    detailed["loss_contrast_change_pct_points_vs_baseline"] = (
        detailed.loss_change_pct - detailed.baseline_loss_change_pct
    )
    summary = detailed.groupby(
        ["ablation", "feeder", "topology", "portfolio"],
        as_index=False,
    ).agg(
        cells=("seed", "size"),
        all_ac_pct=("architecture", lambda values: (values == "all-AC").mean() * 100.0),
        hybrid_pct=("architecture", lambda values: (values == "hybrid").mean() * 100.0),
        root_dc_pct=(
            "architecture",
            lambda values: (values == "root-converted DC").mean() * 100.0,
        ),
        mean_dc_bus_fraction=("dc_node_fraction", "mean"),
        mean_dc_energy_fraction=("dc_energy_fraction", "mean"),
        mean_boundary_count=("converter_count", "mean"),
        mean_loss_change_pct=("loss_change_pct", "mean"),
        architecture_change_pct=(
            "architecture_changed_vs_baseline",
            lambda values: values.mean() * 100.0,
        ),
        boundary_change_pct=(
            "boundary_changed_vs_baseline",
            lambda values: values.mean() * 100.0,
        ),
        mean_loss_contrast_change_pct_points=(
            "loss_contrast_change_pct_points_vs_baseline",
            "mean",
        ),
    )
    return detailed, summary


def attribution_report(frame: pd.DataFrame) -> str:
    columns = [
        "feeder",
        "topology",
        "inherited_ac_loss_kwh",
        "conductor_optimized_ac_loss_kwh",
        "fixed_conductor_hybrid_loss_kwh",
        "joint_hybrid_loss_kwh",
        "conductor_contrast_pct",
        "fixed_design_dc_permission_contrast_pct",
        "joint_incremental_architecture_contrast_pct",
        "topology_sensitivity_vs_original_joint_pct",
    ]
    return "\n".join(
        [
            "# Feeder-Level Architecture Attribution",
            "",
            "Central conditions are K3, 50% native-DC annual energy, the first frozen",
            "spatial allocation, and 98% boundary efficiency. Values are modeled",
            "attribution contrasts, not causal or realized utility effects.",
            "",
            "```csv",
            frame[columns].to_csv(index=False).strip(),
            "```",
            "",
            "- Conductor contrast compares conductor-optimized AC with inherited AC.",
            "- Fixed-design DC-permission contrast compares fixed-conductor hybrid with",
            "  fixed-conductor AC on the same topology.",
            "- Joint incremental architecture contrast compares joint domain/conductor",
            "  optimization with conductor-optimized AC on the same topology.",
            "- Topology sensitivity compares a synthetic coordinate-based MST with the",
            "  original benchmark. It is not an observed infrastructure effect.",
            "",
        ]
    )


def factorial_report(
    scenarios: pd.DataFrame,
    summary: pd.DataFrame,
    structure: pd.DataFrame,
) -> str:
    joint = scenarios[scenarios.case == "hybrid_joint"]
    architectures = (
        joint.architecture.value_counts().reindex(
            ["all-AC", "hybrid", "root-converted DC"],
            fill_value=0,
        )
    )
    efficiency = (
        joint.groupby(["converter_efficiency", "architecture"])
        .size()
        .unstack(fill_value=0)
        .reset_index()
    )
    return "\n".join(
        [
            "# Full-Factorial Architecture Evidence",
            "",
            "```csv",
            structure.to_csv(index=False).strip(),
            "```",
            "",
            f"- Joint all-AC cells: {int(architectures['all-AC'])}/{len(joint)}.",
            f"- Joint hybrid cells: {int(architectures['hybrid'])}/{len(joint)}.",
            f"- Joint root-converted-DC cells: "
            f"{int(architectures['root-converted DC'])}/{len(joint)}.",
            "",
            "Architecture counts by boundary-efficiency grid:",
            "",
            "```csv",
            efficiency.to_csv(index=False).strip(),
            "```",
            "",
            f"The stratified machine-readable summary contains {len(summary)} rows.",
            "Frequencies are properties of the sampled design grid. Frozen spatial seeds",
            "are sensitivity allocations, not independent feeders or statistical",
            "replications. Repeated values at endpoint native-DC shares are structural.",
            "",
        ]
    )


def discrepancy_report(
    classified: pd.DataFrame,
    validation: pd.DataFrame,
) -> str:
    threshold = validation[["feeder", "relative_error"]].copy()
    threshold["threshold_pct"] = threshold.relative_error.abs() * 100.0
    lines = [
        "# Model-Discrepancy Screening Classification",
        "",
        "The validation discrepancy denominator is pandapower nonlinear AC line loss.",
        "The paired architecture contrast denominator is matched conductor-optimized",
        "AC total modeled electrical loss. Applying the validation percentage to the",
        "paired contrast is therefore a conservative screening heuristic, not a",
        "confidence interval or formal error propagation.",
        "",
        "```csv",
        threshold[["feeder", "threshold_pct"]].to_csv(index=False).strip(),
        "```",
        "",
    ]
    for column, label in (
        ("classification_feeder_threshold", "Feeder-specific threshold"),
        ("classification_global_max_threshold", "Global maximum threshold"),
        ("classification_double_feeder_threshold", "Twice feeder-specific threshold"),
    ):
        counts = classified[column].value_counts()
        lines.extend(
            [
                f"## {label}",
                "",
                "```csv",
                counts.rename_axis("classification").rename("cells").to_csv().strip(),
                "```",
                "",
            ]
        )
    lines.extend(
        [
            "Classification rule: an all-AC solution or nonnegative electrical-loss",
            "contrast is “no modeled loss benefit/AC retained”; a negative contrast",
            "whose magnitude exceeds the selected threshold is “robustly material under",
            "the screening rule”; remaining negative contrasts are indeterminate.",
            "",
        ]
    )
    return "\n".join(lines)


def ablation_report(detailed: pd.DataFrame) -> str:
    aggregate = detailed.groupby("ablation", as_index=False).agg(
        cells=("seed", "size"),
        all_ac_pct=("architecture", lambda values: (values == "all-AC").mean() * 100.0),
        hybrid_pct=("architecture", lambda values: (values == "hybrid").mean() * 100.0),
        root_dc_pct=(
            "architecture",
            lambda values: (values == "root-converted DC").mean() * 100.0,
        ),
        architecture_change_pct=(
            "architecture_changed_vs_baseline",
            lambda values: values.mean() * 100.0,
        ),
        boundary_change_pct=(
            "boundary_changed_vs_baseline",
            lambda values: values.mean() * 100.0,
        ),
        mean_dc_bus_fraction=("dc_node_fraction", "mean"),
        mean_loss_change_pct=("loss_change_pct", "mean"),
        mean_loss_contrast_change_pct_points=(
            "loss_contrast_change_pct_points_vs_baseline",
            "mean",
        ),
    )
    return "\n".join(
        [
            "# Converter-Component Ablations",
            "",
            "All ranges are dimensionless planning scenarios. They are not empirical",
            "vendor curves or equipment-cost estimates. Baseline comparison is matched",
            "within feeder, topology, portfolio, native-DC share, spatial seed, and",
            "nominal boundary-efficiency grid point.",
            "",
            "```csv",
            aggregate.to_csv(index=False).strip(),
            "```",
            "",
            "Boundary-efficiency loss, standby loss, capacity regularization, endpoint",
            "mismatch, aggregate boundary electrical loss, electrical-ideal conversion,",
            "and a full idealized converter are separated. High nominal efficiency alone",
            "does not establish adequate utilization; boundary changes remain conditioned",
            "on the spatially downstream energy and peak power.",
            "",
        ]
    )
