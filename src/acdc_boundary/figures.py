from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from .paths import FIGURES


def _save(fig, stem: str) -> None:
    FIGURES.mkdir(parents=True, exist_ok=True)
    fig.savefig(FIGURES / f"{stem}.png", dpi=300, bbox_inches="tight")
    fig.savefig(
        FIGURES / f"{stem}.tiff",
        dpi=600,
        bbox_inches="tight",
        pil_kwargs={"compression": "tiff_lzw"},
    )
    plt.close(fig)


def decomposition_figure(central: pd.DataFrame) -> None:
    order = ["all_ac_fixed", "all_ac_conductor", "hybrid_fixed", "hybrid_joint"]
    labels = ["Inherited AC", "AC + conductor", "Hybrid, fixed conductor", "Joint hybrid"]
    pivot = central.pivot(index="feeder", columns="case", values="total_loss_kwh")
    feeders = list(pivot.index)
    x = np.arange(len(feeders))
    width = 0.19
    fig, ax = plt.subplots(figsize=(7.2, 3.7))
    for index, (case, label) in enumerate(zip(order, labels)):
        ax.bar(x + (index - 1.5) * width, pivot[case], width, label=label)
    ax.set_xticks(x, [value.title() for value in feeders])
    ax.set_ylabel("Annual modeled loss (kWh)")
    ax.legend(frameon=False, fontsize=7, ncol=2)
    ax.grid(axis="y", alpha=0.25)
    fig.tight_layout()
    _save(fig, "figure_1_decomposition")


def phase_figure(phase: pd.DataFrame) -> None:
    subset = phase[
        (phase.feeder == "suburban")
        & (phase.topology == "original")
        & (phase.portfolio == "K3")
        & (phase.seed == phase.seed.min())
    ]
    pivot = subset.pivot_table(
        index="converter_efficiency",
        columns="native_dc_share",
        values="dc_node_fraction",
        aggfunc="first",
    ).sort_index(ascending=False)
    fig, ax = plt.subplots(figsize=(5.2, 3.8))
    image = ax.imshow(pivot.to_numpy(), aspect="auto", vmin=0, vmax=1, cmap="viridis")
    ax.set_xticks(range(len(pivot.columns)), [f"{value:.2f}" for value in pivot.columns])
    ax.set_yticks(range(len(pivot.index)), [f"{value:.2f}" for value in pivot.index])
    ax.set_xlabel("Native-DC annual-energy share")
    ax.set_ylabel("Boundary-converter peak efficiency")
    bar = fig.colorbar(image, ax=ax)
    bar.set_label("Fraction of non-root buses assigned DC")
    fig.tight_layout()
    _save(fig, "figure_2_phase_diagram")


def architecture_figure(phase: pd.DataFrame) -> None:
    subset = phase[
        (phase.topology == "original")
        & (phase.portfolio == "K3")
        & (phase.converter_efficiency == 0.98)
    ]
    grouped = (
        subset.groupby(["feeder", "native_dc_share"], as_index=False)
        .dc_node_fraction.mean()
        .sort_values("native_dc_share")
    )
    fig, ax = plt.subplots(figsize=(5.5, 3.7))
    for feeder, frame in grouped.groupby("feeder"):
        ax.plot(
            frame.native_dc_share,
            frame.dc_node_fraction,
            marker="o",
            label=feeder.title(),
        )
    ax.plot([0, 1], [0, 1], color="0.6", linestyle="--", linewidth=1, label="Identity")
    ax.set_xlabel("Native-DC annual-energy share")
    ax.set_ylabel("Mean bus share assigned DC")
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    ax.grid(alpha=0.25)
    ax.legend(frameon=False, fontsize=8)
    fig.tight_layout()
    _save(fig, "figure_3_architecture_transition")


def validation_figure(validation: pd.DataFrame) -> None:
    fig, ax = plt.subplots(figsize=(4.4, 4.0))
    ax.scatter(validation.pandapower_loss_kw, validation.approximate_loss_kw, s=55)
    upper = max(validation.pandapower_loss_kw.max(), validation.approximate_loss_kw.max())
    ax.plot([0, upper], [0, upper], linestyle="--", color="0.4")
    for row in validation.itertuples():
        ax.annotate(row.feeder, (row.pandapower_loss_kw, row.approximate_loss_kw), fontsize=8)
    ax.set_xlabel("pandapower line loss (kW)")
    ax.set_ylabel("Planning approximation (kW)")
    ax.grid(alpha=0.25)
    fig.tight_layout()
    _save(fig, "figure_4_validation")


def formulation_figure() -> None:
    fig, ax = plt.subplots(figsize=(7.2, 2.8))
    ax.axis("off")
    boxes = [
        (0.03, 0.58, "Archived benchmark\nand temporal profiles"),
        (0.28, 0.58, "Matched AC and\nAC/DC design cells"),
        (0.53, 0.58, "Domain/conductor\noptimization"),
        (0.78, 0.58, "Physics replay\nand QC gates"),
        (0.28, 0.12, "Topology and conductor\nattribution"),
        (0.58, 0.12, "Conditional architecture\ntransition map"),
    ]
    for x, y, text in boxes:
        ax.text(
            x,
            y,
            text,
            ha="center",
            va="center",
            fontsize=8,
            bbox={"boxstyle": "round,pad=0.45", "fc": "white", "ec": "0.25"},
            transform=ax.transAxes,
        )
    arrows = [
        ((0.12, 0.58), (0.21, 0.58)),
        ((0.37, 0.58), (0.46, 0.58)),
        ((0.62, 0.58), (0.71, 0.58)),
        ((0.37, 0.47), (0.34, 0.25)),
        ((0.62, 0.47), (0.60, 0.25)),
        ((0.43, 0.12), (0.49, 0.12)),
    ]
    for start, end in arrows:
        ax.annotate("", xy=end, xytext=start, xycoords="axes fraction", arrowprops={"arrowstyle": "->"})
    fig.tight_layout()
    _save(fig, "figure_0_formulation")


def build_all(central: pd.DataFrame, phase: pd.DataFrame, validation: pd.DataFrame) -> None:
    formulation_figure()
    decomposition_figure(central)
    phase_figure(phase)
    architecture_figure(phase)
    validation_figure(validation)
    Path(FIGURES / "README.txt").write_text(
        "PNG files are 300 dpi; TIFF files are 600 dpi with LZW compression.\n",
        encoding="utf-8",
    )
