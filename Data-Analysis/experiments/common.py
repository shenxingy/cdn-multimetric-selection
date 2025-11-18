"""Shared utilities and data structures used across experiments."""

from __future__ import annotations

import time
from dataclasses import dataclass
from typing import Any, Dict, List

import numpy as np
import pandas as pd
from scipy import sparse
from sklearn.compose import ColumnTransformer
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from sklearn.preprocessing import OneHotEncoder, StandardScaler


EARTH_RADIUS_KM = 6371.0
RANDOM_STATE = 42

np.random.seed(RANDOM_STATE)


@dataclass
class ModelArtifact:
    """Container storing a fitted model and relevant metadata."""

    name: str
    model: Any
    preprocessor: ColumnTransformer
    features: List[str]
    metrics: Dict[str, float]
    prediction_time_10k: float
    dense_input: bool
    training_time: float | None = None
    feature_importance: pd.Series | None = None


def haversine(lat1: np.ndarray, lon1: np.ndarray, lat2: np.ndarray, lon2: np.ndarray) -> np.ndarray:
    """Great-circle distance in kilometers between two lat/lon coordinate pairs."""
    lat1, lon1, lat2, lon2 = map(np.radians, [lat1, lon1, lat2, lon2])
    dlat = lat2 - lat1
    dlon = lon2 - lon1
    a = np.sin(dlat / 2.0) ** 2 + np.cos(lat1) * np.cos(lat2) * np.sin(dlon / 2.0) ** 2
    return 2 * EARTH_RADIUS_KM * np.arcsin(np.sqrt(a))


def build_simple_preprocessor(features: List[str]) -> ColumnTransformer:
    """Return a StandardScaler-only pipeline for numeric features."""
    return ColumnTransformer(
        transformers=[("num", StandardScaler(), features)],
        remainder="drop",
    )


def _build_one_hot_encoder() -> OneHotEncoder:
    """Construct an encoder compatible with multiple sklearn versions."""
    try:
        return OneHotEncoder(handle_unknown="ignore", sparse_output=False)
    except TypeError:
        return OneHotEncoder(handle_unknown="ignore", sparse=False)


def build_extended_preprocessor(numeric_features: List[str], categorical_features: List[str]) -> ColumnTransformer:
    """Return a scaler + one-hot encoder pipeline for mixed feature sets."""
    return ColumnTransformer(
        transformers=[
            ("num", StandardScaler(), numeric_features),
            ("cat", _build_one_hot_encoder(), categorical_features),
        ],
        remainder="drop",
    )


def to_dense(matrix: Any) -> np.ndarray:
    """Convert sparse matrices to dense arrays when needed."""
    if sparse.issparse(matrix):
        return matrix.toarray()
    return matrix


def ensure_batch(df: pd.DataFrame, target_size: int) -> pd.DataFrame:
    """Repeat rows so benchmarking always uses a fixed number of samples."""
    if len(df) == 0:
        raise ValueError("Cannot create a batch from an empty DataFrame.")
    if len(df) >= target_size:
        return df.iloc[:target_size].copy()
    reps = int(np.ceil(target_size / len(df)))
    expanded = pd.concat([df] * reps, ignore_index=True)
    return expanded.iloc[:target_size].copy()


def safe_predict(model: Any, X: Any) -> np.ndarray:
    """Run inference regardless of estimator API differences."""
    try:
        preds = model.predict(X, verbose=0)
    except TypeError:
        preds = model.predict(X)
    return np.asarray(preds).reshape(-1)


def compute_split_metrics(model: Any, X_train: Any, y_train: np.ndarray, X_test: Any, y_test: np.ndarray) -> Dict[str, float]:
    """Compute train/test R2, RMSE, and MAE for a fitted model."""
    y_pred_train = safe_predict(model, X_train)
    y_pred_test = safe_predict(model, X_test)
    mse_train = mean_squared_error(y_train, y_pred_train)
    mse_test = mean_squared_error(y_test, y_pred_test)
    return {
        "r2_train": r2_score(y_train, y_pred_train),
        "r2_test": r2_score(y_test, y_pred_test),
        "rmse_train": np.sqrt(mse_train),
        "rmse_test": np.sqrt(mse_test),
        "mae_train": mean_absolute_error(y_train, y_pred_train),
        "mae_test": mean_absolute_error(y_test, y_pred_test),
    }


def measure_prediction_latency(
    model: Any, preprocessor: ColumnTransformer, sample_df: pd.DataFrame, dense_output: bool = False
) -> float:
    """Benchmark prediction wall-clock time on a 10k row sample."""
    transformed = preprocessor.transform(sample_df)
    if dense_output:
        transformed = to_dense(transformed)
    start = time.time()
    _ = safe_predict(model, transformed)
    return time.time() - start
