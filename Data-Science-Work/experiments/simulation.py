"""Server selection simulation using different strategies."""

from __future__ import annotations

import numpy as np
import pandas as pd

from .common import ModelArtifact, safe_predict, to_dense


def select_with_model(group: pd.DataFrame, artifact: ModelArtifact) -> float:
    """Predict throughput for a client group and return the best actual Mbps."""
    feature_df = group[artifact.features]
    transformed = artifact.preprocessor.transform(feature_df)
    if artifact.dense_input:
        transformed = to_dense(transformed)
    preds_log = safe_predict(artifact.model, transformed)
    best_idx = int(np.argmax(preds_log))
    return group.iloc[best_idx]["download_mbps"]


def simulate_selection(
    df: pd.DataFrame,
    simple_artifact: ModelArtifact,
    extended_artifact: ModelArtifact,
    nn_artifact: ModelArtifact,
):
    """Compare RTT-based and model-based server selection across clients."""
    methods: dict[str, list[float]] = {
        "Method 1 - Min RTT": [],
        "Method 2 - Model A": [],
        "Method 3 - Model B": [],
        "Method 4 - Model C": [],
    }

    for _, group in df.groupby(["client_lat", "client_lon", "client_asn"]):
        group = group.sort_values("min_rtt_ms")
        methods["Method 1 - Min RTT"].append(group.iloc[0]["download_mbps"])
        methods["Method 2 - Model A"].append(select_with_model(group, simple_artifact))
        methods["Method 3 - Model B"].append(select_with_model(group, extended_artifact))
        methods["Method 4 - Model C"].append(select_with_model(group, nn_artifact))

    summary_rows = []
    baseline = np.array(methods["Method 1 - Min RTT"])
    baseline_median = np.median(baseline)
    for method_name, values in methods.items():
        arr = np.array(values)
        pct_gain = 0.0
        if method_name != "Method 1 - Min RTT" and baseline_median > 0:
            pct_gain = (np.median(arr) - baseline_median) / baseline_median * 100.0
        summary_rows.append(
            {
                "method": method_name,
                "median_mbps": np.median(arr),
                "p90_mbps": np.percentile(arr, 90),
                "pct_gain_vs_rtt": pct_gain,
            }
        )

    summary_df = pd.DataFrame(summary_rows)
    per_client_results = pd.DataFrame(methods)
    print("\nServer-selection summary (actual throughput in Mbps):")
    print(summary_df)
    return summary_df, per_client_results
