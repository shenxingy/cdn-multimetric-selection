"""Aggregate reporting utilities for fitted models."""

from __future__ import annotations

import pandas as pd

from .common import ModelArtifact


def evaluate_models(model_artifacts: list[ModelArtifact]) -> pd.DataFrame:
    """Return a DataFrame summarizing core metrics for each model."""
    rows = []
    for artifact in model_artifacts:
        row = {"model": artifact.name, **artifact.metrics}
        row["prediction_time_10k_s"] = artifact.prediction_time_10k
        if artifact.training_time is not None:
            row["training_time_s"] = artifact.training_time
        rows.append(row)
    summary = pd.DataFrame(rows)
    print("\nModel performance summary (log-download space):")
    print(summary)
    return summary
