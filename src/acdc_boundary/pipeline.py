import re
import shutil
import subprocess
import time
import zipfile
from dataclasses import replace
from pathlib import Path

import pandas as pd
import yaml

from .acquire import main as acquire
from .analysis import (
    ablation_report,
    attribution_report,
    classify_model_discrepancy,
    converter_ablations,
    discrepancy_report,
    factorial_report,
    factorial_summaries,
    feeder_attribution,
    paired_joint_results,
)
from .data import ev_data_summary, export_feeder, load_feeder, native_dc_allocation
from .exactness import exactness_report, require_exactness, validate_toy_cases
from .figures import build_all
from .manuscript import (
    build_cover_letter,
    build_manuscript,
    build_submission_documents,
    write_result_manifest,
)
from .model import Parameters, solve_case
from .paths import (
    CONFIGS,
    FIGURES,
    MANUSCRIPT,
    QC,
    REPORTS,
    RESULTS,
    ROOT,
    SUBMISSION,
    TABLES,
)
from .performance import (
    environment_record,
    feeder_runtime_benchmark,
    performance_report,
    toy_scaling_benchmark,
)
from .validation import (
    validate_all_ac,
    validate_all_ac_stress,
    validation_stress_report,
)


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
        conductor_scales=tuple(float(value) for value in config["conductor_scale_options"]),
        energy_factor=float(portfolio["annual_energy_factor"]),
        peak_factor=float(portfolio["peak_factor"]),
    )


def _run_scenarios(config: dict) -> pd.DataFrame:
    rows = []
    cases = {
        "all_ac_fixed": (False, False, False),
        "all_ac_conductor": (False, True, False),
        "hybrid_fixed": (True, False, False),
        "hybrid_joint": (True, True, False),
        "hybrid_ideal": (True, True, True),
    }
    feeder_objects = {}
    for feeder_name, code in config["feeders"].items():
        for topology in config["topologies"]:
            feeder = load_feeder(feeder_name, code, topology)
            export_feeder(feeder)
            feeder_objects[(feeder_name, topology)] = feeder
    for (feeder_name, topology), feeder in feeder_objects.items():
        for portfolio_name, portfolio in config["portfolios"].items():
            for share in config["native_dc_shares"]:
                for seed in config["spatial_seeds"]:
                    native_dc = native_dc_allocation(feeder, float(share), int(seed))
                    for efficiency in config["converter_efficiencies"]:
                        base_params = _parameters(config, portfolio, float(efficiency))
                        for case, (allow_dc, optimize_conductor, ideal) in cases.items():
                            params = (
                                replace(
                                    base_params,
                                    boundary_efficiency=1.0,
                                    endpoint_efficiency=1.0,
                                    standby_fraction=0.0,
                                )
                                if ideal
                                else base_params
                            )
                            _, result = solve_case(
                                feeder,
                                native_dc,
                                params,
                                allow_dc=allow_dc,
                                optimize_conductor=optimize_conductor,
                            )
                            rows.append(
                                {
                                    "feeder": feeder_name,
                                    "topology": topology,
                                    "portfolio": portfolio_name,
                                    "native_dc_share": float(share),
                                    "seed": int(seed),
                                    "converter_efficiency": float(efficiency),
                                    "case": case,
                                    **result,
                                }
                            )
    return pd.DataFrame(rows)


def _novelty_matrix() -> pd.DataFrame:
    rows = [
        ["Ahmed et al. (2016)", "10.1109/TSG.2016.2608508", 1, 1, 1, 0, 0, 0, 0],
        ["Lotfi and Khodaei (2017)", "10.1016/j.energy.2016.12.015", 1, 1, 1, 0, 1, 1, 0],
        ["Wu et al. (2019)", "10.3390/en12091751", 1, 1, 1, 0, 1, 0, 0],
        ["Zhang et al. (2022)", "10.1109/TSG.2021.3102615", 1, 1, 1, 0, 1, 0, 1],
        ["de Barros et al. (2023)", "10.1109/TPWRD.2023.3277089", 1, 1, 1, 1, 0, 0, 0],
        ["Wang et al. (2022)", "10.1016/j.apenergy.2022.119438", 1, 1, 1, 1, 1, 0, 1],
        ["This study", "", 1, 1, 1, 1, 1, 1, 1],
    ]
    return pd.DataFrame(
        rows,
        columns=[
            "study",
            "doi",
            "endogenous_ac_dc",
            "converter_placement",
            "topology",
            "conductor_design",
            "temporal_der",
            "matched_attribution",
            "transition_map",
        ],
    )


