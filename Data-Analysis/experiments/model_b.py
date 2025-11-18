"""Model B: extended linear regression with distance and categorical features."""

from __future__ import annotations

import numpy as np
import pandas as pd
from sklearn.linear_model import Ridge
from sklearn.model_selection import train_test_split

from .common import (
    ModelArtifact,
    RANDOM_STATE,
    build_extended_preprocessor,
    compute_split_metrics,
    ensure_batch,
    measure_prediction_latency,
)


def train_linear_extended(df: pd.DataFrame) -> ModelArtifact:
    """Train Model B on numeric and categorical features."""
    # Make a copy to avoid modifying the original dataframe
    df_processed = df.copy()
    
    # Process client_asn: merge low-frequency ASNs (freq < 100) into "other"
    # Note: client_asn is already converted to string in feature_engineering()
    asn_counts = df_processed["client_asn"].value_counts()
    low_freq_asns = asn_counts[asn_counts < 100].index
    df_processed.loc[df_processed["client_asn"].isin(low_freq_asns), "client_asn"] = "other"
    
    numeric_features = ["inv_rtt", "packet_loss_rate", "distance_km"]
    categorical_features = ["server_site", "client_country", "client_asn"]
    features = numeric_features + categorical_features
    target = df_processed["log_download"]

    X_train, X_test, y_train, y_test = train_test_split(
        df_processed[features], target, test_size=0.2, random_state=RANDOM_STATE
    )
    preprocessor = build_extended_preprocessor(numeric_features, categorical_features)
    X_train_proc = preprocessor.fit_transform(X_train)
    X_test_proc = preprocessor.transform(X_test)

    # Use Ridge regression for regularization to reduce overfitting
    # Alternative: ElasticNet(alpha=0.1, l1_ratio=0.5) for L1+L2 regularization
    model = Ridge(alpha=1.0)
    model.fit(X_train_proc, y_train)

    metrics = compute_split_metrics(model, X_train_proc, y_train, X_test_proc, y_test)
    sample_features = ensure_batch(X_test, 10000)
    prediction_time = measure_prediction_latency(model, preprocessor, sample_features)

    feature_names = preprocessor.get_feature_names_out()
    coef_series = pd.Series(model.coef_, index=feature_names)
    top_coefficients = coef_series.reindex(coef_series.abs().sort_values(ascending=False).index).head(10)

    return ModelArtifact(
        name="Model B - Ridge Regression",
        model=model,
        preprocessor=preprocessor,
        features=features,
        metrics=metrics,
        prediction_time_10k=prediction_time,
        dense_input=False,
        feature_importance=top_coefficients,
    )
