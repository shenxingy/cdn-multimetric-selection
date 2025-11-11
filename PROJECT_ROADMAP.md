# CDN Multi-Metric Selection - Project Roadmap

## ✅ Completed Tasks

### Phase 1: Environment Setup
- [x] Python 3.12 virtual environment configured
- [x] All core packages installed (pandas, numpy, scikit-learn, matplotlib, etc.)
- [x] RIPE Atlas API keys configured (10 keys in .env)
- [x] BigQuery libraries installed for M-Lab data access
- [x] Project directory structure created

### Phase 2: Data Exploration
- [x] M-Lab NDT dataset exploration notebook created
- [x] Synthetic data generation for testing (5,000 measurements)
- [x] Correlation analysis: RTT vs Throughput = -0.666 (moderate)
- [x] Performance gap analysis: 21% average loss when using RTT alone
- [x] Visualization: 4-panel analysis of RTT/throughput relationship

---

## 🎯 Next Steps

### **IMMEDIATE: Phase 3 - Real M-Lab Data Collection**

#### Task 3.1: Set Up Google Cloud BigQuery Access
**Priority: HIGH | Estimated Time: 30 minutes**

**What to do:**
1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project (or use existing)
3. Enable BigQuery API
4. Set up authentication:
   ```bash
   # Install gcloud CLI if not already installed
   brew install --cask google-cloud-sdk
   
   # Authenticate
   gcloud auth application-default login
   
   # Set your project
   gcloud config set project YOUR_PROJECT_ID
   ```

**Verification:**
```python
from google.cloud import bigquery
client = bigquery.Client()
print("✓ BigQuery connected")
```