def _constraint_violation_count(joint: pd.DataFrame, config: dict) -> int:
    ampacity_limit = float(config["ampacity_limit_fraction"])
    voltage_drop_limit = float(config["voltage_drop_limit_pu"])
    return int(
        (
            (joint.max_ampacity_fraction > ampacity_limit)
            | (joint.max_single_edge_drop_pu > voltage_drop_limit)
        ).sum()
    )


def _manuscript_values(
    scenarios: pd.DataFrame,
    central: pd.DataFrame,
    validation: pd.DataFrame,
    config: dict,
    attribution: pd.DataFrame,
    validation_stress: pd.DataFrame,
    exactness: pd.DataFrame,
    discrepancy: pd.DataFrame,
    ablations: pd.DataFrame,
    feeder_performance: pd.DataFrame,
    toy_performance: pd.DataFrame,
    environment: pd.DataFrame,
    factorial_structure: pd.DataFrame,
) -> pd.DataFrame:
    pivot = central.pivot(index="feeder", columns="case", values="total_loss_kwh")
    conductor_effect = (
        (pivot["all_ac_conductor"] - pivot["all_ac_fixed"]) / pivot["all_ac_fixed"] * 100.0
    )
    hybrid_effect = (
        (pivot["hybrid_joint"] - pivot["all_ac_conductor"])
        / pivot["all_ac_conductor"]
        * 100.0
    )
    architectures = central[central.case == "hybrid_joint"].set_index("feeder").architecture
    summary = "; ".join(f"{name}: {value}" for name, value in architectures.items())
    key = [
        "feeder",
        "topology",
        "portfolio",
        "native_dc_share",
        "seed",
        "converter_efficiency",
    ]
    joint = scenarios[scenarios.case == "hybrid_joint"].copy()
    ac = scenarios[scenarios.case == "all_ac_conductor"][key + ["total_loss_kwh"]].rename(
        columns={"total_loss_kwh": "ac_total_loss_kwh"}
    )
    paired = joint.merge(ac, on=key, validate="one_to_one")
    paired["loss_change_pct"] = (
        (paired.total_loss_kwh - paired.ac_total_loss_kwh)
        / paired.ac_total_loss_kwh
        * 100.0
    )
    architecture_counts = joint.architecture.value_counts(normalize=True)
    rows = [
        {
            "value_id": "mean_conductor_effect_pct",
            "value": float(conductor_effect.mean()),
            "units": "%",
            "scenario": "central/original/K3/share0.5/seed20260924/eta0.98",
            "uncertainty": "range across three feeders",
            "source_file": "results/central_decomposition.csv",
            "generator": "acdc_boundary.pipeline._manuscript_values",
        },
        {
            "value_id": "mean_hybrid_vs_ac_loss_change_pct",
            "value": float(hybrid_effect.mean()),
            "units": "%",
            "scenario": "central/original/K3/share0.5/seed20260924/eta0.98",
            "uncertainty": "range across three feeders",
            "source_file": "results/central_decomposition.csv",
            "generator": "acdc_boundary.pipeline._manuscript_values",
        },
        {
            "value_id": "central_architecture_summary",
            "value": summary,
            "units": "text",
            "scenario": "central/original/K3/share0.5/seed20260924/eta0.98",
            "uncertainty": "not applicable",
            "source_file": "results/central_decomposition.csv",
            "generator": "acdc_boundary.pipeline._manuscript_values",
        },
        {
            "value_id": "median_validation_error_pct",
            "value": float(validation.relative_error.median() * 100.0),
            "units": "%",
            "scenario": "SimBench benchmark operating point",
            "uncertainty": "range across three feeders",
            "source_file": "results/validation_results.csv",
            "generator": "acdc_boundary.validation.validate_all_ac",
        },
        {
            "value_id": "scenario_cell_count",
            "value": int(len(scenarios)),
            "units": "rows",
            "scenario": "full factorial",
            "uncertainty": "not applicable",
            "source_file": "results/scenario_results.csv",
            "generator": "acdc_boundary.pipeline._run_scenarios",
        },
        {
            "value_id": "joint_hybrid_selected_pct",
            "value": float(architecture_counts.get("hybrid", 0.0) * 100.0),
            "units": "%",
            "scenario": "all hybrid-joint cells",
            "uncertainty": "descriptive across factorial cells",
            "source_file": "results/phase_diagram.csv",
            "generator": "acdc_boundary.pipeline._manuscript_values",
        },
        {
            "value_id": "joint_all_ac_selected_pct",
            "value": float(architecture_counts.get("all-AC", 0.0) * 100.0),
            "units": "%",
            "scenario": "all hybrid-joint cells",
            "uncertainty": "descriptive across factorial cells",
            "source_file": "results/phase_diagram.csv",
            "generator": "acdc_boundary.pipeline._manuscript_values",
        },
        {
            "value_id": "joint_root_dc_selected_pct",
            "value": float(architecture_counts.get("root-converted DC", 0.0) * 100.0),
            "units": "%",
            "scenario": "all hybrid-joint cells",
            "uncertainty": "descriptive across factorial cells",
            "source_file": "results/phase_diagram.csv",
            "generator": "acdc_boundary.pipeline._manuscript_values",
        },
        {
            "value_id": "paired_loss_change_median_pct",
            "value": float(paired.loss_change_pct.median()),
            "units": "%",
            "scenario": "hybrid-joint versus conductor-optimized AC, all cells",
            "uncertainty": "factorial distribution",
            "source_file": "results/uncertainty_summary.csv",
            "generator": "acdc_boundary.pipeline._manuscript_values",
        },
        {
            "value_id": "paired_loss_change_q05_pct",
            "value": float(paired.loss_change_pct.quantile(0.05)),
            "units": "%",
            "scenario": "hybrid-joint versus conductor-optimized AC, all cells",
            "uncertainty": "5th percentile",
            "source_file": "results/uncertainty_summary.csv",
            "generator": "acdc_boundary.pipeline._manuscript_values",
        },
        {
            "value_id": "paired_loss_change_q95_pct",
            "value": float(paired.loss_change_pct.quantile(0.95)),
            "units": "%",
            "scenario": "hybrid-joint versus conductor-optimized AC, all cells",
            "uncertainty": "95th percentile",
            "source_file": "results/uncertainty_summary.csv",
            "generator": "acdc_boundary.pipeline._manuscript_values",
        },
        {
            "value_id": "constraint_violation_cells",
            "value": _constraint_violation_count(joint, config),
            "units": "cells",
            "scenario": "all hybrid-joint cells",
            "uncertainty": "screening diagnostic",
            "source_file": "results/phase_diagram.csv",
            "generator": "acdc_boundary.pipeline._manuscript_values",
        },
    ]
    common_generator = "acdc_boundary.pipeline._manuscript_values"

    def add(
        value_id: str,
        value: float | int | str,
        units: str,
        scenario: str,
        source_file: str,
        uncertainty: str = "not applicable",
        generator: str = common_generator,
    ) -> None:
        rows.append(
            {
                "value_id": value_id,
                "value": value,
                "units": units,
                "scenario": scenario,
                "uncertainty": uncertainty,
                "source_file": source_file,
                "generator": generator,
            }
        )

    add(
        "joint_cell_count",
        len(joint),
        "cells",
        "all joint-optimization cells",
        "results/phase_diagram.csv",
    )
    for dimension, denominator in (
        ("efficiency", joint.converter_efficiency.nunique()),
        ("native_share", joint.native_dc_share.nunique()),
        ("feeder", joint.feeder.nunique()),
    ):
        add(
            f"joint_cells_per_{dimension}",
            len(joint) // int(denominator),
            "cells",
            f"balanced joint grid per {dimension}",
            "results/phase_diagram.csv",
            "deterministic factorial cell count",
        )
    for architecture, identifier in (
        ("all-AC", "joint_all_ac_selected_cells"),
        ("hybrid", "joint_hybrid_selected_cells"),
        ("root-converted DC", "joint_root_dc_selected_cells"),
    ):
        add(
            identifier,
            int((joint.architecture == architecture).sum()),
            "cells",
            "all joint-optimization cells",
            "results/phase_diagram.csv",
        )
    for efficiency in sorted(joint.converter_efficiency.unique()):
        efficiency_rows = joint[joint.converter_efficiency == efficiency]
        efficiency_id = f"{int(round(float(efficiency) * 100.0))}"
        for architecture, identifier in (
            ("all-AC", "all_ac"),
            ("hybrid", "hybrid"),
            ("root-converted DC", "root_dc"),
        ):
            add(
                f"joint_efficiency_{efficiency_id}_{identifier}_cells",
                int((efficiency_rows.architecture == architecture).sum()),
                "cells",
                f"joint cells at {float(efficiency) * 100.0:.0f}% boundary efficiency",
                "results/phase_diagram.csv",
                "descriptive scenario-grid count",
            )
    for native_share in sorted(joint.native_dc_share.unique()):
        native_rows = joint[joint.native_dc_share == native_share]
        native_share_id = f"{int(round(float(native_share) * 100.0))}"
        for architecture, identifier in (
            ("all-AC", "all_ac"),
            ("hybrid", "hybrid"),
            ("root-converted DC", "root_dc"),
        ):
            add(
                f"joint_native_share_{native_share_id}_{identifier}_cells",
                int((native_rows.architecture == architecture).sum()),
                "cells",
                f"joint cells at {float(native_share) * 100.0:.0f}% native-DC annual energy",
                "results/phase_diagram.csv",
                "descriptive scenario-grid count",
            )
    structure = factorial_structure.iloc[0]
    add(
        "joint_repeated_outcome_group_rows",
        int(structure.joint_rows_in_repeated_outcome_groups),
        "rows",
        "joint outcome signatures excluding spatial seed",
        "results/factorial_structure.csv",
    )
    add(
        "joint_unique_outcome_rows_excluding_seed",
        int(structure.joint_unique_outcome_rows_excluding_seed),
        "rows",
        "joint outcome signatures excluding spatial seed",
        "results/factorial_structure.csv",
    )
    add(
        "design_case_count",
        int(structure.design_cases),
        "design cells",
        "nested attribution design",
        "results/factorial_structure.csv",
        "declared design-cell count",
    )
    for key, units in (
        ("ac_voltage_line_line_v", "V"),
        ("dc_voltage_pole_to_pole_v", "V"),
        ("power_factor", "p.u."),
        ("endpoint_efficiency", "p.u."),
        ("converter_standby_fraction", "fraction of rated power"),
        ("material_weight", "normalized objective weight"),
        ("converter_capacity_weight", "normalized objective weight"),
        ("ampacity_limit_fraction", "p.u."),
        ("voltage_drop_limit_pu", "p.u."),
    ):
        add(
            f"config_{key}",
            float(config[key]),
            units,
            "frozen analysis configuration",
            "configs/analysis_plan.yaml",
        )
    for key, values in (
        ("feeders", config["feeders"]),
        ("topologies", config["topologies"]),
        ("portfolios", config["portfolios"]),
        ("native_dc_shares", config["native_dc_shares"]),
        ("spatial_seeds", config["spatial_seeds"]),
        ("converter_efficiencies", config["converter_efficiencies"]),
        ("conductor_scale_options", config["conductor_scale_options"]),
    ):
        add(
            f"config_{key}_count",
            len(values),
            "count",
            "frozen analysis configuration",
            "configs/analysis_plan.yaml",
        )
    add(
        "central_native_dc_share_pct",
        float(config["native_dc_shares"][2]) * 100.0,
        "%",
        "central setting",
        "configs/analysis_plan.yaml",
    )
    add(
        "central_boundary_efficiency_pct",
        float(config["converter_efficiencies"][2]) * 100.0,
        "%",
        "central setting",
        "configs/analysis_plan.yaml",
    )
    add(
        "central_spatial_seed",
        int(min(config["spatial_seeds"])),
        "seed",
        "central setting",
        "configs/analysis_plan.yaml",
    )
    for row in attribution.to_dict(orient="records"):
        prefix = f"central_{row['feeder']}_{row['topology']}"
        for column, units in (
            ("inherited_ac_loss_kwh", "kWh/year"),
            ("conductor_optimized_ac_loss_kwh", "kWh/year"),
            ("fixed_conductor_hybrid_loss_kwh", "kWh/year"),
            ("joint_hybrid_loss_kwh", "kWh/year"),
            ("electrical_ideal_hybrid_loss_kwh", "kWh/year"),
            ("conductor_contrast_pct", "%"),
            ("fixed_design_dc_permission_contrast_pct", "%"),
            ("joint_incremental_architecture_contrast_pct", "%"),
            ("ideal_conversion_upper_bound_contrast_pct", "%"),
            ("topology_sensitivity_vs_original_joint_pct", "%"),
            ("joint_dc_bus_fraction", "fraction"),
            ("joint_dc_energy_fraction", "fraction"),
            ("joint_boundary_count", "count"),
        ):
            add(
                f"{prefix}_{column}",
                float(row[column]),
                units,
                "central matched attribution cell",
                "results/feeder_attribution.csv",
                "descriptive modeled contrast",
            )
        add(
            f"{prefix}_joint_architecture",
            str(row["joint_architecture"]),
            "text",
            "central matched attribution cell",
            "results/feeder_attribution.csv",
        )
    add(
        "maximum_validation_error_pct",
        float(validation.relative_error.max() * 100.0),
        "%",
        "SimBench benchmark operating point",
        "results/validation_results.csv",
        "range across three feeders",
    )
    for row in validation.itertuples():
        add(
            f"validation_{row.feeder}_relative_error_pct",
            float(row.relative_error * 100.0),
            "%",
            "SimBench benchmark operating point",
            "results/validation_results.csv",
        )
    add(
        "validation_stress_case_count",
        len(validation_stress),
        "cases",
        "configured portfolio peak multipliers",
        "results/validation_stress_results.csv",
    )
    add(
        "validation_stress_max_error_pct",
        float(validation_stress.relative_error.max() * 100.0),
        "%",
        "configured portfolio peak multipliers",
        "results/validation_stress_results.csv",
    )
    add(
        "validation_stress_min_voltage_pu",
        float(validation_stress.minimum_voltage_pu.min()),
        "p.u.",
        "configured portfolio peak multipliers",
        "results/validation_stress_results.csv",
    )
    add(
        "validation_stress_max_loading_pct",
        float(validation_stress.maximum_line_loading_pct.max()),
        "%",
        "configured portfolio peak multipliers",
        "results/validation_stress_results.csv",
    )
    add(
        "dp_exactness_case_count",
        len(exactness),
        "cases",
        "independently enumerated toy networks",
        "results/dp_exactness_validation.csv",
    )
    add(
        "dp_exactness_max_objective_error",
        float(exactness.absolute_objective_error.max()),
        "normalized objective units",
        "independently enumerated toy networks",
        "results/dp_exactness_validation.csv",
    )
    add(
        "dp_exactness_tied_case_count",
        int((exactness.brute_force_optimum_count > 1).sum()),
        "cases",
        "independently enumerated toy networks",
        "results/dp_exactness_validation.csv",
    )
    for column, rule_id in (
        ("classification_feeder_threshold", "feeder"),
        ("classification_global_max_threshold", "global_max"),
        ("classification_double_feeder_threshold", "double_feeder"),
    ):
        counts = discrepancy[column].value_counts()
        for category, identifier in (
            ("no modeled loss benefit/AC retained", "no_benefit"),
            ("robustly material under screening rule", "robust"),
            ("indeterminate relative to model discrepancy", "indeterminate"),
        ):
            add(
                f"discrepancy_{rule_id}_{identifier}_cells",
                int(counts.get(category, 0)),
                "cells",
                f"{rule_id} discrepancy screening rule",
                "results/model_discrepancy_classification.csv",
            )
    for feeder, feeder_rows in discrepancy.groupby("feeder"):
        counts = feeder_rows.classification_feeder_threshold.value_counts()
        for category, identifier in (
            ("no modeled loss benefit/AC retained", "no_benefit"),
            ("robustly material under screening rule", "robust"),
            ("indeterminate relative to model discrepancy", "indeterminate"),
        ):
            add(
                f"discrepancy_feeder_rule_{feeder}_{identifier}_cells",
                int(counts.get(category, 0)),
                "cells",
                f"{feeder} joint cells under the feeder-specific rule",
                "results/model_discrepancy_classification.csv",
                "descriptive scenario-grid count",
            )
    aggregate_ablations = ablations.groupby("ablation", as_index=False).agg(
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
    )
    for row in aggregate_ablations.to_dict(orient="records"):
        for column, units in (
            ("all_ac_pct", "%"),
            ("hybrid_pct", "%"),
            ("root_dc_pct", "%"),
            ("architecture_change_pct", "%"),
            ("boundary_change_pct", "%"),
            ("mean_dc_bus_fraction", "fraction"),
            ("mean_loss_change_pct", "%"),
        ):
            add(
                f"ablation_{row['ablation']}_{column}",
                float(row[column]),
                units,
                "all matched factorial cells",
                "results/converter_ablations.csv",
                "descriptive scenario-grid summary",
            )
    environment_row = environment.iloc[0]
    for column in ("platform", "python", "processor", "memory_total", "software_versions"):
        add(
            f"performance_{column}",
            str(environment_row[column]),
            "text",
            "current revision VM",
            "results/computational_environment.csv",
            "single-run environment record",
        )
    for column, units in (
        ("logical_cpus", "count"),
        ("peak_process_rss_mb", "MiB"),
        ("factorial_scenario_runtime_s", "s"),
        ("converter_ablation_runtime_s", "s"),
        ("pipeline_elapsed_before_document_build_s", "s"),
    ):
        add(
            f"performance_{column}",
            float(environment_row[column]),
            units,
            "current revision VM",
            "results/computational_environment.csv",
            "single-run timing",
        )
    add(
        "performance_benchmark_repeats",
        int(feeder_performance.repeats.iloc[0]),
        "repeated solves",
        "each feeder/topology benchmark",
        "results/feeder_runtime_benchmark.csv",
        "declared benchmark repetition count",
    )
    for row in feeder_performance.to_dict(orient="records"):
        prefix = f"performance_{row['feeder']}_{row['topology']}"
        for column, units in (
            ("nodes", "nodes"),
            ("edges", "edges"),
            ("median_runtime_ms", "ms"),
            ("state_evaluations", "evaluations"),
            ("transition_evaluations", "evaluations"),
        ):
            add(
                f"{prefix}_{column}",
                float(row[column]),
                units,
                "30 repeated solves for the central optimization setting",
                "results/feeder_runtime_benchmark.csv",
                "median timing or deterministic evaluation count",
            )
    add(
        "performance_min_feeder_median_runtime_ms",
        float(feeder_performance.median_runtime_ms.min()),
        "ms",
        "30 repeated solves per feeder/topology",
        "results/feeder_runtime_benchmark.csv",
        "range across six feeder/topology cells",
    )
    add(
        "performance_max_feeder_median_runtime_ms",
        float(feeder_performance.median_runtime_ms.max()),
        "ms",
        "30 repeated solves per feeder/topology",
        "results/feeder_runtime_benchmark.csv",
        "range across six feeder/topology cells",
    )
    final_toy = toy_performance.sort_values("nodes").iloc[-1]
    add(
        "performance_max_enumerated_designs",
        int(final_toy.enumerated_designs),
        "designs",
        f"{int(final_toy.nodes)}-node toy chain",
        "results/toy_scaling_benchmark.csv",
    )
    add(
        "performance_toy_max_objective_error",
        float(toy_performance.objective_absolute_error.max()),
        "normalized objective units",
        "independently enumerated toy scaling cases",
        "results/toy_scaling_benchmark.csv",
    )
    return pd.DataFrame(rows)


