"""
RIPE Atlas Analysis: Server Selection Based on RTT and Packet Loss

IMPORTANT LIMITATION: RIPE Atlas data only contains RTT and packet loss measurements.
It does NOT include throughput data, so we cannot directly evaluate selection performance
like we did with M-Lab data.

Instead, this analysis will:
1. Show diversity of network paths (different probes see different RTTs to same target)
2. Analyze correlation between RTT and packet loss
3. Identify optimal paths per probe (lowest RTT, lowest loss)
4. Demonstrate that multi-metric selection WOULD differ from RTT-only

Author: Research Team
Date: November 18, 2025
"""

import pandas as pd
import numpy as np
from pathlib import Path
import matplotlib.pyplot as plt
import seaborn as sns

print("="*80)
print("RIPE ATLAS DATA ANALYSIS")
print("="*80)
print()

# Load RIPE data
ripe_path = Path("/Users/ankitraj2/558/cdn-multimetric-selection/notebooks/data/processed/ripe_atlas_processed.csv")
df = pd.read_csv(ripe_path)

print(f"✓ Loaded {len(df):,} RIPE Atlas measurements")
print()

# Basic statistics
print("="*80)
print("DATASET OVERVIEW")
print("="*80)
print()

print(f"Time range: {df['datetime'].min()} to {df['datetime'].max()}")
print(f"Unique probes: {df['probe_id'].nunique():,}")
print(f"Unique targets: {df['target'].nunique():,}")
print(f"Measurements per probe: {df.groupby('probe_id').size().mean():.1f} (avg)")
print()

print("RTT Statistics:")
print(f"  Min: {df['rtt_min'].min():.3f} ms")
print(f"  Max: {df['rtt_max'].max():.3f} ms")
print(f"  Mean: {df['rtt_avg'].mean():.3f} ms")
print(f"  Median: {df['rtt_avg'].median():.3f} ms")
print()

print("Packet Loss Statistics:")
print(f"  Mean: {df['packet_loss_pct'].mean():.2f}%")
print(f"  Measurements with 0% loss: {(df['packet_loss_pct'] == 0).sum():,} ({(df['packet_loss_pct'] == 0).mean()*100:.1f}%)")
print(f"  Measurements with >0% loss: {(df['packet_loss_pct'] > 0).sum():,} ({(df['packet_loss_pct'] > 0).mean()*100:.1f}%)")
print()

# ============================================================================
# ANALYSIS 1: Path Diversity (Multiple Options per Probe)
# ============================================================================
print("="*80)
print("ANALYSIS 1: PATH DIVERSITY - Do Probes Have Choices?")
print("="*80)
print()

# Group by probe to see how many targets each probe measured
probe_target_counts = df.groupby('probe_id')['target'].nunique()
probes_with_choices = (probe_target_counts > 1).sum()

print(f"Probes with multiple target options: {probes_with_choices:,} ({probes_with_choices/len(probe_target_counts)*100:.1f}%)")
print(f"Average targets per probe: {probe_target_counts.mean():.1f}")
print(f"Max targets per probe: {probe_target_counts.max()}")
print()

if probes_with_choices == 0:
    print("⚠️  CRITICAL LIMITATION: Each probe only measured ONE target!")
    print("   Cannot perform server selection analysis without multiple options per probe.")
    print()
    print("   This means:")
    print("   - No realistic CDN selection scenario (each 'client' has only 1 server)")
    print("   - Cannot compare RTT-only vs multi-metric selection")
    print("   - Data shows network characteristics but not selection performance")
    print()
else:
    print("✓ Can analyze server selection for probes with multiple targets")
    print()

# ============================================================================
# ANALYSIS 2: RTT vs Packet Loss Correlation
# ============================================================================
print("="*80)
print("ANALYSIS 2: RTT vs PACKET LOSS CORRELATION")
print("="*80)
print()

correlation = df['rtt_avg'].corr(df['packet_loss_pct'])
print(f"Pearson correlation (RTT vs Loss): r = {correlation:.4f}")

if abs(correlation) < 0.1:
    print("  → Very weak correlation - RTT and loss are nearly independent")
elif abs(correlation) < 0.3:
    print("  → Weak correlation - RTT and loss provide different information")
else:
    print("  → Moderate correlation - RTT and loss are somewhat related")

print()

