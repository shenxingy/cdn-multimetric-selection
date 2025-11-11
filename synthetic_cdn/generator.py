"""
Synthetic CDN Data Generator

This module generates synthetic CDN performance metrics including RTT, TTFB, 
packet loss, and throughput. The data models realistic CDN behavior with 
log-normal distributions for latency metrics and a non-linear relationship 
between network conditions and throughput.

Author: CDN Multi-Metric Selection Project
Date: November 2025
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns


# ============================================================================
# CONFIGURATION CONSTANTS
# ============================================================================

# Random seed for reproducibility
RANDOM_SEED = 42

# Number of synthetic samples to generate
N_SAMPLES = 500

# RTT Distribution Parameters (Log-Normal Distribution)
# Target mean RTT around 30ms, typical for CDN edge servers
RTT_MEAN_LOG = np.log(30)  # Logarithmic mean
RTT_SIGMA_LOG = 0.5         # Standard deviation controlling RTT spread

# Server Delay Distribution Parameters (Log-Normal Distribution)
# Target mean of 20ms with higher variance to simulate variable server load
DELAY_MEAN_LOG = np.log(20)
DELAY_SIGMA_LOG = 0.8

# Packet Loss Distribution Parameters
LOSS_PROBABILITY = 0.15  # Probability of experiencing packet loss (15%)
LOSS_MIN = 0.001         # Minimum loss rate (0.1%)
LOSS_MAX = 0.02          # Maximum loss rate (2%)

# Throughput Model Parameters
THROUGHPUT_CONSTANT = 10000  # Base constant for throughput scaling (Mbps)
LOSS_IMPACT_WEIGHT = 5000    # Weight factor for packet loss impact on throughput


# ============================================================================
# DATA GENERATION
# ============================================================================

def generate_synthetic_cdn_data():
    """
    Generate synthetic CDN performance metrics.
    
    This function creates realistic CDN metrics with the following characteristics:
    - RTT and server delay follow log-normal distributions
    - Packet loss occurs in 15% of samples with varying rates
    - Throughput is inversely related to latency and packet loss
    - TCP congestion control effects are modeled through amplified loss impact
    
    Returns:
        pd.DataFrame: DataFrame containing RTT, TTFB, Loss, and Throughput columns
    """
    # Set random seed for reproducibility
    np.random.seed(RANDOM_SEED)
    
    # Generate Round-Trip Time (RTT) using log-normal distribution
    # Log-normal distribution is appropriate for network latency measurements
    rtt = np.random.lognormal(mean=RTT_MEAN_LOG, sigma=RTT_SIGMA_LOG, size=N_SAMPLES)
    
    # Generate Server Delay to simulate variable server load
    # Higher variance represents unstable load conditions
    server_delay = np.random.lognormal(mean=DELAY_MEAN_LOG, sigma=DELAY_SIGMA_LOG, size=N_SAMPLES)
    
    # Calculate Time To First Byte (TTFB)
    # TTFB is the sum of network RTT and server processing delay
    ttfb = rtt + server_delay
    
    # Generate Packet Loss to simulate network congestion
    # Most samples (85%) have zero loss; remaining samples have variable loss rates
    loss = np.zeros(N_SAMPLES)
    lossy_indices = np.random.choice(
        N_SAMPLES, 
        size=int(N_SAMPLES * LOSS_PROBABILITY), 
        replace=False
    )
    loss[lossy_indices] = np.random.uniform(
        low=LOSS_MIN, 
        high=LOSS_MAX, 
        size=len(lossy_indices)
    )
    
    # Calculate Throughput using a ground truth model
    # This model simulates the combined impact of RTT, TTFB, and packet loss
    # Packet loss impact is amplified to model TCP congestion control behavior
    total_cost = rtt + ttfb + (loss * LOSS_IMPACT_WEIGHT)
    
    # Base throughput is inversely proportional to total network cost
    base_throughput = THROUGHPUT_CONSTANT / total_cost
    
    # Add random noise (±10% variation) to simulate real-world fluctuations
    noise = np.random.uniform(0.9, 1.1, size=N_SAMPLES)
    throughput = base_throughput * noise
    
    # Ensure throughput values remain positive
    throughput = np.maximum(throughput, 0.01)
    
    # Create DataFrame with all metrics
    data = {
        'RTT': rtt,
        'TTFB': ttfb,
        'Loss': loss,
        'Throughput': throughput
    }
    
    return pd.DataFrame(data)


# ============================================================================
# VISUALIZATION
# ============================================================================

def visualize_data(df, output_file='data-visualization.png'):
    """
    Create and save a scatter plot visualization of RTT vs. Throughput.
    
    This visualization helps verify the synthetic data generation by showing
    the expected negative correlation between RTT and throughput, with
    significant noise demonstrating that RTT alone cannot predict throughput.
    
    Args:
        df (pd.DataFrame): DataFrame containing the synthetic CDN metrics
        output_file (str): Path to save the visualization (default: 'data-visualization.png')
    """
    plt.figure(figsize=(10, 6))
    sns.scatterplot(data=df, x='RTT', y='Throughput', alpha=0.5)
    plt.title('RTT vs. Throughput (Synthetic CDN Data)', fontsize=14, fontweight='bold')
    plt.xlabel('Round-Trip Time (ms)', fontsize=12)
    plt.ylabel('Throughput (Mbps)', fontsize=12)
    plt.grid(True, alpha=0.3)
    plt.tight_layout()
    plt.savefig(output_file, dpi=300, bbox_inches='tight')
    plt.close()


# ============================================================================
# MAIN EXECUTION
# ============================================================================

def main():
    """
    Main execution function for synthetic CDN data generation.
    
    This function orchestrates the data generation process, saves the results
    to a CSV file, and displays summary statistics and visualizations.
    """
    print("=" * 70)
    print("SYNTHETIC CDN DATA GENERATOR")
    print("=" * 70)
    
    # Generate synthetic data
    print(f"\nGenerating {N_SAMPLES} synthetic CDN samples...")
    df = generate_synthetic_cdn_data()
    
    # Save to CSV file
    output_file = 'synthetic_cdn_data.csv'
    df.to_csv(output_file, index=False)
    print(f"✓ Successfully saved data to '{output_file}'")
    
    # Display summary statistics
    print("\n" + "=" * 70)
    print("SUMMARY STATISTICS")
    print("=" * 70)
    print(df.describe())
    
    # Display correlation insights
    print("\n" + "=" * 70)
    print("DATA CHARACTERISTICS")
    print("=" * 70)
    print(f"• Samples with packet loss: {(df['Loss'] > 0).sum()} ({(df['Loss'] > 0).sum()/N_SAMPLES*100:.1f}%)")
    print(f"• Mean RTT: {df['RTT'].mean():.2f} ms")
    print(f"• Mean TTFB: {df['TTFB'].mean():.2f} ms")
    print(f"• Mean Throughput: {df['Throughput'].mean():.2f} Mbps")
    print(f"• RTT-Throughput Correlation: {df['RTT'].corr(df['Throughput']):.3f}")
    
    # Create and save visualization
    print("\n" + "=" * 70)
    print("GENERATING VISUALIZATION")
    print("=" * 70)
    visualization_file = 'data-visualization.png'
    print(f"Creating RTT vs. Throughput scatter plot...")
    visualize_data(df, output_file=visualization_file)
    print(f"✓ Successfully saved visualization to '{visualization_file}'")
    print("\nNote: The plot shows a noisy negative correlation, demonstrating that")
    print("      RTT alone is insufficient for predicting throughput.")


if __name__ == "__main__":
    main()