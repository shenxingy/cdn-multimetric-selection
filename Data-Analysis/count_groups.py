"""Count unique client groups in the dataset."""

import pandas as pd
from experiments.data import load_data, feature_engineering

# Load and process data
df_raw = load_data("mlab_ndt_us_30days_20251111_004612.csv")
df = feature_engineering(df_raw)

# Count unique groups based on simulation groupby keys
unique_groups = df.groupby(["client_lat", "client_lon", "client_asn"]).ngroups
print(f"\n{'='*60}")
print(f"Dataset Analysis Results")
print(f"{'='*60}")
print(f"Total Records: {len(df):,}")
print(f"Unique Client Groups (grouped by client_lat, client_lon, client_asn): {unique_groups:,}")
print(f"{'='*60}\n")

# Show group size distribution
group_sizes = df.groupby(["client_lat", "client_lon", "client_asn"]).size()
print("Server Candidate Statistics per Client Group:")
print(f"  Average Candidate Servers: {group_sizes.mean():.2f}")
print(f"  Median Candidate Servers: {group_sizes.median():.0f}")
print(f"  Minimum Candidate Servers: {group_sizes.min()}")
print(f"  Maximum Candidate Servers: {group_sizes.max()}")
print(f"  Standard Deviation: {group_sizes.std():.2f}")

print("\nDistribution of Candidate Servers:")
print(group_sizes.value_counts().sort_index().head(10))

# Show some example groups
print("\n\nSample Client Groups (first 5):")
for i, ((lat, lon, asn), group) in enumerate(df.groupby(["client_lat", "client_lon", "client_asn"])):
    if i >= 5:
        break
    print(f"\nClient {i+1}:")
    print(f"  Location: ({lat:.4f}, {lon:.4f})")
    print(f"  ASN: {asn}")
    print(f"  Available Servers: {len(group)}")
    print(f"  RTT Range: {group['min_rtt_ms'].min():.2f} - {group['min_rtt_ms'].max():.2f} ms")
    print(f"  Throughput Range: {group['download_mbps'].min():.2f} - {group['download_mbps'].max():.2f} Mbps")