**Resources:**
- [BigQuery Quickstart](https://cloud.google.com/bigquery/docs/quickstarts)
- [M-Lab BigQuery Guide](https://www.measurementlab.net/data/docs/bq/quickstart/)

---

#### Task 3.2: Query Real M-Lab Data
**Priority: HIGH | Estimated Time: 1 hour**

**What to do:**
1. Create new notebook: `02_mlab_real_data_collection.ipynb`
2. Query M-Lab NDT dataset for recent data (last 7-30 days)
3. Focus on these metrics:
   - `a.MeanThroughputMbps` (throughput)
   - `a.MinRTT` (latency)
   - `a.LossRate` (packet loss)
   - Client/Server geographic data
   - Time of day patterns

**Sample Query:**
```sql
SELECT
  date,
  TIMESTAMP_TRUNC(test_date, HOUR) as hour,
  a.MeanThroughputMbps as throughput_mbps,
  a.MinRTT as min_rtt_ms,
  a.LossRate as loss_rate,
  Client.Geo.Latitude as client_lat,
  Client.Geo.Longitude as client_lon,
  Client.Geo.CountryCode as client_country,
  Client.Network.ASNumber as client_asn,
  Server.Geo.Latitude as server_lat,
  Server.Geo.Longitude as server_lon,
  Server.Site as server_site
FROM
  `measurement-lab.ndt.unified_downloads`
WHERE
  date BETWEEN DATE_SUB(CURRENT_DATE(), INTERVAL 30 DAY) 
    AND CURRENT_DATE()
  AND a.MeanThroughputMbps IS NOT NULL
  AND a.MinRTT IS NOT NULL
  AND a.MinRTT > 0
  AND a.MeanThroughputMbps > 0
  AND Client.Geo.CountryCode = 'US'  -- Start with US data
LIMIT 50000
```

**Expected Output:**
- 50,000 real measurements
- Compare correlation with synthetic data
- Validate hypothesis: RTT alone is insufficient

**Cost Estimate:** ~0.5-2 GB query = FREE (within 1 TB/month free tier)

---

### **Phase 4 - RIPE Atlas Measurements**

#### Task 4.1: Design Measurement Campaign
**Priority: MEDIUM | Estimated Time: 2 hours**

**What to do:**
1. Select target CDN servers to measure:
   - Popular CDNs: Cloudflare, Akamai, Fastly, AWS CloudFront, Google CDN
   - Get IP addresses for each CDN's edge servers
   
2. Design measurement strategy:
   - **Probes:** Use 50-100 RIPE Atlas probes globally
   - **Metrics:** Ping (RTT), Traceroute, HTTP timing
   - **Duration:** 24-48 hours for temporal patterns
   - **Frequency:** Every 5-15 minutes

3. Create notebook: `03_ripe_atlas_measurements.ipynb`

**Key Decisions:**
- Which geographic regions to focus on?
- Which CDNs to compare?
- What time period captures enough variation?

---

#### Task 4.2: Run RIPE Atlas Measurements
**Priority: MEDIUM | Estimated Time: 3 hours + 24-48h wait**

**What to do:**
```python
from ripe.atlas.cousteau import (
    Ping, Traceroute, AtlasSource, AtlasCreateRequest
)
import os

# Use your SNM API key (can create measurements)
ATLAS_API_KEY = os.getenv('RIPE_ATLAS_SNM_KEY')

# Example: Measure RTT to Cloudflare
ping = Ping(
    af=4,
    target="1.1.1.1",  # Cloudflare DNS (anycast)
    description="CDN RTT Measurement - Cloudflare"
)

source = AtlasSource(
    type="area",
    value="WW",  # Worldwide
    requested=50  # 50 probes
)

atlas_request = AtlasCreateRequest(
    key=ATLAS_API_KEY,
    measurements=[ping],
    sources=[source],
    is_oneoff=False,  # Recurring
    interval=300  # Every 5 minutes
)

(is_success, response) = atlas_request.create()
print(f"Measurement ID: {response['measurements'][0]}")
```

**What you'll measure:**
1. RTT to CDN edge servers (ping)
2. Path characteristics (traceroute)
3. HTTP response times (optional)

**Data Collection:**
- Let measurements run for 24-48 hours
- Retrieve results using measurement IDs
- Store in `data/raw/ripe_atlas_measurements.csv`

---

### **Phase 5 - Feature Engineering & Analysis**

#### Task 5.1: Merge M-Lab + RIPE Atlas Data
**Priority: MEDIUM | Estimated Time: 2 hours**

**What to do:**
1. Create notebook: `04_feature_engineering.ipynb`
2. Combine datasets:
   - M-Lab: throughput ground truth
   - RIPE Atlas: detailed RTT measurements
3. Calculate additional features:
   - **Geographic distance** (client-server)
   - **RTT jitter** (variance)
   - **Time of day** (peak vs off-peak)
   - **ASN characteristics**
   - **Packet loss patterns**

**New Features to Create:**
```python
# Distance calculation
from geopy.distance import geodesic

df['distance_km'] = df.apply(
    lambda row: geodesic(
        (row['client_lat'], row['client_lon']),
        (row['server_lat'], row['server_lon'])
    ).km, axis=1
)

# Time-based features
df['hour'] = df['timestamp'].dt.hour
df['is_peak_hour'] = df['hour'].between(9, 17)
df['day_of_week'] = df['timestamp'].dt.dayofweek

# RTT-based features
df['rtt_per_km'] = df['min_rtt_ms'] / df['distance_km']
df['rtt_jitter'] = df.groupby('server')['min_rtt_ms'].transform('std')
```

---

#### Task 5.2: Correlation & Feature Importance Analysis
**Priority: HIGH | Estimated Time: 2 hours**

**What to do:**
1. Create correlation matrix for all features vs throughput
2. Identify which metrics matter most:
   - RTT (baseline)
   - Packet loss
   - Geographic distance
   - Time of day
   - Jitter
   - ASN

**Analysis Questions:**
- Which features have stronger correlation than RTT alone?
- Are there interaction effects? (e.g., RTT + loss together)
- Do patterns vary by region or ASN?

**Expected Insight:**
You'll likely find that **packet loss** and **jitter** are as important as RTT for predicting throughput.

---

### **Phase 6 - Machine Learning Models**

#### Task 6.1: Baseline Model Comparison
**Priority: HIGH | Estimated Time: 3 hours**

**What to do:**
1. Create notebook: `05_ml_baseline_models.ipynb`
2. Train and compare models:

```python
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_squared_error, r2_score

# Prepare data
X = df[['min_rtt_ms', 'loss_rate', 'distance_km', 'hour', 'rtt_jitter']]
y = df['throughput_mbps']

X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.2, random_state=42
)

# Model 1: RTT only (baseline)
from sklearn.linear_model import LinearRegression
model_rtt_only = LinearRegression()
model_rtt_only.fit(X_train[['min_rtt_ms']], y_train)

# Model 2: Multi-metric Linear
model_multi = LinearRegression()
model_multi.fit(X_train, y_train)

# Model 3: Random Forest
from sklearn.ensemble import RandomForestRegressor
model_rf = RandomForestRegressor(n_estimators=100, random_state=42)
model_rf.fit(X_train, y_train)

# Model 4: Gradient Boosting
from sklearn.ensemble import GradientBoostingRegressor
model_gb = GradientBoostingRegressor(n_estimators=100, random_state=42)
model_gb.fit(X_train, y_train)
```

**Compare:**
- RTT-only baseline
- Multi-metric linear regression
- Random Forest
- Gradient Boosting
- XGBoost (advanced)

**Metrics to Report:**
- R² score
- RMSE (throughput prediction error)
- Feature importance rankings

---

#### Task 6.2: Model Optimization & Selection
**Priority: MEDIUM | Estimated Time: 2 hours**

**What to do:**
1. Hyperparameter tuning (GridSearchCV)
2. Cross-validation
3. Feature selection (remove low-importance features)
4. Save best model

**Goal:** Show that multi-metric models outperform RTT-only by 15-30%

---

### **Phase 7 - CDN Selection Algorithm**

#### Task 7.1: Implement Selection Strategy
**Priority: HIGH | Estimated Time: 3 hours**

**What to do:**
1. Create notebook: `06_cdn_selection_algorithm.ipynb`
2. Implement selection strategies:

```python
def select_cdn_rtt_only(measurements):
    """Baseline: select by lowest RTT"""
    return measurements.loc[measurements['min_rtt_ms'].idxmin()]

def select_cdn_ml_predicted(measurements, model):
    """ML-based: predict throughput and select best"""
    measurements['predicted_throughput'] = model.predict(
        measurements[features]
    )
    return measurements.loc[
        measurements['predicted_throughput'].idxmax()
    ]

def select_cdn_weighted_score(measurements):
    """Weighted scoring approach"""
    # Normalize metrics (0-1)
    measurements['rtt_score'] = 1 - (
        measurements['min_rtt_ms'] / measurements['min_rtt_ms'].max()
    )
    measurements['loss_score'] = 1 - (
        measurements['loss_rate'] / measurements['loss_rate'].max()
    )
    
    # Weighted combination
    measurements['total_score'] = (
        0.4 * measurements['rtt_score'] +
        0.4 * measurements['loss_score'] +
        0.2 * measurements['distance_score']
    )
    return measurements.loc[measurements['total_score'].idxmax()]
```

3. Compare selection strategies on test scenarios

---

#### Task 7.2: Simulation & Performance Evaluation
**Priority: HIGH | Estimated Time: 2 hours**

**What to do:**
1. Simulate 1000 CDN selection scenarios
2. Compare actual throughput achieved:
   - RTT-only selection
   - ML prediction selection
   - Weighted scoring selection
   - Oracle (perfect knowledge)

**Metrics:**
- Average throughput improvement (%)
- Selection accuracy
- Robustness to outliers

**Expected Result:** 15-30% improvement over RTT-only

---

### **Phase 8 - Validation & Real-World Testing**

#### Task 8.1: Live CDN Selection Test
**Priority: MEDIUM | Estimated Time: 4 hours**

**What to do:**
1. Deploy your algorithm in a test environment
2. Make real CDN selection decisions
3. Measure actual download performance
4. Compare with traditional (RTT-only) approach

**Tools:**
- `curl` with timing flags
- Custom download scripts
- RIPE Atlas HTTP measurements

---

### **Phase 9 - Documentation & Presentation**

#### Task 9.1: Final Report & Visualizations
**Priority: MEDIUM | Estimated Time: 4 hours**

**What to do:**
1. Create comprehensive report notebook: `07_final_results.ipynb`
2. Key sections:
   - Problem statement
   - Data collection methodology
   - Correlation analysis
   - Model comparison
   - CDN selection algorithm
   - Performance improvements
   - Conclusions & future work

3. Create presentation-ready visualizations:
   - Before/After comparison charts
   - Feature importance plots
   - Geographic distribution maps
   - ROI calculations

---

## 📊 Success Metrics

### Quantitative Goals:
- [ ] Collect 50,000+ real M-Lab measurements
- [ ] Run 48-hour RIPE Atlas measurement campaign
- [ ] Achieve R² > 0.7 in throughput prediction
- [ ] Demonstrate 15-30% improvement over RTT-only selection
- [ ] Test on 5+ major CDN providers

### Qualitative Goals:
- [ ] Prove RTT alone is insufficient (correlation < 0.7)
- [ ] Identify top 3 most important features
- [ ] Create reproducible selection algorithm
- [ ] Document methodology for future researchers

---

## 📚 Additional Resources

### Documentation to Read:
1. [M-Lab Data Documentation](https://www.measurementlab.net/data/)
2. [RIPE Atlas Measurement API](https://atlas.ripe.net/docs/api/v2/manual/)
3. [BigQuery Best Practices](https://cloud.google.com/bigquery/docs/best-practices)
4. [CDN Selection Research Papers](https://scholar.google.com/scholar?q=CDN+server+selection)

### Helpful Papers:
- "On the Effectiveness of RTT-based Server Selection" (SIGCOMM)
- "Demystifying CDN Server Selection" (IMC)
- "A Measurement Study of Netflix, Hulu, and Shazam"

---

## ⏱️ Timeline Estimate

| Phase | Tasks | Time | Priority |
|-------|-------|------|----------|
| **Phase 3** | BigQuery + Real Data | 2-3 hours | 🔴 HIGH |
| **Phase 4** | RIPE Atlas Setup | 5 hours + 48h wait | 🟡 MEDIUM |
| **Phase 5** | Feature Engineering | 4 hours | 🔴 HIGH |
| **Phase 6** | ML Models | 5 hours | 🔴 HIGH |
| **Phase 7** | Selection Algorithm | 5 hours | 🔴 HIGH |
| **Phase 8** | Validation | 4 hours | 🟡 MEDIUM |
| **Phase 9** | Documentation | 4 hours | 🟡 MEDIUM |

**Total Active Work:** ~30-35 hours
**Total Calendar Time:** 5-7 days (including measurement wait time)

---

## 🚀 Quick Start: What to Do RIGHT NOW

### Option A: Continue with BigQuery (Recommended)
```bash
# 1. Install gcloud CLI
brew install --cask google-cloud-sdk

# 2. Authenticate
gcloud auth application-default login

# 3. Open your notebook and run the BigQuery query
jupyter notebook notebooks/exploratory/01_mlab_data_exploration.ipynb
```

### Option B: Start RIPE Atlas Measurements
```bash
# 1. Create new notebook
jupyter notebook notebooks/exploratory/03_ripe_atlas_measurements.ipynb

# 2. Design your measurement campaign
# 3. Launch measurements (they'll run for 24-48 hours)
```

### Option C: Work on Feature Engineering with Synthetic Data
```bash
# While waiting for real data, you can:
# 1. Create feature engineering notebook
# 2. Test your ML pipeline on synthetic data
# 3. Validate your approach before applying to real data
```

---

## 🎓 Learning Outcomes

By completing this project, you will:
1. ✅ Understand CDN selection mechanisms
2. ✅ Master large-scale network measurement analysis
3. ✅ Apply ML to real networking problems
4. ✅ Use BigQuery and RIPE Atlas professionally
5. ✅ Create reproducible research methodology
6. ✅ Demonstrate quantifiable performance improvements

---

## 💡 Tips for Success

1. **Start with BigQuery** - Real data makes everything more convincing
2. **Document as you go** - Take notes in markdown cells
3. **Version control** - Commit after each major milestone
4. **Iterate quickly** - Don't over-optimize early
5. **Validate assumptions** - Test on real data frequently
6. **Compare everything** - Always benchmark against RTT-only baseline

---

**Ready to proceed? I recommend starting with Task 3.1 (BigQuery setup)!**

Let me know which task you'd like to tackle first, and I'll provide detailed step-by-step guidance.
