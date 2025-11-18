"""Data loading and feature engineering helpers."""

from __future__ import annotations

import numpy as np
import pandas as pd

from .common import haversine


def load_data(csv_path: str) -> pd.DataFrame:
    """Load CSV, drop invalid rows, and add log throughput."""
    df = pd.read_csv(csv_path, parse_dates=["date"])
    df = df.dropna(subset=["download_mbps", "min_rtt_ms", "packet_loss_rate"])
    df = df[df["min_rtt_ms"] > 0].copy()
    df = df[df["download_mbps"] >= 0]
    df["log_download"] = np.log1p(df["download_mbps"])
    return df.reset_index(drop=True)


def feature_engineering(df: pd.DataFrame) -> pd.DataFrame:
    """Augment data with engineered numeric features and client identifiers."""
    processed = df.copy()
    # Convert categorical features to string type for consistency
    processed["client_asn"] = processed["client_asn"].astype(str)
    processed["client_country"] = processed["client_country"].fillna("UNK")
    processed["server_site"] = processed["server_site"].fillna("UNK")
    processed["distance_km"] = haversine(
        processed["client_lat"].values,
        processed["client_lon"].values,
        processed["server_lat"].values,
        processed["server_lon"].values,
    )
    processed["inv_rtt"] = 1.0 / processed["min_rtt_ms"]
    processed["client_id"] = (
        processed["client_lat"].round(4).astype(str)
        + "_"
        + processed["client_lon"].round(4).astype(str)
        + "_"
        + processed["client_asn"].astype(str)
    )
    return processed
