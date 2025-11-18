"""Model C: small neural network (scikit-learn MLP) mirroring Model B features."""

from __future__ import annotations

import time

import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.neural_network import MLPRegressor

from .common import (
    ModelArtifact,
    RANDOM_STATE,
    build_extended_preprocessor,
    compute_split_metrics,
    ensure_batch,
    measure_prediction_latency,
    to_dense,
)


def train_nn(df: pd.DataFrame) -> ModelArtifact:
    """Train the neural network baseline with dense categorical encodings."""
    numeric_features = ["inv_rtt", "packet_loss_rate", "distance_km"]
    categorical_features = ["server_site", "client_country"]
    features = numeric_features + categorical_features
    target = df["log_download"].values

    X_train, X_test, y_train, y_test = train_test_split(
        df[features], target, test_size=0.2, random_state=RANDOM_STATE
    )
    preprocessor = build_extended_preprocessor(numeric_features, categorical_features)
    X_train_proc = to_dense(preprocessor.fit_transform(X_train))
    X_test_proc = to_dense(preprocessor.transform(X_test))

    start = time.time()
    model = MLPRegressor(
        hidden_layer_sizes=(16,),
        activation="relu",
        solver="adam",
        batch_size=512,
        learning_rate_init=0.001,
        max_iter=150,
        random_state=RANDOM_STATE,
        early_stopping=True,
        validation_fraction=0.1,
        n_iter_no_change=5,
        verbose=False,
    )
    model.fit(X_train_proc, y_train)
    training_time = time.time() - start

    metrics = compute_split_metrics(model, X_train_proc, y_train, X_test_proc, y_test)
    sample_features = ensure_batch(X_test, 10000)
    prediction_time = measure_prediction_latency(model, preprocessor, sample_features, dense_output=True)

    return ModelArtifact(
        name="Model C - Small Neural Network",
        model=model,
        preprocessor=preprocessor,
        features=features,
        metrics=metrics,
        prediction_time_10k=prediction_time,
        dense_input=True,
        training_time=training_time,
    )
