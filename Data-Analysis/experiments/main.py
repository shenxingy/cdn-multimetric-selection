"""Entry point orchestrating all experiments."""

from __future__ import annotations

from typing import Any, Dict

from .data import feature_engineering, load_data
from .evaluation import evaluate_models
from .model_a import train_linear_simple
from .model_b import train_linear_extended
from .model_c import train_nn
from .simulation import simulate_selection
from .visualization import create_visualizations


def main(csv_path: str = "mlab_ndt_us_30days_20251111_004612.csv") -> Dict[str, Any]:
    """Run the full experiment stack end to end."""
    df_raw = load_data(csv_path)
    df = feature_engineering(df_raw)

    model_a = train_linear_simple(df)
    model_b = train_linear_extended(df)
    model_c = train_nn(df)

    metrics_table = evaluate_models([model_a, model_b, model_c])
    selection_summary, per_client_results = simulate_selection(df, model_a, model_b, model_c)
    create_visualizations(df, model_b, selection_summary, output_path="experiments_summary.png")

    return {
        "metrics": metrics_table,
        "selection_summary": selection_summary,
        "per_client_results": per_client_results,
    }