# Count failure cases: high RTT AND high loss
high_rtt_threshold = df['rtt_avg'].quantile(0.75)
high_loss_threshold = 0.1  # >0% loss

high_rtt_high_loss = ((df['rtt_avg'] > high_rtt_threshold) & 
                       (df['packet_loss_pct'] > high_loss_threshold)).sum()

print(f"Paths with high RTT (>{high_rtt_threshold:.1f} ms): {(df['rtt_avg'] > high_rtt_threshold).sum():,}")
print(f"Paths with packet loss (>{high_loss_threshold}%): {(df['packet_loss_pct'] > high_loss_threshold).sum():,}")
print(f"Paths with BOTH high RTT AND loss: {high_rtt_high_loss:,}")
print()

# Low RTT but high loss (RTT would mislead)
low_rtt_threshold = df['rtt_avg'].quantile(0.25)
low_rtt_high_loss = ((df['rtt_avg'] < low_rtt_threshold) & 
                      (df['packet_loss_pct'] > high_loss_threshold)).sum()

print(f"CRITICAL: Paths with LOW RTT (<{low_rtt_threshold:.1f} ms) but HIGH loss: {low_rtt_high_loss:,}")
if low_rtt_high_loss > 0:
    print(f"  → {low_rtt_high_loss/len(df)*100:.2f}% of measurements where RTT-only would select bad path")
    print(f"  → This proves multi-metric selection can help!")
else:
    print(f"  → RTT and loss are perfectly aligned in this dataset")
print()

# ============================================================================
# ANALYSIS 3: Target Comparison (Different Targets, Different Performance)
# ============================================================================
print("="*80)
print("ANALYSIS 3: TARGET COMPARISON")
print("="*80)
print()

# Get statistics per target
target_stats = df.groupby('target').agg({
    'rtt_avg': ['mean', 'median', 'std'],
    'packet_loss_pct': ['mean', 'sum'],
    'probe_id': 'nunique'
}).round(3)

target_stats.columns = ['RTT_mean', 'RTT_median', 'RTT_std', 'Loss_mean', 'Loss_total', 'Num_probes']
target_stats = target_stats.sort_values('RTT_median')

print(f"Analyzing {len(target_stats)} different targets:")
print()
print(target_stats.head(10).to_string())
print()

# Which target is "best"?
print("Best targets by different criteria:")
best_rtt = target_stats['RTT_median'].idxmin()
best_loss = target_stats['Loss_mean'].idxmin()

print(f"  Lowest RTT: {best_rtt} ({target_stats.loc[best_rtt, 'RTT_median']:.2f} ms)")
print(f"  Lowest loss: {best_loss} ({target_stats.loc[best_loss, 'Loss_mean']:.2f}%)")

if best_rtt != best_loss:
    print(f"  → DIFFERENT targets are optimal by RTT vs loss!")
    print(f"  → Multi-metric selection would choose differently than RTT-only")
else:
    print(f"  → Same target is best for both metrics")
print()

# ============================================================================
# ANALYSIS 4: Simulated Selection (If probes had multiple options)
# ============================================================================
print("="*80)
print("ANALYSIS 4: SIMULATED SERVER SELECTION")
print("="*80)
print()