def _build_pdf(manuscript: Path, page_limit: int) -> Path:
    pdf_dir = MANUSCRIPT / "build/pdf"
    pdf_dir.mkdir(parents=True, exist_ok=True)
    pdf = pdf_dir / manuscript.with_suffix(".pdf").name
    pdf.unlink(missing_ok=True)
    subprocess.run(
        [
            "libreoffice",
            "--headless",
            "--convert-to",
            "pdf",
            "--outdir",
            str(pdf_dir),
            str(manuscript),
        ],
        check=True,
        capture_output=True,
        text=True,
    )
    if not pdf.exists() or pdf.stat().st_size == 0:
        raise RuntimeError(f"LibreOffice did not create {pdf}")
    info = subprocess.run(
        ["pdfinfo", str(pdf)],
        check=True,
        capture_output=True,
        text=True,
    )
    match = re.search(r"^Pages:\s+(\d+)", info.stdout, re.MULTILINE)
    if match is None:
        raise RuntimeError(f"Could not read page count from {pdf}")
    pages = int(match.group(1))
    if not 1 <= pages <= page_limit:
        raise RuntimeError(f"PDF page count {pages} is outside the allowed range 1-{page_limit}")
    return pdf


def _validate_scalar_registry(values: pd.DataFrame) -> str:
    if values.value_id.duplicated().any():
        duplicates = values.loc[values.value_id.duplicated(), "value_id"].tolist()
        raise RuntimeError(f"Duplicate scalar registry identifiers: {duplicates}")
    if values[["value_id", "value", "units", "source_file", "generator"]].isna().any().any():
        raise RuntimeError("Scalar registry contains missing required values")
    missing_sources = [
        source
        for source in values.source_file.unique()
        if not (ROOT / str(source)).exists()
    ]
    if missing_sources:
        raise RuntimeError(f"Scalar registry sources do not exist: {missing_sources}")
    return "\n".join(
        [
            "# Scalar Registry Audit",
            "",
            "**PASS**",
            "",
            f"- Unique scalar identifiers: {len(values)}",
            "- Duplicate identifiers: 0",
            "- Missing required fields: 0",
            "- Missing source files: 0",
            "",
        ]
    )


