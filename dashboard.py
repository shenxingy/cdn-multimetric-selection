"""
CDN Multi-Metric Server Selection - Interactive Dashboard
Streamlit app to visualize research results
"""

import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import json
import glob
from pathlib import Path

# Page configuration
st.set_page_config(
    page_title="CDN Multi-Metric Selection Dashboard",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
<style>
    .main-header {
        font-size: 3rem;
        font-weight: bold;
        color: #4a9eff;
        text-align: center;
        margin-bottom: 0.5rem;
    }
    .sub-header {
        font-size: 1.5rem;
        color: #e0e0e0;
        text-align: center;
        margin-bottom: 2rem;
    }
    .metric-card {
        background-color: #2b2b2b;
        color: #f0f0f0;
        padding: 1.5rem;
        border-radius: 0.5rem;
        border-left: 4px solid #4a9eff;
    }
    .highlight-box {
        background-color: #1a3a52;
        color: #f0f0f0;
        padding: 1rem;
        border-radius: 0.5rem;
        border-left: 4px solid #4caf50;
    }
    .stMetric {
        background-color: #2b2b2b;
        color: #f0f0f0;
        padding: 1rem;
        border-radius: 0.5rem;
    }
    h1, h2, h3, h4, h5, h6 {
        color: #f0f0f0;
    }
    p, li {
        color: #e0e0e0;
    }
</style>
""", unsafe_allow_html=True)

# Load data function with caching
@st.cache_data
def load_mlab_data():
    """Load M-Lab dataset, discovering the file via glob to avoid hardcoded filenames."""
    candidates = sorted(Path("data/raw").glob("mlab_ndt_*.csv"))
    if not candidates:
        # Fall back to notebooks mirror location
        candidates = sorted(Path("notebooks/data/raw").glob("mlab_ndt_*.csv"))
    if not candidates:
        st.error("M-Lab data file not found. Run src/utils/mlab_data_collector.py first.")
        return pd.DataFrame()
    try:
        df = pd.read_csv(candidates[-1])
        df['date'] = pd.to_datetime(df['date'])
        return df
    except Exception as e:
        st.error(f"Failed to load M-Lab data: {e}")
        return pd.DataFrame()

@st.cache_data
def load_ripe_data():
    """Load RIPE Atlas data"""
    ripe_files = glob.glob('notebooks/data/raw/RIPE-Atlas-measurement-*.json')
    
    if not ripe_files:
        return pd.DataFrame()
    
    ripe_data = []
    for file in ripe_files:
        with open(file, 'r') as f:
            for line in f:
                if line.strip():
                    try:
                        data = json.loads(line)
                        record = {
                            'timestamp': data.get('timestamp'),
                            'target': data.get('dst_name'),
                            'probe_id': data.get('prb_id'),
                            'rtt_avg': data.get('avg'),
                            'rtt_min': data.get('min'),
                            'rtt_max': data.get('max'),
                            'packets_sent': data.get('sent'),
                            'packets_rcvd': data.get('rcvd'),
                        }
                        if record['packets_sent'] and record['packets_sent'] > 0:
                            record['packet_loss_pct'] = ((record['packets_sent'] - record['packets_rcvd']) / record['packets_sent']) * 100
                        else:
                            record['packet_loss_pct'] = 0
                        ripe_data.append(record)
                    except json.JSONDecodeError:
                        continue
    
    return pd.DataFrame(ripe_data)

@st.cache_data
def load_lumos5g_data():
    """Load Lumos5G dataset"""
    try:
        df = pd.read_csv('notebooks/data/processed/lumos5g_5g_only.csv')
        return df
    except FileNotFoundError:
        return pd.DataFrame()

@st.cache_data
def calculate_composite_scores(df):
    """Calculate normalized scores and composite score"""
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
    
    df['rtt_score'] = normalize_metric(df['min_rtt_ms'], lower_is_better=True)
    df['throughput_score'] = normalize_metric(df['download_mbps'], lower_is_better=False)
    df['loss_score'] = normalize_metric(df['packet_loss_rate'], lower_is_better=True)
    df['composite_score'] = (0.3 * df['rtt_score'] + 0.4 * df['throughput_score'] + 0.3 * df['loss_score'])
    
    return df

def simulate_selection_comparison(df, n_simulations=1000):
    """Simulate RTT-only vs Multi-metric selection"""
    np.random.seed(42)
    
    rtt_throughputs = []
    multi_throughputs = []
    
    for _ in range(n_simulations):
        sample = df.sample(n=min(100, len(df)), replace=True)
        
        # RTT-only selection
        rtt_selected = sample.nsmallest(1, 'min_rtt_ms')
        rtt_throughputs.append(rtt_selected['download_mbps'].values[0])
        
        # Multi-metric selection
        multi_selected = sample.nlargest(1, 'composite_score')
        multi_throughputs.append(multi_selected['download_mbps'].values[0])
    
    return np.array(rtt_throughputs), np.array(multi_throughputs)

# Sidebar
with st.sidebar:
    st.image("https://img.icons8.com/color/96/000000/network.png", width=80)
    st.title("Navigation")
    
    page = st.radio(
        "Select View:",
        ["Executive Summary",
         "Dataset Overview", 
         "Correlation Analysis",
         "Performance Comparison",
         "Statistical Validation",
         "Geographic Analysis",
         "RIPE Atlas CDN Comparison",
         "5G Analysis (Lumos5G)",
         "Variable Importance & Comparison",
         "Interactive Simulator"]
    )
    
    st.markdown("---")
    st.markdown("### About")
    st.info("""
    This dashboard presents comprehensive results from our research on 
    **Multi-Metric CDN Server Selection**.
    
    **Key Finding:** RTT explains only 2.6% of throughput variance; rigorous analysis shows RTT-only currently performs best with limited features.
    """)

# Main content
st.markdown('<div class="main-header">CDN Multi-Metric Server Selection</div>', unsafe_allow_html=True)
st.markdown('<div class="sub-header">Research Dashboard - November 2025</div>', unsafe_allow_html=True)

# Load data
mlab_df = load_mlab_data()
ripe_df = load_ripe_data()
lumos_df = load_lumos5g_data()

if not mlab_df.empty:
    mlab_df = calculate_composite_scores(mlab_df)

# Page content
if page == "Executive Summary":
    st.header("Executive Summary")
    
    # Key metrics
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric(
            label="Total Measurements",
            value=f"{len(mlab_df) + len(ripe_df) + len(lumos_df):,}",
            delta="3 datasets combined"
        )
    
    with col2:
        st.metric(
            label="Best Model R²",
            value="20.5%",
            delta="Neural Network"
        )
    
    with col3:
        st.metric(
            label="RTT-Only Wins",
            value="142.9 Mbps",
            delta="Best method"
        )
    
    with col4:
        st.metric(
            label="Statistical Significance",
            value="p < 0.001",
            delta="Highly significant"
        )
    
    st.markdown("---")
    
    # Key findings
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.subheader("Key Findings")
        
        st.markdown("""
        <div class="highlight-box">
        <h4>Key Research Findings</h4>
        <ul>
            <li><strong>RTT explains only 2.6% of throughput variance</strong> (R² = 0.026)</li>
            <li>Correlation: r = -0.161 (weak but statistically significant, p < 0.001)</li>
            <li>Packet loss explains 1.2% of variance (R² = 0.012)</li>
            <li>Combined features show <strong>low predictability</strong> (R² < 21%)</li>
        </ul>
        
        <h4>Model Performance</h4>
        <ul>
            <li><strong>Model A (Linear):</strong> R² = 5.7% on test set</li>
            <li><strong>Model B (Ridge):</strong> R² = 11.7% on test set</li>
            <li><strong>Model C (Neural Net):</strong> R² = 20.5% on test set</li>
            <li>All models predict in log-space for throughput stability</li>
        </ul>
        
        <h4>Server Selection Results</h4>
        <ul>
            <li><strong>RTT-only selection:</strong> 142.9 Mbps median (current baseline)</li>
            <li><strong>ML-based selection:</strong> Performs 1.8-14.4% worse than RTT-only</li>
            <li><strong>Methodology:</strong> Grouped by client (lat/lon/ASN) for realistic scenarios</li>
            <li><strong>Current Conclusion:</strong> With limited features (RTT + loss), RTT-only remains most reliable</li>
        </ul>
        
        <h4>5G Mobile Networks (Lumos5G)</h4>
        <ul>
            <li><strong>RSRP (signal strength)</strong> explains 22.3% of variance</li>
            <li>Multi-metric (RSRP+RSRQ+SINR): 24.3% R²</li>
            <li>Mobile networks show more potential for multi-metric approaches</li>
        </ul>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.subheader("📚 Datasets")
        
        st.markdown(f"""
        **M-Lab NDT (US)**
        - Records: {len(mlab_df):,}
        - Period: Oct-Nov 2025
        - Metrics: RTT, Throughput, Loss
        
        **RIPE Atlas (Global)**
        - Records: {len(ripe_df):,}
        - Period: Nov 13-14, 2025
        - Metrics: RTT, Packet Loss
        
        **Lumos5G (Mobile)**
        - Records: {len(lumos_df):,}
        - Period: 2020
        - Metrics: Signal, Throughput
        """)
        
        st.markdown("---")
        
        st.subheader("📖 Documentation")
        st.markdown("""
        - [Results Report](RESULTS.md)
        - [Discussion & Limitations](DISCUSSION_AND_LIMITATIONS.md)
        - [Project Completion](PROJECT_COMPLETION.md)
        """)

elif page == "Dataset Overview":
    st.header("Dataset Overview")
    
    tab1, tab2, tab3 = st.tabs(["M-Lab", "RIPE Atlas", "Lumos5G"])
    
    with tab1:
        st.subheader("M-Lab NDT Dataset (US)")
        
        if not mlab_df.empty:
            col1, col2 = st.columns(2)
            
            with col1:
                st.metric("Total Records", f"{len(mlab_df):,}")
                st.metric("Date Range", f"{mlab_df['date'].min().date()} to {mlab_df['date'].max().date()}")
                st.metric("Unique Cities", f"{mlab_df['client_city'].nunique():,}")
            
            with col2:
                st.metric("Mean Throughput", f"{mlab_df['download_mbps'].mean():.2f} Mbps")
                st.metric("Mean RTT", f"{mlab_df['min_rtt_ms'].mean():.2f} ms")
                st.metric("Mean Packet Loss", f"{mlab_df['packet_loss_rate'].mean()*100:.2f}%")
            
            st.markdown("---")
            
            # Distribution plots
            col1, col2 = st.columns(2)
            
            with col1:
                fig = px.histogram(mlab_df, x='download_mbps', nbins=50,
                                 title='Throughput Distribution',
                                 labels={'download_mbps': 'Throughput (Mbps)'})
                fig.update_layout(showlegend=False)
                st.plotly_chart(fig, use_container_width=True)
            
            with col2:
                fig = px.histogram(mlab_df, x='min_rtt_ms', nbins=50,
                                 title='RTT Distribution',
                                 labels={'min_rtt_ms': 'RTT (ms)'})
                fig.update_layout(showlegend=False)
                st.plotly_chart(fig, use_container_width=True)
            
            # Sample data
            st.subheader("Sample Data")
            st.dataframe(mlab_df.head(100), use_container_width=True)
    
    with tab2:
        st.subheader("RIPE Atlas Dataset (Global)")
        
        if not ripe_df.empty:
            col1, col2 = st.columns(2)
            
            with col1:
                st.metric("Total Records", f"{len(ripe_df):,}")
                st.metric("Unique Targets", f"{ripe_df['target'].nunique()}")
                st.metric("Unique Probes", f"{ripe_df['probe_id'].nunique()}")
            
            with col2:
                st.metric("Mean RTT", f"{ripe_df['rtt_avg'].mean():.2f} ms")
                st.metric("Mean Packet Loss", f"{ripe_df['packet_loss_pct'].mean():.2f}%")
            
            # Sample data
            st.subheader("Sample Data")
            st.dataframe(ripe_df.head(100), use_container_width=True)
    
    with tab3:
        st.subheader("Lumos5G Dataset (Mobile 5G)")
        
        if not lumos_df.empty:
            col1, col2 = st.columns(2)
            
            with col1:
                st.metric("Total Records", f"{len(lumos_df):,}")
                if 'Throughput' in lumos_df.columns:
                    st.metric("Mean Throughput", f"{lumos_df['Throughput'].mean():.2f} Mbps")
            
            with col2:
                if 'nr_ssRsrp' in lumos_df.columns:
                    st.metric("Mean RSRP", f"{lumos_df['nr_ssRsrp'].mean():.2f} dBm")
            
            # Sample data
            st.subheader("Sample Data")
            st.dataframe(lumos_df.head(100), use_container_width=True)

elif page == "Correlation Analysis":
    st.header("Correlation Analysis")
    
    if not mlab_df.empty:
        st.subheader("M-Lab: RTT vs Throughput")
        
        # Calculate correlation
        correlation = mlab_df['min_rtt_ms'].corr(mlab_df['download_mbps'])
        r_squared = correlation ** 2
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric("Pearson Correlation (r)", f"{correlation:.4f}")
        with col2:
            st.metric("R² (Variance Explained)", f"{r_squared*100:.2f}%")
        with col3:
            st.metric("p-value", "< 0.001")
        
        st.markdown(f"""
        <div class="highlight-box">
        <h4>Key Insight</h4>
        RTT explains only <strong>{r_squared*100:.1f}% of throughput variance</strong>. 
        This proves that RTT alone is insufficient for server selection!
        </div>
        """, unsafe_allow_html=True)
        
        # Scatter plot
        fig = px.scatter(mlab_df.sample(n=min(5000, len(mlab_df))), 
                        x='min_rtt_ms', 
                        y='download_mbps',
                        opacity=0.3,
                        title=f'RTT vs Throughput (r={correlation:.3f}, R²={r_squared:.4f})',
                        labels={'min_rtt_ms': 'RTT (ms)', 'download_mbps': 'Throughput (Mbps)'})
        
        # Add trend line
        from scipy import stats
        slope, intercept, r_value, p_value, std_err = stats.linregress(
            mlab_df['min_rtt_ms'], mlab_df['download_mbps']
        )
        line_x = np.array([mlab_df['min_rtt_ms'].min(), mlab_df['min_rtt_ms'].max()])
        line_y = slope * line_x + intercept
        
        fig.add_trace(go.Scatter(x=line_x, y=line_y, mode='lines', 
                                name='Linear Fit', 
                                line=dict(color='red', width=2)))
        
        st.plotly_chart(fig, use_container_width=True)
        
        # Correlation matrix
        st.subheader("Correlation Matrix")
        
        corr_data = mlab_df[['min_rtt_ms', 'download_mbps', 'packet_loss_rate']].corr()
        
        fig = px.imshow(corr_data, 
                       text_auto='.3f',
                       aspect='auto',
                       title='Correlation Heatmap',
                       color_continuous_scale='RdBu_r',
                       zmin=-1, zmax=1)
        st.plotly_chart(fig, use_container_width=True)
        
        # Statistical validation
        st.subheader("Statistical Validation")
        
        st.markdown("""
        | Method | RTT vs Throughput | Loss vs Throughput | RTT vs Loss |
        |--------|-------------------|-------------------|-------------|
        | **Pearson r** | -0.161 | -0.111 | 0.105 |
        | **R²** | 2.58% | 1.23% | 1.09% |
        | **Spearman ρ** | -0.271 | -0.035 | (calculated) |
        | **p-value** | < 0.001 | < 0.001 | < 0.001 |
        | **95% CI** | [-0.173, -0.150] | [-0.118, -0.104] | N/A |
        
        **✓ All correlations are statistically significant but weak**
        
        **✓ RTT and Loss are largely independent (r=0.105)**
        
        **✓ This validates combining them in a composite score**
        """)

elif page == "Performance Comparison":
    st.title("Performance Comparison: Rigorous Server Selection Analysis")
    
    st.markdown("""
    ### Methodology
    
    This analysis uses a rigorous approach from `Data-Analysis/experiments.py` that:
    - Groups measurements by **exact client** (latitude, longitude, ASN)
    - Each group represents real server options available to that specific client
    - Models predict throughput for each option
    - Selection is based on predictions, **not actual throughput** (no future knowledge)
    
    **Key difference from naive approaches:**
    - No temporal advantage (train/test on same time period)
    - No cherry-picking of favorable scenarios
    - Models must work across all clients, not just easy cases
    """)
    
    if not mlab_df.empty:
        # Display results from the rigorous analysis (Data-Analysis/result)
        st.markdown("### Results from Rigorous Analysis")
        
        # Results table
        results_data = {
            'Method': ['RTT-Only (Baseline)', 'Model A - Linear Regression', 'Model B - Ridge Regression', 'Model C - Neural Network'],
            'Median Mbps': [142.86, 123.32, 122.31, 140.27],
            'P90 Mbps': [605.12, 546.73, 542.86, 592.71],
            'Change vs RTT (%)': [0.0, -13.67, -14.38, -1.81],
            'R² (Test)': ['-', '5.7%', '11.7%', '20.5%']
        }
        results_df = pd.DataFrame(results_data)
        
        # Metrics
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("RTT-Only Median", "142.9 Mbps", delta="✓ BEST")
        with col2:
            st.metric("Best ML Model", "140.3 Mbps", delta="-1.8%")
        with col3:
            st.metric("Model A (Linear)", "123.3 Mbps", delta="-13.7%")
        with col4:
            st.metric("Model B (Ridge)", "122.3 Mbps", delta="-14.4%")
        
        st.markdown("---")
        
        # Display results table
        st.markdown("### Server Selection Performance by Method")
        st.dataframe(results_df.style.format({
            'Median Mbps': '{:.2f}',
            'P90 Mbps': '{:.2f}',
            'Change vs RTT (%)': '{:+.2f}%'
        }), use_container_width=True)
        
        # Visualizations
        col1, col2 = st.columns(2)
        
        with col1:
            fig = go.Figure()
            colors = ['green', 'red', 'red', 'orange']
            fig.add_trace(go.Bar(
                x=results_df['Method'],
                y=results_df['Median Mbps'],
                marker_color=colors,
                text=results_df['Median Mbps'].round(1),
                textposition='outside'
            ))
            fig.update_layout(
                title='Median Throughput by Selection Method',
                xaxis_title='Selection Method',
                yaxis_title='Throughput (Mbps)',
                showlegend=False,
                xaxis={'tickangle': -45}
            )
            st.plotly_chart(fig, use_container_width=True)
        
        with col2:
            # Performance vs RTT chart (excluding baseline)
            methods = results_df['Method'][1:].str.replace('Model ', '')
            changes = results_df['Change vs RTT (%)'][1:]
            colors_bar = ['red', 'red', 'orange']
            
            fig = go.Figure()
            fig.add_trace(go.Bar(
                x=methods,
                y=changes,
                marker_color=colors_bar,
                text=[f"{v:+.1f}%" for v in changes],
                textposition='outside'
            ))
            fig.update_layout(
                title='Performance vs RTT-Only Baseline',
                xaxis_title='ML Model',
                yaxis_title='Change (%)',
                showlegend=False
            )
            fig.add_hline(y=0, line_dash="dash", line_color="gray", annotation_text="Baseline")
            st.plotly_chart(fig, use_container_width=True)
        
        # Model Performance
        st.markdown("### Model Prediction Performance")
        
        model_perf = pd.DataFrame({
            'Model': ['Model A - Linear', 'Model B - Ridge', 'Model C - Neural Net'],
            'R² (Test)': [0.057, 0.117, 0.205],
            'RMSE (Test)': [1.501, 1.461, 1.390],
            'MAE (Test)': [1.210, 1.174, 1.128]
        })
        
        st.dataframe(model_perf.style.format({
            'R² (Test)': '{:.3f}',
            'RMSE (Test)': '{:.3f}',
            'MAE (Test)': '{:.3f}'
        }), use_container_width=True)
        
        st.markdown("""
        **Key Observations:**
        - Best R² is only 20.5% (Neural Network) - very low predictability
        - All models perform in log-space to handle throughput variability
        - Despite 20.5% R², the neural network's selections are only 1.8% worse than RTT-only
        - Simpler models (5.7-11.7% R²) perform significantly worse in selection
        
        **Conclusion:**
        For this M-Lab dataset, with only RTT and packet loss as predictive features,
        **RTT-only selection remains the most reliable approach**. The low R² values
        indicate that throughput is difficult to predict from these metrics alone.
        """)

elif page == "Statistical Validation":
    st.header("Statistical Validation")
    
    st.markdown("""
    ## Rigorous Statistical Analysis
    
    This page presents validated statistical findings from our analysis of network metrics
    and their relationship to throughput performance.
    """)
    
    # Test results
    tests = {
        'Test': [
            'RTT vs Throughput Correlation',
            'Loss vs Throughput Correlation',
            'RTT vs Loss Correlation',
            'R² (RTT only)',
            'R² (RTT + Loss, Linear)',
            'R² (RTT + Loss, Neural Net)'
        ],
        'Result': [
            'r = -0.161',
            'r = -0.111',
            'r = 0.105',
            '2.6%',
            '5.7%',
            '20.5%'
        ],
        'p-value': [
            '< 0.001',
            '< 0.001',
            '< 0.001',
            '< 0.001',
            '< 0.001',
            '< 0.001'
        ],
        'Interpretation': [
            'Weak negative correlation',
            'Very weak negative correlation',
            'Very weak positive (independent)',
            'Very low predictability',
            'Low predictability',
            'Modest predictability'
        ]
    }
    
    tests_df = pd.DataFrame(tests)
    st.dataframe(tests_df, use_container_width=True)
    
    st.markdown("""
    <div class="highlight-box">
    <h4>Key Statistical Findings</h4>
    <p>Validated results from rigorous analysis:</p>
    <ol>
        <li>RTT and packet loss are <strong>largely independent</strong> (r = 0.105), supporting their use together</li>
        <li>All correlations are <strong>statistically significant</strong> (p < 0.001)</li>
        <li>However, correlations are <strong>weak</strong>, indicating low individual predictive power</li>
        <li>Best model (Neural Net) achieves only <strong>20.5% R²</strong></li>
        <li>This suggests <strong>additional features needed</strong> for accurate throughput prediction</li>
    </ol>
    </div>
    """, unsafe_allow_html=True)
    
    st.markdown("---")
    
    st.subheader("Understanding Low R² Values")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("""
        **What Low R² Tells Us:**
        
        - **2.6% R² for RTT alone:** RTT explains very little throughput variance
        - **20.5% R² with Neural Net:** Even complex models struggle with limited features
        - **79.5% unexplained variance:** Many factors affect throughput beyond RTT and loss
        """)
        
        st.info("""
        **Implication:** Current features (RTT + packet loss) are insufficient for
        accurate throughput prediction. Additional metrics needed such as:
        - TTFB (Time to First Byte)
        - Jitter/RTT variance
        - Bandwidth capacity estimates
        - Server load indicators
        """)
    
    with col2:
        st.markdown("""
        **Why This Matters:**
        
        1. **Validates the problem:** RTT-only is indeed insufficient (only 2.6% explained)
        2. **Shows current limitations:** RTT + loss only reaches 20.5% R²
        3. **Points to solution:** Need more informative metrics
        
        **Research Findings:**
        - **Jitter analysis:** Shows r=0.40 correlation, independent of RTT
        - **5G RSRP:** Explains 22.3% variance in mobile networks
        - **Multi-metric 5G:** Achieves 24.3% R² (RSRP+RSRQ+SINR)
        
        **Next Steps:**
        - Add TTFB active measurements
        - Include bandwidth estimation
        - Test with more comprehensive feature sets
        """)
    
    st.markdown("---")
    
    st.subheader("Server Selection Performance")
    
    st.markdown("""
    ### Current Results (M-Lab dataset, RTT + Loss features)
    
    When testing server selection with rigorous methodology (grouping by actual clients):
    """)
    
    selection_results = pd.DataFrame({
        'Method': ['RTT-Only', 'Model A (Linear)', 'Model B (Ridge)', 'Model C (Neural Net)'],
        'Median Throughput': ['142.9 Mbps', '123.3 Mbps', '122.3 Mbps', '140.3 Mbps'],
        'vs RTT-Only': ['Baseline', '-13.7%', '-14.4%', '-1.8%'],
        'Status': ['✓ Current Best', '✗ Worse', '✗ Worse', '≈ Similar']
    })
    
    st.dataframe(selection_results, use_container_width=True)
    
    st.warning("""
    **Conclusion:** With only RTT and packet loss as features, ML models cannot outperform
    simple RTT-only selection. The low R² values directly translate to poor selection performance.
    This validates the need for richer feature sets before ML can provide practical improvements.
    """)

elif page == "Geographic Analysis":
    st.header("Geographic Analysis")
    
    if not mlab_df.empty and 'client_city' in mlab_df.columns:
        st.subheader("Top Cities by Measurement Count")
        
        city_counts = mlab_df['client_city'].value_counts().head(20)
        
        fig = px.bar(x=city_counts.index, y=city_counts.values,
                    labels={'x': 'City', 'y': 'Number of Measurements'},
                    title='Top 20 Cities by Measurement Count')
        fig.update_layout(xaxis_tickangle=-45)
        st.plotly_chart(fig, use_container_width=True)
        
        # City statistics
        st.subheader("Performance by City")
        
        city_stats = mlab_df.groupby('client_city').agg({
            'download_mbps': ['mean', 'median', 'std', 'count'],
            'min_rtt_ms': ['mean', 'median'],
            'packet_loss_rate': 'mean'
        }).round(2)
        
        city_stats.columns = ['_'.join(col).strip() for col in city_stats.columns.values]
        city_stats = city_stats.sort_values('download_mbps_mean', ascending=False).head(20)
        city_stats = city_stats.reset_index()
        
        st.dataframe(city_stats, use_container_width=True)
        
        # Map visualization (if coordinates available)
        if 'client_lat' in mlab_df.columns and 'client_lon' in mlab_df.columns:
            st.subheader("Geographic Distribution")
            
            # Create tabs for 2D and 3D views
            map_tab1, map_tab2 = st.tabs(["2D Map View", "3D Globe View"])
            
            with map_tab1:
                sample_size = min(1000, len(mlab_df))
                map_data = mlab_df.sample(n=sample_size)[['client_lat', 'client_lon', 'download_mbps']]
                map_data = map_data.dropna()
                
                fig = px.scatter_mapbox(map_data, 
                                       lat='client_lat', 
                                       lon='client_lon',
                                       color='download_mbps',
                                       size='download_mbps',
                                       hover_data=['download_mbps'],
                                       title=f'Measurement Locations (sample of {sample_size})',
                                       mapbox_style='open-street-map',
                                       zoom=3)
                st.plotly_chart(fig, use_container_width=True)
            
            with map_tab2:
                sample_size = min(2000, len(mlab_df))
                globe_data = mlab_df.sample(n=sample_size)[['client_lat', 'client_lon', 'download_mbps', 'client_city']]
                globe_data = globe_data.dropna()
                
                # Add projection selector
                col1, col2 = st.columns([3, 1])
                with col2:
                    projection = st.selectbox(
                        "Globe Projection",
                        ["orthographic", "natural earth", "equirectangular", "mercator"],
                        index=0
                    )
                
                # Create 3D globe visualization
                fig = px.scatter_geo(globe_data,
                                    lat='client_lat',
                                    lon='client_lon',
                                    color='download_mbps',
                                    size='download_mbps',
                                    hover_name='client_city',
                                    hover_data={'download_mbps': ':.2f', 
                                               'client_lat': ':.2f',
                                               'client_lon': ':.2f'},
                                    projection=projection,
                                    title=f'3D Globe View - Measurement Locations (sample of {sample_size})',
                                    color_continuous_scale='Viridis')
                
                fig.update_geos(
                    showcountries=True,
                    showcoastlines=True,
                    showland=True,
                    landcolor='rgb(243, 243, 243)',
                    coastlinecolor='rgb(204, 204, 204)',
                    projection_type=projection
                )
                
                fig.update_layout(
                    height=700,
                    geo=dict(
                        showocean=True,
                        oceancolor='rgb(230, 245, 255)',
                        showlakes=True,
                        lakecolor='rgb(230, 245, 255)',
                    )
                )
                
                st.plotly_chart(fig, use_container_width=True)
                
                st.info("""
                **Interactive 3D Globe:** 
                - **Drag** to rotate the globe (orthographic projection)
                - **Scroll** to zoom in/out
                - **Hover** over points to see detailed information
                - **Color intensity** represents throughput (Mbps)
                - **Point size** indicates throughput magnitude
                - Try different **projections** to see various world views
                """)
                
                # Add statistics panel
                st.markdown("### Global Coverage Statistics")
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("Unique Locations", len(globe_data))
                with col2:
                    st.metric("Avg Throughput", f"{globe_data['download_mbps'].mean():.2f} Mbps")
                with col3:
                    st.metric("Max Throughput", f"{globe_data['download_mbps'].max():.2f} Mbps")

elif page == "RIPE Atlas CDN Comparison":
    st.title("RIPE Atlas: CDN Performance Comparison")
    
    if not ripe_df.empty:
        # CDN comparison
        cdn_stats = ripe_df.groupby('target').agg({
            'rtt_avg': ['mean', 'median', 'std'],
            'packet_loss_pct': 'mean',
            'probe_id': 'count'
        }).round(2)
        
        cdn_stats.columns = ['_'.join(col).strip() for col in cdn_stats.columns.values]
        cdn_stats = cdn_stats.reset_index()
        cdn_stats = cdn_stats.sort_values('rtt_avg_mean')
        
        st.subheader("CDN Performance Rankings")
        st.dataframe(cdn_stats, use_container_width=True)
        
        # Box plot
        fig = px.box(ripe_df, x='target', y='rtt_avg',
                    title='RTT Distribution by CDN Target',
                    labels={'target': 'CDN', 'rtt_avg': 'RTT (ms)'})
        fig.update_layout(xaxis_tickangle=-45)
        st.plotly_chart(fig, use_container_width=True)
        
        # Loss comparison
        loss_by_cdn = ripe_df.groupby('target')['packet_loss_pct'].mean().sort_values()
        
        fig = px.bar(x=loss_by_cdn.index, y=loss_by_cdn.values,
                    labels={'x': 'CDN', 'y': 'Packet Loss (%)'},
                    title='Packet Loss by CDN Target')
        st.plotly_chart(fig, use_container_width=True)
        
        st.markdown("""
        <div class="highlight-box">
        <h4>Key Finding</h4>
        No universally "best" CDN across all metrics. Cloudflare has lowest RTT 
        but higher loss. Quad9 has lowest loss but higher RTT. This validates 
        the need for multi-metric selection!
        </div>
        """, unsafe_allow_html=True)

elif page == "5G Analysis (Lumos5G)":
    st.header("5G Mobile Network Analysis (Lumos5G)")
    
    if not lumos_df.empty:
        if 'Throughput' in lumos_df.columns and 'nr_ssRsrp' in lumos_df.columns:
            # Signal strength correlation
            valid_data = lumos_df[
                (lumos_df['Throughput'] > 0) & 
                (lumos_df['nr_ssRsrp'].notna())
            ]
            
            correlation = valid_data['nr_ssRsrp'].corr(valid_data['Throughput'])
            r_squared = correlation ** 2
            
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.metric("Correlation (r)", f"{correlation:.3f}")
            with col2:
                st.metric("R² (Variance Explained)", f"{r_squared*100:.1f}%")
            with col3:
                st.metric("Interpretation", "Moderate positive")
            
            st.markdown(f"""
            <div class="highlight-box">
            <h4>Mobile Network Insight</h4>
            Signal strength (RSRP) explains <strong>{r_squared*100:.1f}% of throughput variance</strong> 
            in 5G networks - much better than RTT (2.6%) in wired networks!
            This suggests <strong>wireless-specific metrics</strong> should be added to composite scores 
            for mobile CDN selection.
            </div>
            """, unsafe_allow_html=True)
            
            # Scatter plot
            sample_data = valid_data.sample(n=min(2000, len(valid_data)))
            
            fig = px.scatter(sample_data, 
                           x='nr_ssRsrp', 
                           y='Throughput',
                           opacity=0.4,
                           title=f'5G Signal Strength vs Throughput (r={correlation:.3f})',
                           labels={'nr_ssRsrp': 'RSRP (dBm)', 'Throughput': 'Throughput (Mbps)'},
                           trendline='ols')
            st.plotly_chart(fig, use_container_width=True)
            
            # Distribution
            col1, col2 = st.columns(2)
            
            with col1:
                fig = px.histogram(valid_data, x='Throughput', nbins=50,
                                 title='5G Throughput Distribution',
                                 labels={'Throughput': 'Throughput (Mbps)'})
                st.plotly_chart(fig, use_container_width=True)
            
            with col2:
                fig = px.histogram(valid_data, x='nr_ssRsrp', nbins=50,
                                 title='5G Signal Strength (RSRP) Distribution',
                                 labels={'nr_ssRsrp': 'RSRP (dBm)'})
                st.plotly_chart(fig, use_container_width=True)

elif page == "Variable Importance & Comparison":
    st.header("Variable Importance Analysis & Comparison with Google Research")
    
    st.markdown("""
    This page provides a comprehensive analysis of:
    1. **Importance of each variable** in our multi-metric CDN selection
    2. **Comparison with Google's "Beyond RTT" research**
    3. **Key methodological differences**
    4. **Our unique contributions**
    """)
    
    # Quick navigation tabs
    tab1, tab2, tab3, tab4 = st.tabs([
        "Variable Importance", 
        "Comparison with Google", 
        "Key Differences",
        "Recommendations"
    ])
    
    with tab1:
        st.subheader("Variable Importance in Our Research")
        
        # Summary table
        st.markdown("### Summary of Key Variables")
        
        importance_data = pd.DataFrame({
            'Variable': ['RTT', 'Packet Loss', 'Throughput', 'RSRP (5G)', 'Jitter'],
            'Correlation with Throughput': ['-0.161', '-0.111', '(target)', '0.473', '0.40'],
            'R² Explained': ['2.58%', '1.23%', '100%', '22.3%', '~16%'],
            'p-value': ['< 0.001', '< 0.001', 'N/A', '< 0.001', '< 0.001'],
            'Context': ['Wired', 'Wired', 'All', 'Mobile Only', 'Wired'],
            'Status': ['Available', 'Available', 'Target', 'Available (Lumos5G)', 'Analyzed']
        })
        
        st.dataframe(importance_data, use_container_width=True)
        
        # Detailed analysis
        st.markdown("### Detailed Analysis")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("""
            #### RTT (Round-Trip Time)
            - **Pearson:** r = -0.161 (weak negative)
            - **Spearman:** ρ = -0.271 (moderate rank correlation)
            - **R²:** Only 2.58% variance explained
            - **Conclusion:** Insufficient alone for throughput prediction
            
            #### Packet Loss
            - **Correlation:** r = -0.111 (very weak)
            - **R²:** Only 1.23% variance explained
            - **Independence:** Low correlation with RTT (r=0.105)
            - **Why it matters:** Can have non-linear TCP impact in high-loss scenarios
            """)
        
        with col2:
            st.markdown("""
            #### RSRP (5G Signal Strength)
            - **Correlation:** r = 0.473 (moderate positive)
            - **R²:** 22.3% variance explained
            - **Context:** Mobile/5G networks only
            - **Finding:** 9x better predictor than RTT in mobile
            
            #### Jitter (RTT Variance)
            - **Correlation:** r = 0.40 with stability
            - **Cases found:** 1,098 low-RTT but high-jitter scenarios
            - **Independence:** Largely independent from mean RTT
            - **Status:** Analyzed but not yet in models
            """)
        
        # Visualization
        st.markdown("### Variable Importance Visualization")
        
        var_importance = pd.DataFrame({
            'Variable': ['RSRP\n(Mobile)', 'Jitter', 'RTT', 'Packet\nLoss'],
            'R² or Correlation': [22.3, 16.0, 2.6, 1.2],
            'Context': ['Mobile', 'Wired', 'Wired', 'Wired']
        })
        
        fig = px.bar(var_importance, x='Variable', y='R² or Correlation', color='Context',
                    title='Predictive Power of Variables (R² % or Correlation²)',
                    labels={'R² or Correlation': 'Variance Explained (%)'},
                    color_discrete_map={'Wired': '#ff7f0e', 'Mobile': '#2ca02c'})
        st.plotly_chart(fig, use_container_width=True)
        
        st.info("""
        **Key Insight:** For wired networks, individual metrics are weak predictors.
        Mobile networks (5G) show stronger signal-throughput relationships. This suggests:
        - Wired CDN selection needs more features (TTFB, bandwidth estimates)
        - Mobile CDN selection can leverage signal metrics effectively
        - RTT alone explains < 3% variance in both contexts
        """)
    
    with tab2:
        st.subheader("Comparison with Google's 'Beyond RTT' Research")
        
        st.markdown("""
        ### Similarities
        
        | Aspect | Google | Our Research | Match? |
        |--------|--------|--------------|--------|
        | **Core Hypothesis** | RTT insufficient | RTT insufficient | ✅ Yes |
        | **Multi-metric** | TTFB, loss, load | RTT, throughput, loss | ✅ Yes |
        | **Performance Gain** | ~20-40% | 610% median | ✅ Exceeds |
        | **Validation** | A/B testing | 5 statistical tests | ✅ Similar |
        """)
        
        st.markdown("### Key Differences")
        
        comparison_df = pd.DataFrame({
            'Dimension': ['Data Source', 'Scale', 'CDN Coverage', 'Deployment', 'Metrics', 'Reproducibility'],
            'Google Research': [
                'Proprietary', 
                'Millions of users', 
                'Google CDN', 
                'Live production',
                'RTT, TTFB, loss, server load',
                'Limited (proprietary)'
            ],
            'Our Research': [
                'Public (M-Lab, RIPE, Lumos5G)',
                '115,397 measurements',
                'Multi-CDN (Cloudflare, Quad9, etc.)',
                'Simulation-based',
                'RTT, throughput, loss, RSRP',
                'Fully open-source'
            ]
        })
        
        st.dataframe(comparison_df, use_container_width=True)
        
        st.markdown("### Our Unique Contributions")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("""
            #### ✅ What We Add:
            1. **5G Mobile Analysis**
               - Signal strength (RSRP): 22.3% variance
               - 9x better than RTT in mobile
               
            2. **Statistical Rigor**
               - 5 independent validation tests
               - 4 correlation methods
               - Effect size: Cohen's d = 1.77
            """)
        
        with col2:
            st.markdown("""
            #### ✅ Advantages:
            3. **Open & Reproducible**
               - Public datasets
               - Open-source code
               - Interactive dashboard
               
            4. **Multi-CDN Insights**
               - No universally best provider
               - Context-dependent selection
            """)
    
    with tab3:
        st.subheader("Key Methodological Differences")
        
        st.markdown("### Data & Scale")
        st.markdown("""
        **Google's Advantage:**
        - Millions of users, live traffic
        - Real-time decisions
        - Proprietary infrastructure metrics
        
        **Our Advantage:**
        - Reproducible with public data
        - Academic rigor and transparency
        - Multi-CDN comparison
        """)
        
        st.markdown("### Metrics Comparison")
        
        metrics_comparison = pd.DataFrame({
            'Metric': ['RTT', 'TTFB', 'Packet Loss', 'Throughput', 'Server Load', 'Signal Strength'],
            'Google': ['✅', '✅ Active', '✅', '✅', '✅ Internal', '⚠️'],
            'Our Research': ['✅', '❌ Limited', '✅', '✅ Historical', '❌', '✅ Lumos5G'],
            'Importance': ['High', 'Very High', 'High', 'Very High', 'Medium', 'High (Mobile)']
        })
        
        st.dataframe(metrics_comparison, use_container_width=True)
        
        st.markdown("### Selection Algorithms")
        st.markdown("""
        | Approach | Google | Our Research |
        |----------|--------|--------------|
        | **Baseline** | RTT-only | RTT-only |
        | **Multi-metric** | Proprietary formula | 0.3 RTT + 0.4 Throughput + 0.3 Loss |
        | **ML Models** | Neural networks | Planned: Random Forest, XGBoost |
        | **Optimization** | A/B testing, bandits | Grid search, sensitivity analysis |
        | **Complexity** | High (adaptive) | Low (interpretable) |
        """)
        
        st.success("""
        **Why Our Approach Works:** 610% improvement proves simple methods are effective. 
        Near-optimal (96.7%) performance suggests complex models may only add marginal gains.
        """)
    
    with tab4:
        st.subheader("Recommendations & Future Work")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("""
            ### For CDN Providers
            1. **Expose multi-metric APIs**
               - Don't just provide RTT
               - Include server load indicators
               
            2. **Monitor packet loss**
               - Even 0.5% impacts TCP significantly
               
            3. **Mobile-specific metrics**
               - Signal strength (RSRP, RSRQ)
               - Cell handover rates
            """)
        
        with col2:
            st.markdown("""
            ### For Application Developers
            1. **Use composite scores**
               - Weight throughput highest (40%)
               - Balance RTT + Loss (30% each)
               
            2. **Context-aware selection**
               - Mobile: prioritize signal strength
               - Wired: RTT + Loss balance
               
            3. **Client-side implementation**
               - Simple weighted average
               - No server infrastructure needed
            """)
        
        st.markdown("### Future Research Directions")
        
        st.markdown("""
        1. **Add TTFB measurements**
           - Use RIPE Atlas HTTP tests
           - Active probing before selection
           - Expected 10-15% R² improvement
        
        2. **Implement ML models**
           - Random Forest for feature importance
           - XGBoost for accuracy
           - Neural networks for complex patterns
        
        3. **Live deployment**
           - Browser extension
           - A/B testing on real users
           - Validate in production
        
        4. **Geographic expansion**
           - 200+ countries via RIPE Atlas
           - Regional weight optimization
           - Time-of-day analysis
        """)
        
        st.info("""
        **Bridge to Industry:** 
        - Collaborate with CDN providers
        - Contribute to IETF standards
        - Publish in SIGCOMM/IMC conferences
        - Open-source client libraries
        """)
    
    # Footer with document link
    st.markdown("---")
    st.markdown("""
    ### 📄 Full Analysis Document
    
    For the complete 50-page analysis including all tables, formulas, and references, see:
    `VARIABLE_IMPORTANCE_AND_COMPARISON.md` in the project repository.
    
    **Topics covered:**
    - Detailed correlation analysis (Pearson, Spearman, Kendall)
    - Statistical validation methodology
    - Comparison with published CDN research
    - Mathematical formulas and proofs
    - Complete reference list
    """)

elif page == "Interactive Simulator":
    st.header("Interactive CDN Selection Simulator")
    
    if not mlab_df.empty:
        st.markdown("""
        Experiment with different weight combinations and see how they affect 
        server selection performance.
        """)
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            alpha = st.slider("RTT Weight (α)", 0.0, 1.0, 0.3, 0.05)
        with col2:
            beta = st.slider("Throughput Weight (β)", 0.0, 1.0, 0.4, 0.05)
        with col3:
            gamma = st.slider("Loss Weight (γ)", 0.0, 1.0, 0.3, 0.05)
        
        weight_sum = alpha + beta + gamma
        
        if abs(weight_sum - 1.0) > 0.01:
            st.warning(f"Weights sum to {weight_sum:.2f}. They should sum to 1.0. Normalizing...")
            alpha, beta, gamma = alpha/weight_sum, beta/weight_sum, gamma/weight_sum
        
        st.info(f"Current weights: α={alpha:.2f}, β={beta:.2f}, γ={gamma:.2f}")
        
        n_sims = st.slider("Number of simulations", 100, 2000, 500, 100)
        
        if st.button("Run Simulation", type="primary"):
            with st.spinner("Running simulations..."):
                # Calculate custom composite score
                def normalize_metric(series, lower_is_better=True):
                    min_val = series.min()
                    max_val = series.max()
                    if max_val == min_val:
                        return pd.Series([50] * len(series))
                    if lower_is_better:
                        return 100 * (1 - (series - min_val) / (max_val - min_val))
                    else:
                        return 100 * (series - min_val) / (max_val - min_val)
                
                rtt_score = normalize_metric(mlab_df['min_rtt_ms'], True)
                throughput_score = normalize_metric(mlab_df['download_mbps'], False)
                loss_score = normalize_metric(mlab_df['packet_loss_rate'], True)
                
                custom_score = alpha * rtt_score + beta * throughput_score + gamma * loss_score
                
                # Run simulations
                np.random.seed(42)
                rtt_throughputs = []
                custom_throughputs = []
                
                for _ in range(n_sims):
                    sample_idx = np.random.choice(len(mlab_df), size=min(100, len(mlab_df)), replace=True)
                    sample = mlab_df.iloc[sample_idx]
                    sample_custom_score = custom_score.iloc[sample_idx]
                    
                    # RTT-only
                    rtt_selected_idx = sample['min_rtt_ms'].idxmin()
                    rtt_throughputs.append(sample.loc[rtt_selected_idx, 'download_mbps'])
                    
                    # Custom weights
                    custom_selected_idx = sample_custom_score.idxmax()
                    custom_throughputs.append(sample.loc[custom_selected_idx, 'download_mbps'])
                
                rtt_throughputs = np.array(rtt_throughputs)
                custom_throughputs = np.array(custom_throughputs)
                improvements = ((custom_throughputs - rtt_throughputs) / rtt_throughputs) * 100
                
                # Results
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    st.metric("RTT-Only Median", f"{np.median(rtt_throughputs):.1f} Mbps")
                with col2:
                    st.metric("Custom Weights Median", f"{np.median(custom_throughputs):.1f} Mbps")
                with col3:
                    improvement = np.median(improvements)
                    st.metric("Median Improvement", f"{improvement:.1f}%", 
                             delta="vs RTT-only")
                
                # Comparison with rigorous analysis
                st.markdown(f"""
                <div class="highlight-box">
                <h4>Simulation Results</h4>
                Your custom weights show: <strong>{improvement:.1f}%</strong> median improvement over RTT-only in this simulation.
                <br><br>
                <em>⚠️ Note: This is a simplified simulation using composite scoring with actual throughput.
                Rigorous analysis (without future knowledge) shows RTT-only currently performs best with limited features (RTT+loss only).
                Real improvement requires additional predictive features like TTFB, jitter, or bandwidth estimates.</em>
                </div>
                """, unsafe_allow_html=True)
                
                # Visualization
                fig = go.Figure()
                fig.add_trace(go.Histogram(x=rtt_throughputs, name='RTT-Only', 
                                          opacity=0.7, nbinsx=50))
                fig.add_trace(go.Histogram(x=custom_throughputs, name='Custom Weights', 
                                          opacity=0.7, nbinsx=50))
                fig.update_layout(
                    title='Throughput Distribution Comparison',
                    xaxis_title='Throughput (Mbps)',
                    yaxis_title='Frequency',
                    barmode='overlay'
                )
                st.plotly_chart(fig, use_container_width=True)

# Footer
st.markdown("---")
st.markdown("""
<div style='text-align: center; color: #666;'>
    <p>CDN Multi-Metric Server Selection Dashboard | November 2025</p>
    <p>Research by: cdn-multimetric-selection project</p>
    <p>Data sources: M-Lab, RIPE Atlas, Lumos5G</p>
</div>
""", unsafe_allow_html=True)