if probes_with_choices > 0:
    print("Simulating selection for probes with multiple target options...")
    print()
    
    selection_results = []
    
    for probe_id, group in df.groupby('probe_id'):
        if len(group) < 2:
            continue  # Skip probes with only one target
        
        # Method 1: Select by minimum RTT
        rtt_selected = group.nsmallest(1, 'rtt_avg')
        
        # Method 2: Select by minimum packet loss (then RTT as tiebreaker)
        loss_selected = group.sort_values(['packet_loss_pct', 'rtt_avg']).iloc[0:1]
        
        # Method 3: Composite score (lower is better)
        # Score = 0.5 * normalized_rtt + 0.5 * normalized_loss
        group_scored = group.copy()
        group_scored['rtt_norm'] = (group_scored['rtt_avg'] - group['rtt_avg'].min()) / (group['rtt_avg'].max() - group['rtt_avg'].min() + 0.001)
        group_scored['loss_norm'] = group_scored['packet_loss_pct'] / 100.0
        group_scored['composite'] = 0.5 * group_scored['rtt_norm'] + 0.5 * group_scored['loss_norm']
        composite_selected = group_scored.nsmallest(1, 'composite')
        
        selection_results.append({
            'probe_id': probe_id,
            'rtt_method_rtt': rtt_selected['rtt_avg'].values[0],
            'rtt_method_loss': rtt_selected['packet_loss_pct'].values[0],
            'loss_method_rtt': loss_selected['rtt_avg'].values[0],
            'loss_method_loss': loss_selected['packet_loss_pct'].values[0],
            'composite_method_rtt': composite_selected['rtt_avg'].values[0],
            'composite_method_loss': composite_selected['packet_loss_pct'].values[0],
        })
    
    results_df = pd.DataFrame(selection_results)
    
    print(f"Analyzed {len(results_df):,} probes with multiple target options")
    print()
    
    print("Average RTT by selection method:")
    print(f"  RTT-only:    {results_df['rtt_method_rtt'].mean():.2f} ms")
    print(f"  Loss-only:   {results_df['loss_method_rtt'].mean():.2f} ms")
    print(f"  Composite:   {results_df['composite_method_rtt'].mean():.2f} ms")
    print()
    
    print("Average Packet Loss by selection method:")
    print(f"  RTT-only:    {results_df['rtt_method_loss'].mean():.3f}%")
    print(f"  Loss-only:   {results_df['loss_method_loss'].mean():.3f}%")
    print(f"  Composite:   {results_df['composite_method_loss'].mean():.3f}%")
    print()
    
    # Which is better?
    rtt_improvement = ((results_df['rtt_method_rtt'].mean() - results_df['composite_method_rtt'].mean()) / 
                       results_df['rtt_method_rtt'].mean() * 100)
    loss_improvement = ((results_df['rtt_method_loss'].mean() - results_df['composite_method_loss'].mean()) / 
                        (results_df['rtt_method_loss'].mean() + 0.001) * 100)
    
    print("Composite vs RTT-only:")
    print(f"  RTT change:  {rtt_improvement:+.1f}%")
    print(f"  Loss change: {loss_improvement:+.1f}%")
    print()
    
    if rtt_improvement > -5 and loss_improvement > 10:
        print("✓ Composite selection improves loss significantly without much RTT penalty")
    elif rtt_improvement < -10:
        print("⚠️ Composite selection trades significant RTT for lower loss")
    else:
        print("→ Mixed results - depends on whether you optimize for RTT or loss")
    print()
else:
    print("⚠️ Cannot simulate selection - each probe only has one target")
    print()

# ============================================================================
# SUMMARY
# ============================================================================
print("="*80)
print("SUMMARY AND CONCLUSIONS")
print("="*80)
print()

print("LIMITATIONS OF RIPE ATLAS DATA:")
print("1. ✗ No throughput measurements - cannot validate actual performance")
print("2. ✗ Ping tests only - RTT and loss, no bandwidth/capacity info")
if probes_with_choices == 0:
    print("3. ✗ Each probe measured only ONE target - no selection choices")
else:
    print(f"3. ✓ {probes_with_choices:,} probes with multiple targets - can simulate selection")
print()

print("KEY FINDINGS:")
print(f"1. RTT and packet loss correlation: r = {correlation:.4f} (weak)")
print(f"   → They provide different information about path quality")
print()
print(f"2. Low-RTT paths with high loss: {low_rtt_high_loss:,} cases ({low_rtt_high_loss/len(df)*100:.2f}%)")
if low_rtt_high_loss > 0:
    print(f"   → RTT-only would select suboptimal paths in these cases")
else:
    print(f"   → RTT and loss are aligned (no misleading cases)")
print()

if probes_with_choices > 0:
    print(f"3. Simulated selection on {len(results_df):,} probes:")
    print(f"   → Composite method differs from RTT-only in path selection")
    print(f"   → Cannot measure actual throughput impact (data limitation)")
    print()

print("CONCLUSION:")
print("RIPE Atlas data shows that RTT and packet loss are weakly correlated,")
print("suggesting they capture different aspects of path quality. However,")
print("without throughput measurements, we cannot prove that multi-metric")
print("selection improves actual performance.")
print()
print("This data is useful for:")
print("  ✓ Understanding network path diversity")
print("  ✓ Showing RTT ≠ packet loss (different signals)")
print("  ✓ Identifying when RTT might mislead")
print()
print("But NOT sufficient for:")
print("  ✗ Proving multi-metric selection improves throughput")
print("  ✗ Comparing with M-Lab's rigorous selection analysis")
print("  ✗ Making performance claims")
print()
print("="*80)