def _write_deterministic_zip(root: Path, destination: Path) -> None:
    with zipfile.ZipFile(
        destination,
        "w",
        compression=zipfile.ZIP_DEFLATED,
        compresslevel=9,
    ) as archive:
        for path in sorted(item for item in root.rglob("*") if item.is_file()):
            entry = zipfile.ZipInfo(
                path.relative_to(root).as_posix(),
                date_time=(1980, 1, 1, 0, 0, 0),
            )
            entry.compress_type = zipfile.ZIP_DEFLATED
            entry.create_system = 0
            entry.external_attr = 0
            archive.writestr(entry, path.read_bytes())


def _package(manuscript: Path, cover_letter: Path, pdf: Path) -> None:
    build = SUBMISSION / "build"
    package = build / "tsg_submission_package"
    if package.exists():
        shutil.rmtree(package)
    package.mkdir(parents=True)
    shutil.copy2(manuscript, package / manuscript.name)
    shutil.copy2(pdf, package / pdf.name)
    shutil.copy2(cover_letter, package / cover_letter.name)
    figure_package = package / "figures"
    figure_package.mkdir()
    for path in sorted(FIGURES.glob("*")):
        if path.suffix.lower() in {".png", ".tiff"}:
            shutil.copy2(path, figure_package / path.name)
    table_package = package / "tables"
    table_package.mkdir()
    for path in sorted(TABLES.glob("*.csv")):
        shutil.copy2(path, table_package / path.name)
    for name in (
        "submission_checklist.md",
        "author_declarations.md",
        "FINAL_HANDOFF.txt",
        "FINAL_HANDOFF_REVISED.txt",
    ):
        shutil.copy2(build / name, package / name)
    for name in ("README.md", "Makefile", "pyproject.toml"):
        shutil.copy2(ROOT / name, package / name)
    for directory in (
        "configs",
        "environment",
        "handoffs",
        "provenance",
        "reports",
        "src",
        "tests",
    ):
        shutil.copytree(
            ROOT / directory,
            package / directory,
            ignore=shutil.ignore_patterns("__pycache__", "*.pyc", "*.egg-info"),
        )
    result_package = package / "results"
    result_package.mkdir()
    for path in sorted(RESULTS.glob("*")):
        if path.is_file():
            shutil.copy2(path, result_package / path.name)
    _write_deterministic_zip(package, build / "tsg_submission_package.zip")


