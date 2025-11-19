"""
RIPE Atlas Jitter Analysis
===========================
Analyzes RTT variance (jitter) to show path instability that RTT alone misses.
"""

import pandas as pd
import numpy as np
from pathlib import Path
import warnings
warnings.filterwarnings('ignore')

# Load RIPE data
data_path = Path("/Users/ankitraj2/558/cdn-multimetric-selection/notebooks/data/processed/ripe_atlas_processed.csv")
print(f"Loading RIPE Atlas data from {data_path}...")
df = pd.read_csv(data_path, parse_dates=['timestamp'])
print(f"✓ Loaded {len(df):,} RIPE Atlas measurements")

# Calculate jitter metrics
print("\n" + "="*80)
print("CALCULATING JITTER METRICS")
print("="*80)

df['jitter'] = df['rtt_max'] - df['rtt_min']
df['jitter_pct'] = (df['jitter'] / df['rtt_avg'] * 100).clip(0, 1000)  # Cap at 1000%
df['cv_rtt'] = (df['rtt_max'] - df['rtt_min']) / df['rtt_avg']  # Coefficient of variation

print(f"\nJitter Statistics:")
print(f"  - Mean jitter: {df['jitter'].mean():.2f} ms")
print(f"  - Median jitter: {df['jitter'].median():.2f} ms")
print(f"  - Max jitter: {df['jitter'].max():.2f} ms")
print(f"  - Mean jitter as % of RTT: {df['jitter_pct'].mean():.1f}%")

# Distribution of jitter
print(f"\nJitter Distribution:")
jitter_bins = [0, 1, 5, 10, 25, 50, 100, float('inf')]
jitter_labels = ['<1ms', '1-5ms', '5-10ms', '10-25ms', '25-50ms', '50-100ms', '>100ms']
df['jitter_bin'] = pd.cut(df['jitter'], bins=jitter_bins, labels=jitter_labels)
jitter_dist = df['jitter_bin'].value_counts().sort_index()

for bin_label, count in jitter_dist.items():
    pct = count / len(df) * 100
    print(f"  {bin_label:>10s}: {count:6,} ({pct:5.1f}%)")

# Analyze correlation between RTT and jitter
print("\n" + "="*80)
print("RTT vs JITTER CORRELATION")
print("="*80)

correlation = df['rtt_avg'].corr(df['jitter'])
print(f"\nCorrelation between RTT and Jitter: r = {correlation:.4f}")

if abs(correlation) < 0.3:
    print("  → WEAK correlation: RTT and jitter are largely independent!")
    print("  → Low RTT doesn't guarantee stable path")
elif abs(correlation) < 0.7:
    print("  → MODERATE correlation: Some relationship but still independent signal")
else:
    print("  → STRONG correlation: Jitter captured by RTT")

# Find problematic cases: Low RTT but high jitter
print("\n" + "="*80)
print("PROBLEM CASES: LOW RTT BUT HIGH JITTER")
print("="*80)

# Define thresholds
low_rtt_threshold = df['rtt_avg'].quantile(0.25)  # Bottom 25% RTT
high_jitter_threshold = df['jitter'].quantile(0.75)  # Top 25% jitter

problem_cases = df[(df['rtt_avg'] < low_rtt_threshold) & (df['jitter'] > high_jitter_threshold)]
print(f"\nCases with low RTT (<{low_rtt_threshold:.1f}ms) BUT high jitter (>{high_jitter_threshold:.1f}ms):")
print(f"  - Count: {len(problem_cases):,} measurements ({len(problem_cases)/len(df)*100:.2f}%)")

if len(problem_cases) > 0:
    print(f"\n  Example problem cases:")
    print(f"  {'Target':20s} {'Probe':10s} {'RTT Avg':>10s} {'Jitter':>10s} {'Loss':>8s}")
    print(f"  {'-'*20} {'-'*10} {'-'*10} {'-'*10} {'-'*8}")
    for _, row in problem_cases.head(10).iterrows():
        print(f"  {str(row['target'])[:20]:20s} {str(row['probe_id'])[:10]:10s} "
              f"{row['rtt_avg']:8.1f}ms {row['jitter']:8.1f}ms {row['packet_loss_pct']:6.1f}%")
    
    print(f"\n  ⚠️  RTT-only selection would choose these 'fast but unstable' paths!")
    print(f"      Multi-metric selection with jitter could avoid them.")

# Analyze jitter impact on loss
print("\n" + "="*80)
print("JITTER vs PACKET LOSS")
print("="*80)

# Group by jitter bins
jitter_loss_analysis = df.groupby('jitter_bin').agg({
    'packet_loss_pct': ['mean', 'count'],
    'rtt_avg': 'mean',
    'jitter': 'mean'
}).round(2)

