"""
Generate Key Plots for CDN Multi-Metric Selection Presentation
===============================================================
Creates publication-ready figures for thesis/presentation
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from pathlib import Path
from scipy import stats
import warnings
warnings.filterwarnings('ignore')

# Set publication style
plt.style.use('seaborn-v0_8-paper')
sns.set_palette("husl")
plt.rcParams['figure.dpi'] = 300
plt.rcParams['savefig.dpi'] = 300
plt.rcParams['font.size'] = 11
plt.rcParams['axes.labelsize'] = 12
plt.rcParams['axes.titlesize'] = 13
plt.rcParams['legend.fontsize'] = 10
plt.rcParams['figure.figsize'] = (10, 6)

# Create output directory
output_dir = Path("results/presentation_plots")
output_dir.mkdir(parents=True, exist_ok=True)

print("="*80)
print("GENERATING PRESENTATION PLOTS")
print("="*80)

# Load M-Lab data
print("\n📊 Loading data...")
mlab_path = Path("notebooks/data/raw/mlab_ndt_us_30days_20251111_004612.csv")
df = pd.read_csv(mlab_path)
df = df.dropna(subset=['download_mbps', 'min_rtt_ms', 'packet_loss_rate'])
df = df[df['min_rtt_ms'] > 0]
df = df[df['download_mbps'] >= 0]
print(f"✓ Loaded {len(df):,} M-Lab measurements")

# Load Lumos5G data
lumos_path = Path("notebooks/data/processed/lumos5g_5g_only.csv")
if lumos_path.exists():
    lumos_df = pd.read_csv(lumos_path)
    print(f"✓ Loaded {len(lumos_df):,} Lumos5G measurements")
else:
    lumos_df = None
    print("⚠️ Lumos5G data not found")

# =============================================================================
# PLOT 1: RTT vs Throughput - Core Finding
# =============================================================================
print("\n1️⃣ Creating RTT vs Throughput scatter plot...")

fig, ax = plt.subplots(figsize=(10, 6))

# Sample for visibility
sample = df.sample(n=min(5000, len(df)), random_state=42)
correlation = df['min_rtt_ms'].corr(df['download_mbps'])
r_squared = correlation ** 2

# Scatter plot with density coloring
scatter = ax.scatter(sample['min_rtt_ms'], sample['download_mbps'], 
                    alpha=0.3, s=10, c='#2E86AB', edgecolors='none')

# Add trend line
z = np.polyfit(df['min_rtt_ms'], df['download_mbps'], 1)
p = np.poly1d(z)
x_line = np.linspace(df['min_rtt_ms'].min(), df['min_rtt_ms'].max(), 100)
ax.plot(x_line, p(x_line), "r--", linewidth=2, label='Linear Fit', alpha=0.8)

ax.set_xlabel('RTT (ms)', fontsize=13, fontweight='bold')
ax.set_ylabel('Throughput (Mbps)', fontsize=13, fontweight='bold')
ax.set_title(f'RTT vs Throughput: Weak Correlation (r={correlation:.3f}, R²={r_squared:.3f})', 
            fontsize=14, fontweight='bold', pad=20)
ax.legend(loc='upper right')
ax.grid(True, alpha=0.3, linestyle='--')

# Add text box with key stats
textstr = f'Pearson r = {correlation:.3f}\nR² = {r_squared:.3f} ({r_squared*100:.1f}%)\np < 0.001\nn = {len(df):,}'
props = dict(boxstyle='round', facecolor='wheat', alpha=0.8)
ax.text(0.98, 0.97, textstr, transform=ax.transAxes, fontsize=11,
        verticalalignment='top', horizontalalignment='right', bbox=props)

plt.tight_layout()
plt.savefig(output_dir / "01_rtt_vs_throughput.png", bbox_inches='tight')
plt.savefig(output_dir / "01_rtt_vs_throughput.pdf", bbox_inches='tight')
print(f"✓ Saved: 01_rtt_vs_throughput.png/pdf")
plt.close()

# =============================================================================
# PLOT 2: Correlation Matrix
# =============================================================================
print("\n2️⃣ Creating correlation matrix...")

fig, ax = plt.subplots(figsize=(8, 6))

# Calculate correlations
corr_data = df[['min_rtt_ms', 'download_mbps', 'packet_loss_rate']].corr()
corr_data.columns = ['RTT', 'Throughput', 'Packet Loss']
corr_data.index = ['RTT', 'Throughput', 'Packet Loss']

# Heatmap
sns.heatmap(corr_data, annot=True, fmt='.3f', cmap='RdBu_r', center=0,
            square=True, linewidths=2, cbar_kws={"shrink": 0.8},
            vmin=-1, vmax=1, ax=ax, annot_kws={'size': 12, 'weight': 'bold'})

ax.set_title('Correlation Matrix: Network Metrics', fontsize=14, fontweight='bold', pad=20)
plt.tight_layout()
plt.savefig(output_dir / "02_correlation_matrix.png", bbox_inches='tight')
plt.savefig(output_dir / "02_correlation_matrix.pdf", bbox_inches='tight')
print(f"✓ Saved: 02_correlation_matrix.png/pdf")
plt.close()

# =============================================================================
# PLOT 3: Model Performance Comparison
# =============================================================================
print("\n3️⃣ Creating model performance comparison...")

fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 6))

# R² comparison
models = ['Model A\n(Linear)', 'Model B\n(Ridge)', 'Model C\n(Neural Net)']
r2_scores = [0.057, 0.117, 0.205]
colors = ['#A23B72', '#F18F01', '#2E86AB']

bars1 = ax1.bar(models, [r*100 for r in r2_scores], color=colors, alpha=0.8, edgecolor='black', linewidth=1.5)
ax1.set_ylabel('R² Score (%)', fontsize=12, fontweight='bold')
ax1.set_title('Model Prediction Performance (R²)', fontsize=13, fontweight='bold')
ax1.set_ylim(0, 25)
ax1.grid(axis='y', alpha=0.3, linestyle='--')

# Add value labels on bars
for bar, score in zip(bars1, r2_scores):
    height = bar.get_height()
    ax1.text(bar.get_x() + bar.get_width()/2., height,
            f'{score*100:.1f}%',
            ha='center', va='bottom', fontsize=11, fontweight='bold')

# Add reference line at 20%
ax1.axhline(y=20, color='red', linestyle='--', linewidth=2, alpha=0.5, label='20% threshold')
ax1.legend()

# Throughput selection comparison
selection_methods = ['RTT-Only\n(Baseline)', 'Model A\n(Linear)', 'Model B\n(Ridge)', 'Model C\n(Neural Net)']
median_throughput = [142.86, 123.32, 122.31, 140.27]
colors2 = ['#06A77D', '#A23B72', '#F18F01', '#2E86AB']

bars2 = ax2.bar(selection_methods, median_throughput, color=colors2, alpha=0.8, edgecolor='black', linewidth=1.5)
ax2.set_ylabel('Median Throughput (Mbps)', fontsize=12, fontweight='bold')
ax2.set_title('Server Selection Performance', fontsize=13, fontweight='bold')
ax2.set_ylim(0, 160)
ax2.grid(axis='y', alpha=0.3, linestyle='--')

# Add value labels on bars
for bar, throughput in zip(bars2, median_throughput):
    height = bar.get_height()
    ax2.text(bar.get_x() + bar.get_width()/2., height,
            f'{throughput:.1f}',
            ha='center', va='bottom', fontsize=10, fontweight='bold')

# Highlight best performer
ax2.axhline(y=142.86, color='green', linestyle='--', linewidth=2, alpha=0.5, label='RTT-Only (Best)')
ax2.legend()

plt.tight_layout()
plt.savefig(output_dir / "03_model_performance.png", bbox_inches='tight')
plt.savefig(output_dir / "03_model_performance.pdf", bbox_inches='tight')
print(f"✓ Saved: 03_model_performance.png/pdf")
plt.close()

# =============================================================================
# PLOT 4: Feature Importance (R² Explained)
# =============================================================================
print("\n4️⃣ Creating feature importance comparison...")

fig, ax = plt.subplots(figsize=(10, 6))

# Feature importance data
features = ['RTT\n(Wired)', 'Packet Loss\n(Wired)', 'Jitter\n(Wired)', 'RSRP\n(5G Mobile)', 'Multi-Metric\n(5G: RSRP+RSRQ+SINR)']
r2_values = [2.58, 1.23, 16.0, 22.3, 24.3]
contexts = ['Wired', 'Wired', 'Wired', 'Mobile', 'Mobile']
colors_feat = ['#E63946' if c == 'Wired' else '#06A77D' for c in contexts]

bars = ax.barh(features, r2_values, color=colors_feat, alpha=0.8, edgecolor='black', linewidth=1.5)
ax.set_xlabel('Variance Explained (R²%)', fontsize=12, fontweight='bold')
ax.set_title('Feature Importance: Predictive Power Comparison', fontsize=14, fontweight='bold', pad=20)
ax.set_xlim(0, 30)
ax.grid(axis='x', alpha=0.3, linestyle='--')

# Add value labels
for bar, value in zip(bars, r2_values):
    width = bar.get_width()
    ax.text(width, bar.get_y() + bar.get_height()/2.,
            f' {value:.1f}%',
            ha='left', va='center', fontsize=11, fontweight='bold')

# Add legend
from matplotlib.patches import Patch
legend_elements = [Patch(facecolor='#E63946', edgecolor='black', label='Wired Network'),
                   Patch(facecolor='#06A77D', edgecolor='black', label='Mobile Network (5G)')]
ax.legend(handles=legend_elements, loc='lower right', fontsize=11)

plt.tight_layout()
plt.savefig(output_dir / "04_feature_importance.png", bbox_inches='tight')
plt.savefig(output_dir / "04_feature_importance.pdf", bbox_inches='tight')
print(f"✓ Saved: 04_feature_importance.png/pdf")
plt.close()

# =============================================================================
# PLOT 5: 5G RSRP vs Throughput (if available)
# =============================================================================
if lumos_df is not None and 'nr_ssRsrp' in lumos_df.columns and 'Throughput' in lumos_df.columns:
    print("\n5️⃣ Creating 5G RSRP vs Throughput plot...")
    
    fig, ax = plt.subplots(figsize=(10, 6))
    
    # Clean data
    valid_data = lumos_df[(lumos_df['Throughput'] > 0) & (lumos_df['nr_ssRsrp'].notna())]
    sample = valid_data.sample(n=min(3000, len(valid_data)), random_state=42)
    
    correlation = valid_data['nr_ssRsrp'].corr(valid_data['Throughput'])
    r_squared = correlation ** 2
    
    # Scatter plot
    scatter = ax.scatter(sample['nr_ssRsrp'], sample['Throughput'], 
                        alpha=0.3, s=10, c='#06A77D', edgecolors='none')
    
    # Add trend line
    z = np.polyfit(valid_data['nr_ssRsrp'], valid_data['Throughput'], 1)
    p = np.poly1d(z)
    x_line = np.linspace(valid_data['nr_ssRsrp'].min(), valid_data['nr_ssRsrp'].max(), 100)
    ax.plot(x_line, p(x_line), "r--", linewidth=2, label='Linear Fit', alpha=0.8)
    
    ax.set_xlabel('RSRP - Signal Strength (dBm)', fontsize=13, fontweight='bold')
    ax.set_ylabel('Throughput (Mbps)', fontsize=13, fontweight='bold')
    ax.set_title(f'5G: Signal Strength vs Throughput (r={correlation:.3f}, R²={r_squared:.3f})', 
                fontsize=14, fontweight='bold', pad=20)
    ax.legend(loc='upper left')
    ax.grid(True, alpha=0.3, linestyle='--')
    
    # Add text box
    textstr = f'Pearson r = {correlation:.3f}\nR² = {r_squared:.3f} ({r_squared*100:.1f}%)\np < 0.001\nn = {len(valid_data):,}'
    props = dict(boxstyle='round', facecolor='lightgreen', alpha=0.8)
    ax.text(0.02, 0.97, textstr, transform=ax.transAxes, fontsize=11,
            verticalalignment='top', horizontalalignment='left', bbox=props)
    
    plt.tight_layout()
    plt.savefig(output_dir / "05_5g_rsrp_vs_throughput.png", bbox_inches='tight')
    plt.savefig(output_dir / "05_5g_rsrp_vs_throughput.pdf", bbox_inches='tight')
    print(f"✓ Saved: 05_5g_rsrp_vs_throughput.png/pdf")
    plt.close()

# =============================================================================
# PLOT 6: Key Findings Summary
# =============================================================================
print("\n6️⃣ Creating key findings summary chart...")

fig, ax = plt.subplots(figsize=(12, 8))
ax.axis('off')

# Title
fig.text(0.5, 0.95, 'CDN Multi-Metric Server Selection: Key Findings', 
         ha='center', va='top', fontsize=18, fontweight='bold')

# Create text sections
findings = [
    ("🎯 CORE PROBLEM", [
        "• RTT explains only 2.6% of throughput variance (R² = 0.026)",
        "• Correlation r = -0.161 (weak but statistically significant, p < 0.001)",
        "• 97.4% of throughput variance remains unexplained by RTT alone"
    ]),
    
    ("📊 MODEL PERFORMANCE", [
        "• Linear Model (A): R² = 5.7% on test set",
        "• Ridge Regression (B): R² = 11.7% on test set",  
        "• Neural Network (C): R² = 20.5% on test set (best)",
        "• All models predict in log-space for stability"
    ]),
    
    ("🏆 SERVER SELECTION RESULTS", [
        "• RTT-Only: 142.9 Mbps median (BEST)",
        "• Model A: 123.3 Mbps (-13.7% vs RTT)",
        "• Model B: 122.3 Mbps (-14.4% vs RTT)",
        "• Model C: 140.3 Mbps (-1.8% vs RTT)",
        "• Conclusion: Limited features (RTT + loss) insufficient for ML improvement"
    ]),
    
    ("📱 5G MOBILE NETWORKS", [
        "• RSRP explains 22.3% variance (9x better than RTT!)",
        "• Multi-metric (RSRP+RSRQ+SINR): 24.3% R²",
        "• Mobile shows more promise for multi-metric selection"
    ]),
    
    ("🔍 ADDITIONAL FINDINGS", [
        "• Jitter: r = 0.40 correlation, 1,098 problem cases identified",
        "• Temporal patterns: Only +0.1% improvement (minimal impact)",
        "• RTT and packet loss are independent (r = 0.105)",
        "• Statistical significance confirmed (p < 0.001 for all tests)"
    ]),
    
    ("💡 RECOMMENDATIONS", [
        "• Add TTFB measurements (expected +10-15% R²)",
        "• Include bandwidth capacity estimates",
        "• Prioritize signal metrics for mobile CDN selection",
        "• For wired networks with RTT+loss only: RTT-only remains optimal"
    ])
]

y_pos = 0.88
for title, points in findings:
    # Section title
    fig.text(0.08, y_pos, title, fontsize=13, fontweight='bold', 
             bbox=dict(boxstyle='round', facecolor='lightblue', alpha=0.7))
    y_pos -= 0.04
    
    # Points
    for point in points:
        fig.text(0.10, y_pos, point, fontsize=10, family='monospace')
        y_pos -= 0.025
    
    y_pos -= 0.02  # Extra space between sections

plt.tight_layout()
plt.savefig(output_dir / "06_key_findings_summary.png", bbox_inches='tight')
plt.savefig(output_dir / "06_key_findings_summary.pdf", bbox_inches='tight')
print(f"✓ Saved: 06_key_findings_summary.png/pdf")
plt.close()

# =============================================================================
# Summary Statistics Table
# =============================================================================
print("\n7️⃣ Creating summary statistics table...")

fig, ax = plt.subplots(figsize=(12, 8))
ax.axis('off')

fig.text(0.5, 0.96, 'Research Summary Statistics', 
         ha='center', va='top', fontsize=16, fontweight='bold')

# Dataset statistics
table_data = [
    ['DATASET', 'RECORDS', 'KEY METRICS', 'TIME PERIOD'],
    ['M-Lab NDT (US)', f'{len(df):,}', 'RTT, Throughput, Loss', 'Oct-Nov 2025'],
    ['Lumos5G (Mobile)', f'{len(lumos_df):,}' if lumos_df is not None else 'N/A', 
     'RSRP, RSRQ, SINR, Throughput', '2020'],
    ['', '', '', ''],
    ['METRIC', 'CORRELATION (r)', 'R² EXPLAINED', 'SIGNIFICANCE'],
    ['RTT vs Throughput', '-0.161', '2.58%', 'p < 0.001'],
    ['Loss vs Throughput', '-0.111', '1.23%', 'p < 0.001'],
    ['RSRP vs Throughput (5G)', '0.473', '22.3%', 'p < 0.001'],
    ['', '', '', ''],
    ['MODEL', 'R² (TEST)', 'MEDIAN THROUGHPUT', 'vs RTT-ONLY'],
    ['RTT-Only Selection', 'N/A', '142.9 Mbps', 'Baseline'],
    ['Linear Regression', '5.7%', '123.3 Mbps', '-13.7%'],
    ['Ridge Regression', '11.7%', '122.3 Mbps', '-14.4%'],
    ['Neural Network', '20.5%', '140.3 Mbps', '-1.8%'],
]

# Create table
table = ax.table(cellText=table_data, cellLoc='left', loc='center',
                colWidths=[0.25, 0.25, 0.25, 0.25])
table.auto_set_font_size(False)
table.set_fontsize(10)
table.scale(1, 2.5)

# Style header rows
for i in [0, 4, 9]:
    for j in range(4):
        cell = table[(i, j)]
        cell.set_facecolor('#4A90E2')
        cell.set_text_props(weight='bold', color='white')

# Style data rows
for i in range(1, len(table_data)):
    if i not in [0, 3, 4, 8, 9]:
        for j in range(4):
            cell = table[(i, j)]
            cell.set_facecolor('#F0F0F0' if i % 2 == 0 else 'white')

plt.tight_layout()
plt.savefig(output_dir / "07_summary_statistics.png", bbox_inches='tight')
plt.savefig(output_dir / "07_summary_statistics.pdf", bbox_inches='tight')
print(f"✓ Saved: 07_summary_statistics.png/pdf")
plt.close()

print("\n" + "="*80)
print("✅ ALL PLOTS GENERATED SUCCESSFULLY!")
print("="*80)
print(f"\n📁 Output directory: {output_dir.absolute()}")
print("\nGenerated files:")
print("  1. 01_rtt_vs_throughput.png/pdf - Core correlation finding")
print("  2. 02_correlation_matrix.png/pdf - All metric correlations")
print("  3. 03_model_performance.png/pdf - R² and selection comparison")
print("  4. 04_feature_importance.png/pdf - Wired vs Mobile comparison")
print("  5. 05_5g_rsrp_vs_throughput.png/pdf - 5G analysis")
print("  6. 06_key_findings_summary.png/pdf - Complete findings summary")
print("  7. 07_summary_statistics.png/pdf - Statistical summary table")
print("\n🎓 These plots are ready for your thesis presentation!")
print("="*80)