def main() -> None:
    pipeline_start = time.perf_counter()
    acquire()
    config = yaml.safe_load((CONFIGS / "analysis_plan.yaml").read_text(encoding="utf-8"))
    journal = yaml.safe_load((CONFIGS / "journal_target.yaml").read_text(encoding="utf-8"))
    RESULTS.mkdir(parents=True, exist_ok=True)
    TABLES.mkdir(parents=True, exist_ok=True)
    REPORTS.mkdir(parents=True, exist_ok=True)
    ev_data_summary()
    scenario_start = time.perf_counter()
    scenarios = _run_scenarios(config)
    scenario_runtime_s = time.perf_counter() - scenario_start
    scenarios.to_csv(RESULTS / "scenario_results.csv", index=False)
    central = scenarios[
        (scenarios.topology == "original")
        & (scenarios.portfolio == "K3")
        & (scenarios.native_dc_share == 0.5)
        & (scenarios.seed == min(config["spatial_seeds"]))
        & (scenarios.converter_efficiency == 0.98)
        & (
            scenarios.case.isin(
                [
                    "all_ac_fixed",
                    "all_ac_conductor",
                    "hybrid_fixed",
                    "hybrid_joint",
                    "hybrid_ideal",
                ]
            )
        )
    ].copy()
    central.to_csv(RESULTS / "central_decomposition.csv", index=False)
    attribution = feeder_attribution(scenarios, config)
    attribution.to_csv(RESULTS / "feeder_attribution.csv", index=False)
    attribution.to_csv(TABLES / "table_feeder_attribution.csv", index=False)
    (REPORTS / "feeder_attribution.md").write_text(
        attribution_report(attribution),
        encoding="utf-8",
    )
    phase = scenarios[scenarios.case == "hybrid_joint"].copy()
    phase.to_csv(RESULTS / "phase_diagram.csv", index=False)
    factorial, transitions, factorial_structure = factorial_summaries(scenarios)
    factorial.to_csv(RESULTS / "factorial_architecture_summary.csv", index=False)
    transitions.to_csv(RESULTS / "factorial_transition_locations.csv", index=False)
    factorial_structure.to_csv(RESULTS / "factorial_structure.csv", index=False)
    factorial.to_csv(TABLES / "table_factorial_architectures.csv", index=False)
    (REPORTS / "factorial_analysis.md").write_text(
        factorial_report(scenarios, factorial, factorial_structure),
        encoding="utf-8",
    )
    novelty = _novelty_matrix()
    novelty.to_csv(RESULTS / "novelty_matrix.csv", index=False)
    validation = validate_all_ac(
        config["feeders"],
        float(config["power_factor"]),
        float(config["ac_voltage_line_line_v"]),
    )
    validation_stress = validate_all_ac_stress(
        config["feeders"],
        float(config["power_factor"]),
        float(config["ac_voltage_line_line_v"]),
        {
            name: float(portfolio["peak_factor"])
            for name, portfolio in config["portfolios"].items()
        },
    )
    validation_stress.to_csv(
        TABLES / "table_validation_stress.csv",
        index=False,
    )
    (REPORTS / "validation_stress.md").write_text(
        validation_stress_report(validation_stress),
        encoding="utf-8",
    )
    exactness = validate_toy_cases()
    exactness.to_csv(RESULTS / "dp_exactness_validation.csv", index=False)
    QC.mkdir(parents=True, exist_ok=True)
    (QC / "dp_exactness_validation.md").write_text(
        exactness_report(exactness),
        encoding="utf-8",
    )
    require_exactness(exactness)
    uncertainty = paired_joint_results(scenarios)
    uncertainty.to_csv(RESULTS / "uncertainty_summary.csv", index=False)
    uncertainty.groupby(["feeder", "topology", "portfolio"], as_index=False).agg(
        median_loss_change_pct=("loss_change_pct", "median"),
        q05_loss_change_pct=("loss_change_pct", lambda values: values.quantile(0.05)),
        q95_loss_change_pct=("loss_change_pct", lambda values: values.quantile(0.95)),
        mean_dc_node_fraction=("dc_node_fraction", "mean"),
    ).to_csv(TABLES / "table_3_robustness.csv", index=False)
    discrepancy, discrepancy_summary = classify_model_discrepancy(
        scenarios,
        validation,
    )
    discrepancy.to_csv(
        RESULTS / "model_discrepancy_classification.csv",
        index=False,
    )
    discrepancy_summary.to_csv(
        TABLES / "table_model_discrepancy_classification.csv",
        index=False,
    )
    (REPORTS / "model_discrepancy_classification.md").write_text(
        discrepancy_report(discrepancy, validation),
        encoding="utf-8",
    )
    ablation_start = time.perf_counter()
    ablations, ablation_summary = converter_ablations(config)
    ablation_runtime_s = time.perf_counter() - ablation_start
    ablations.to_csv(RESULTS / "converter_ablations.csv", index=False)
    ablation_summary.to_csv(TABLES / "table_converter_ablations.csv", index=False)
    (REPORTS / "converter_ablations.md").write_text(
        ablation_report(ablations),
        encoding="utf-8",
    )
    feeder_performance = feeder_runtime_benchmark(config)
    toy_performance = toy_scaling_benchmark()
    environment = environment_record(
        scenario_runtime_s,
        ablation_runtime_s,
        time.perf_counter() - pipeline_start,
    )
    feeder_performance.to_csv(
        RESULTS / "feeder_runtime_benchmark.csv",
        index=False,
    )
    toy_performance.to_csv(
        RESULTS / "toy_scaling_benchmark.csv",
        index=False,
    )
    environment.to_csv(
        RESULTS / "computational_environment.csv",
        index=False,
    )
    feeder_performance.to_csv(
        TABLES / "table_computational_performance.csv",
        index=False,
    )
    (REPORTS / "computational_performance.md").write_text(
        performance_report(environment, feeder_performance, toy_performance),
        encoding="utf-8",
    )
    values = _manuscript_values(
        scenarios,
        central,
        validation,
        config,
        attribution,
        validation_stress,
        exactness,
        discrepancy,
        ablations,
        feeder_performance,
        toy_performance,
        environment,
        factorial_structure,
    )
    values["version"] = "0.1.0"
    values.to_csv(RESULTS / "manuscript_values.csv", index=False)
    values.to_csv(RESULTS / "manuscript_scalar_registry.csv", index=False)
    (QC / "scalar_registry_audit.md").write_text(
        _validate_scalar_registry(values),
        encoding="utf-8",
    )
    central.to_csv(TABLES / "table_1_central_decomposition.csv", index=False)
    validation.to_csv(TABLES / "table_2_validation.csv", index=False)
    build_all(central, phase, validation)
    manuscript = build_manuscript(values, central, validation)
    cover_letter = build_cover_letter(values)
    build_submission_documents(values)
    write_result_manifest()
    pdf = _build_pdf(manuscript, int(journal["initial_page_limit"]))
    _package(manuscript, cover_letter, pdf)


if __name__ == "__main__":
    main()