print(f"\nPacket Loss by Jitter Level:")
print(f"  {'Jitter':>10s} {'Avg Loss':>12s} {'Avg RTT':>12s} {'Count':>10s}")
print(f"  {'-'*10} {'-'*12} {'-'*12} {'-'*10}")
for bin_label in jitter_labels:
    if bin_label in jitter_loss_analysis.index:
        loss = jitter_loss_analysis.loc[bin_label, ('packet_loss_pct', 'mean')]
        rtt = jitter_loss_analysis.loc[bin_label, ('rtt_avg', 'mean')]
        count = int(jitter_loss_analysis.loc[bin_label, ('packet_loss_pct', 'count')])
        print(f"  {bin_label:>10s} {loss:10.2f}% {rtt:10.1f}ms {count:10,}")

# Check if high jitter correlates with high loss
high_jitter = df[df['jitter'] > high_jitter_threshold]
low_jitter = df[df['jitter'] <= high_jitter_threshold]

print(f"\nHigh jitter (>{high_jitter_threshold:.1f}ms) vs Low jitter:")
print(f"  - High jitter avg loss: {high_jitter['packet_loss_pct'].mean():.2f}%")
print(f"  - Low jitter avg loss: {low_jitter['packet_loss_pct'].mean():.2f}%")
print(f"  - Difference: {(high_jitter['packet_loss_pct'].mean() - low_jitter['packet_loss_pct'].mean()):.2f} percentage points")

# Stability score concept
print("\n" + "="*80)
print("PATH STABILITY SCORING")
print("="*80)

# Create a composite stability score
df['stability_score'] = (
    (1 - df['jitter_pct'] / 100).clip(0, 1) * 0.5 +  # Jitter component (50%)
    (1 - df['packet_loss_pct'] / 100).clip(0, 1) * 0.5       # Loss component (50%)
)

# Compare different selection strategies
print(f"\nServer Selection Strategy Comparison:")
print(f"  (Simulated: Pick server for each probe)")

# Group by probe
probe_measurements = df.groupby('probe_id').filter(lambda x: len(x) > 1)
probes_with_choice = probe_measurements['probe_id'].nunique()

if probes_with_choice > 0:
    print(f"\n  Probes with multiple target measurements: {probes_with_choice}")
    
    # For each probe, compare selection strategies
    strategies = {
        'Min RTT': 'rtt_avg',
        'Min Loss': 'packet_loss_pct',
        'Min Jitter': 'jitter',
        'Max Stability': 'stability_score'
    }
    
    selection_results = {}
    for strategy_name, metric in strategies.items():
        if strategy_name == 'Max Stability':
            selections = probe_measurements.loc[probe_measurements.groupby('probe_id')[metric].idxmax()]
        else:
            selections = probe_measurements.loc[probe_measurements.groupby('probe_id')[metric].idxmin()]
        
        selection_results[strategy_name] = {
            'avg_rtt': selections['rtt_avg'].mean(),
            'avg_loss': selections['packet_loss_pct'].mean(),
            'avg_jitter': selections['jitter'].mean(),
            'avg_stability': selections['stability_score'].mean()
        }
    
    print(f"\n  Results by selection strategy:")
    print(f"  {'Strategy':20s} {'Avg RTT':>12s} {'Avg Loss':>12s} {'Avg Jitter':>12s} {'Stability':>12s}")
    print(f"  {'-'*20} {'-'*12} {'-'*12} {'-'*12} {'-'*12}")
    
    for strategy_name, results in selection_results.items():
        print(f"  {strategy_name:20s} {results['avg_rtt']:10.1f}ms "
              f"{results['avg_loss']:10.2f}% {results['avg_jitter']:10.1f}ms "
              f"{results['avg_stability']:10.3f}")
else:
    print(f"\n  ⚠️  No probes measured multiple targets - cannot simulate selection")

# Final summary
print("\n" + "="*80)
print("SUMMARY: JITTER AS A MULTI-METRIC SIGNAL")
print("="*80)

print(f"\n✓ Jitter (RTT variance) is a valuable signal:")
print(f"  - {len(problem_cases):,} cases ({len(problem_cases)/len(df)*100:.2f}%) have low RTT but high jitter")
print(f"  - RTT-jitter correlation: r={correlation:.3f} (independent enough to be useful)")
print(f"  - High jitter paths have {high_jitter['packet_loss_pct'].mean() - low_jitter['packet_loss_pct'].mean():+.2f}% more packet loss")

if len(problem_cases) > 500:
    print(f"\n🎯 SIGNIFICANT FINDING: Jitter reveals unstable paths that RTT misses!")
    print(f"   Multi-metric with jitter could avoid {len(problem_cases):,} problematic selections.")
elif len(problem_cases) > 100:
    print(f"\n⚠️  MODEST FINDING: Jitter matters in {len(problem_cases):,} cases")
    print(f"   Small but measurable benefit from including jitter.")
else:
    print(f"\n✗ LIMITED IMPACT: Only {len(problem_cases):,} problem cases found")
    print(f"  Jitter provides minimal additional signal beyond RTT.")

if probes_with_choice == 0:
    print(f"\n⚠️  LIMITATION: Cannot validate selection performance (no throughput data)")
    print(f"   Analysis shows theoretical benefit but cannot measure actual improvement.")

print("\n" + "="*80)
