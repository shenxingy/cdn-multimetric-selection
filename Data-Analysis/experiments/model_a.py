"""Model A: simple linear regression on RTT and packet loss."""

from __future__ import annotations

from sklearn.linear_model import LinearRegression
from sklearn.model_selection import train_test_split

from .common import (
    ModelArtifact,
    RANDOM_STATE,
    build_simple_preprocessor,
    compute_split_metrics,
    ensure_batch,
    measure_prediction_latency,
)


def train_linear_simple(df):
    """Train Model A using inv_rtt and packet_loss_rate features."""
    features = ["inv_rtt", "packet_loss_rate"]
    target = df["log_download"]
    X_train, X_test, y_train, y_test = train_test_split(
        df[features], target, test_size=0.2, random_state=RANDOM_STATE
    )
    preprocessor = build_simple_preprocessor(features)
    X_train_proc = preprocessor.fit_transform(X_train)
    X_test_proc = preprocessor.transform(X_test)

    model = LinearRegression()
    model.fit(X_train_proc, y_train)

    metrics = compute_split_metrics(model, X_train_proc, y_train, X_test_proc, y_test)
    sample_features = ensure_batch(X_test, 10000)
    prediction_time = measure_prediction_latency(model, preprocessor, sample_features)

    return ModelArtifact(
        name="Model A - Simple Linear Regression",
        model=model,
        preprocessor=preprocessor,
        features=features,
        metrics=metrics,
        prediction_time_10k=prediction_time,
        dense_input=False,
    )
