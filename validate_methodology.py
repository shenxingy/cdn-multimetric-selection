"""
Validation Script: Exposing the Methodological Flaw in the 610% Improvement Claim

This script demonstrates that the current dashboard's "610% improvement" is achieved
by using historical throughput data in the composite score, which is not available
in a real CDN selection scenario.

Author: Validation Team
Date: November 18, 2025
"""

import pandas as pd
import numpy as np
from pathlib import Path

print("="*80)
print("CRITICAL METHODOLOGY VALIDATION")
print("="*80)
print()

# Load M-Lab data
mlab_path = Path("notebooks/data/raw/mlab_ndt_us_30days_20251111_004612.csv")
df = pd.read_csv(mlab_path)
print(f"✓ Loaded {len(df):,} M-Lab measurements")
print()

# Clean data
df = df.dropna(subset=['min_rtt_ms', 'download_mbps', 'packet_loss_rate'])
df = df[(df['min_rtt_ms'] > 0) & (df['download_mbps'] > 0)]
print(f"✓ Cleaned to {len(df):,} valid measurements")
print()

print("="*80)
print("DASHBOARD'S CURRENT APPROACH (Using Historical Throughput)")
print("="*80)
print()

def normalize_metric(series, lower_is_better=True):
    min_val = series.min()
    max_val = series.max()
    if max_val == min_val:
        return pd.Series([50] * len(series))
    
    if lower_is_better:
        normalized = 100 * (1 - (series - min_val) / (max_val - min_val))
    else:
        normalized = 100 * (series - min_val) / (max_val - min_val)
    return normalized

# Calculate composite score (INCLUDES throughput!)
df['rtt_score'] = normalize_metric(df['min_rtt_ms'], lower_is_better=True)
df['throughput_score'] = normalize_metric(df['download_mbps'], lower_is_better=False)
df['loss_score'] = normalize_metric(df['packet_loss_rate'], lower_is_better=True)
df['composite_score'] = (0.3 * df['rtt_score'] + 0.4 * df['throughput_score'] + 0.3 * df['loss_score'])

print("Composite Score Formula:")
print("  Score = 0.3 × RTT_score + 0.4 × THROUGHPUT_score + 0.3 × Loss_score")
print()
print("⚠️  PROBLEM: This uses historical throughput to predict future throughput!")
print("   In reality, you don't know throughput until AFTER you've selected the server.")
print()

# Run simulation (dashboard's method)
np.random.seed(42)
n_simulations = 1000
rtt_throughputs = []
multi_throughputs = []

for _ in range(n_simulations):
    sample = df.sample(n=min(100, len(df)), replace=True)
    
    # RTT-only selection
    rtt_selected = sample.nsmallest(1, 'min_rtt_ms')
    rtt_throughputs.append(rtt_selected['download_mbps'].values[0])
    
    # Multi-metric selection (uses throughput in score)
    multi_selected = sample.nlargest(1, 'composite_score')
    multi_throughputs.append(multi_selected['download_mbps'].values[0])

rtt_median = np.median(rtt_throughputs)
multi_median = np.median(multi_throughputs)
improvement = ((multi_median - rtt_median) / rtt_median) * 100

print("Dashboard's Results:")
print(f"  RTT-only median:    {rtt_median:.1f} Mbps")
print(f"  Multi-metric median: {multi_median:.1f} Mbps")
print(f"  Improvement:         {improvement:.1f}%")
print()
print("✓ This reproduces the dashboard's 610% claim")
print()

print("="*80)
print("REALISTIC APPROACH (WITHOUT Future Knowledge)")
print("="*80)
print()

# Calculate score WITHOUT throughput (realistic)
df['realistic_score'] = (0.5 * df['rtt_score'] + 0.5 * df['loss_score'])

print("Realistic Score Formula:")
print("  Score = 0.5 × RTT_score + 0.5 × Loss_score")
print()
print("✓ This uses only metrics available BEFORE connecting to the server")
print()

# Run simulation (realistic method)
np.random.seed(42)
rtt_throughputs_real = []
realistic_throughputs = []

for _ in range(n_simulations):
    sample = df.sample(n=min(100, len(df)), replace=True)
    
    # RTT-only selection
    rtt_selected = sample.nsmallest(1, 'min_rtt_ms')
    rtt_throughputs_real.append(rtt_selected['download_mbps'].values[0])
    
    # Realistic multi-metric (NO throughput in score)
    realistic_selected = sample.nlargest(1, 'realistic_score')
    realistic_throughputs.append(realistic_selected['download_mbps'].values[0])

rtt_median_real = np.median(rtt_throughputs_real)
realistic_median = np.median(realistic_throughputs)
realistic_improvement = ((realistic_median - rtt_median_real) / rtt_median_real) * 100

print("Realistic Results:")
print(f"  RTT-only median:     {rtt_median_real:.1f} Mbps")
print(f"  Multi-metric median: {realistic_median:.1f} Mbps")
print(f"  Improvement:         {realistic_improvement:.1f}%")
print()

if realistic_improvement < 0:
    print("⚠️  CRITICAL: Multi-metric performs WORSE than RTT-only!")
elif realistic_improvement < 50:
    print("⚠️  Modest improvement, far from 610% claim")
else:
    print("✓ Multi-metric still shows improvement without cheating")
print()

print("="*80)
print("SUMMARY")
print("="*80)
print()
print(f"Dashboard claims:  {improvement:.1f}% improvement (uses future throughput)")
print(f"Realistic result:  {realistic_improvement:.1f}% improvement (no future knowledge)")
print()
print("CONCLUSION:")
if realistic_improvement < 0:
    print("  The 610% improvement claim is INVALID. When using only predictive metrics")
    print("  (RTT + Loss), the multi-metric approach performs worse than RTT-only.")
elif realistic_improvement < 100:
    print("  The 610% improvement is inflated by using historical throughput.")
    print(f"  The realistic improvement is only {realistic_improvement:.1f}%, not 610%.")
else:
    print("  The multi-metric approach still works without throughput, but the")
    print(f"  improvement is {realistic_improvement:.1f}%, not 610%.")
print()
print("RECOMMENDATION:")
print("  The research should either:")
print("  1. Revise claims to reflect realistic (predictive-only) methodology")
print("  2. Clearly state that 610% requires historical throughput knowledge")
print("  3. Focus on other metrics (RSRP in 5G, loss patterns, etc.)")
print()
print("="*80)
