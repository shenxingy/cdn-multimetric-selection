"""Visualization helpers for experiment outputs."""

from __future__ import annotations

import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import pandas as pd

from .common import ModelArtifact


def create_visualizations(
    df: pd.DataFrame,
    extended_artifact: ModelArtifact,
    selection_summary: pd.DataFrame,
    scatter_alpha: float = 0.3,
    output_path: str | None = "experiments_summary.png",
) -> None:
    """Generate scatter plots, feature importance, and selection summary bars."""
    sns.set_theme(style="whitegrid")
    fig, axes = plt.subplots(2, 2, figsize=(14, 10))

    axes[0, 0].scatter(df["min_rtt_ms"], df["download_mbps"], alpha=scatter_alpha)
    axes[0, 0].set_xlabel("Min RTT (ms)")
    axes[0, 0].set_ylabel("Throughput (Mbps)")
    axes[0, 0].set_title("RTT vs Throughput")

    axes[0, 1].scatter(df["distance_km"], df["download_mbps"], alpha=scatter_alpha, color="#ff7f0e")
    axes[0, 1].set_xlabel("Distance (km)")
    axes[0, 1].set_ylabel("Throughput (Mbps)")
    axes[0, 1].set_title("Distance vs Throughput")

    if extended_artifact.feature_importance is not None:
        importance = extended_artifact.feature_importance.sort_values()
        axes[1, 0].barh(importance.index, importance.values, color="#2ca02c")
        axes[1, 0].set_title("Top 10 Linear Coefficients (Model B)")
        axes[1, 0].set_xlabel("Coefficient value")
        axes[1, 0].set_ylabel("Feature")
    else:
        axes[1, 0].axis("off")

    x = np.arange(len(selection_summary))
    width = 0.35
    axes[1, 1].bar(x - width / 2, selection_summary["median_mbps"], width, label="Median")
    axes[1, 1].bar(x + width / 2, selection_summary["p90_mbps"], width, label="P90")
    axes[1, 1].set_xticks(x)
    axes[1, 1].set_xticklabels(selection_summary["method"], rotation=20, ha="right")
    axes[1, 1].set_ylabel("Throughput (Mbps)")
    axes[1, 1].set_title("Server Selection Performance")
    axes[1, 1].legend()

    plt.tight_layout()
    if output_path:
        plt.savefig(output_path, dpi=150)
        plt.close(fig)
    else:
        plt.show()
