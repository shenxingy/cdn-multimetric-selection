# Quick Start Guide: RIPE Atlas + Lumos5G + M-Lab

## ✅ What's Ready

### 1. RIPE Atlas Measurements
**Notebook**: `notebooks/exploratory/03_ripe_atlas_measurements.ipynb`

**What it does:**
- Measures RTT to major CDN providers (Cloudflare, Google, Quad9, OpenDNS)
- Uses your 9 RIPE Atlas API keys
- 50 probes worldwide
- 24-hour measurement campaign
- Collects data every 5 minutes

**API Keys Configured:**
- ✅ SNM (Schedule New Measurement) - PRIMARY
- ✅ NPM, LYM, SRM, UEM (Measurement operations)
- ✅ NPMP, GRIP, SPP, SIP (Probe operations)

### 2. Lumos5G Dataset Exploration
**Notebook**: `notebooks/exploratory/04_lumos5g_exploration.ipynb`

**What it analyzes:**
- 5G mobile network throughput data
- Signal strength metrics (RSRP, RSRQ, SINR)
- Mobility patterns (walking vs driving)
- Geographic performance mapping
- Correlation: signal strength vs throughput

**Dataset location**: `Lumos5G-v1.0/Lumos5G-v1.0.csv`

### 3. M-Lab BigQuery Access
**Notebook**: `notebooks/exploratory/02_mlab_real_data_collection.ipynb`

**Status**: ✅ Billing enabled - Ready to query!

---

## 🚀 How to Start

### Option A: Explore Lumos5G First (Immediate - No waiting)

```bash
cd /Users/ankitraj2/558/cdn-multimetric-selection
source venv/bin/activate
jupyter notebook notebooks/exploratory/04_lumos5g_exploration.ipynb
```

**Timeline**: 30-45 minutes
**What you'll learn**:
- How 5G signal quality relates to throughput
- Mobile vs wired performance patterns
- Data preprocessing techniques

---

### Option B: Launch RIPE Atlas Measurements (Start 24h campaign)

```bash
cd /Users/ankitraj2/558/cdn-multimetric-selection
source venv/bin/activate
jupyter notebook notebooks/exploratory/03_ripe_atlas_measurements.ipynb
```

**Steps:**
1. Run all cells up to "Test Measurement" section
2. Set `TEST_MEASUREMENT = True` to launch a 1-hour test (5 probes)
3. Wait 10 minutes, then collect test results
4. If test works, set `LAUNCH_MEASUREMENTS = True` for full campaign
5. Let it run for 24 hours

**Timeline**: 
- Setup: 15 minutes
- Test: 1 hour
- Full campaign: 24 hours
- Results collection: 30 minutes

---

### Option C: Query M-Lab Data (Get 50K measurements)

```bash
cd /Users/ankitraj2/558/cdn-multimetric-selection
source venv/bin/activate
jupyter notebook notebooks/exploratory/02_mlab_real_data_collection.ipynb
```

**Steps:**
1. Run setup cells
2. Execute BigQuery query (takes ~30-60 seconds)
3. Get 50,000 real NDT measurements
4. Compare with synthetic data

**Timeline**: 15-20 minutes
**Cost**: $0 (within free tier)

---

## 💡 Recommended Workflow

### **TODAY** (1-2 hours):

1. **Explore Lumos5G** (45 min)
   ```bash
   jupyter notebook notebooks/exploratory/04_lumos5g_exploration.ipynb
   ```
   - Understand the 5G dataset
   - Analyze signal-throughput relationships
   - Generate visualizations

2. **Query M-Lab** (15 min)
   ```bash
   jupyter notebook notebooks/exploratory/02_mlab_real_data_collection.ipynb
   ```
   - Get 50K real measurements
   - Validate synthetic data model

3. **Launch RIPE Test** (15 min)
   ```bash
   jupyter notebook notebooks/exploratory/03_ripe_atlas_measurements.ipynb
   ```
   - Start 1-hour test measurement
   - Verify RIPE Atlas is working

### **TONIGHT** (15 min):
- Check RIPE test results
- If successful, launch 24-hour full campaign
- Go to bed while measurements run

### **TOMORROW** (3-4 hours):
- Collect RIPE Atlas results (24h data)
- Feature engineering notebook
- Merge all datasets
- Start ML model development

---

## 📊 Expected Outputs

### Lumos5G Analysis:
- ✅ `lumos5g_processed.csv` - Cleaned 5G data
- ✅ `lumos5g_5g_only.csv` - 5G-connected subset
- ✅ Correlation heatmap (signal vs throughput)
- ✅ Geographic throughput map
- ✅ Mobility mode comparison

### M-Lab Query:
- ✅ `mlab_ndt_us_30days.csv` - 50K measurements
- ✅ Real RTT vs throughput correlation
- ✅ Comparison with synthetic data

### RIPE Atlas:
- ✅ `ripe_measurement_ids.csv` - Active measurement IDs
- ✅ `ripe_atlas_results.csv` - Collected RTT data
- ✅ CDN performance comparison charts
- ✅ Time-series analysis (RTT over 24h)

---

## 🎯 Success Criteria

### After Lumos5G:
- [ ] Understand 5G signal-throughput relationship
- [ ] Generate 4+ visualizations
- [ ] Identify key features for ML models

### After M-Lab:
- [ ] Collect 50K+ real measurements
- [ ] Validate RTT-throughput correlation
- [ ] Confirm synthetic data accuracy

### After RIPE Atlas:
- [ ] 24h of CDN measurements
- [ ] 4-5 CDN providers compared
- [ ] RTT distribution by geographic region
- [ ] Identify best/worst performing CDNs

---

## 🆘 Troubleshooting

### Jupyter won't start:
```bash
source venv/bin/activate
pip install jupyter notebook
jupyter notebook
```

### RIPE Atlas API error:
- Check API keys in `.env` file
- Verify internet connection
- Try test measurement first

### BigQuery permission error:
- Verify billing is enabled
- Check project: `cdn-adv-comp-network-project`
- Re-run: `gcloud auth application-default login`

### Lumos5G file not found:
```bash
# Check if file exists
ls -lh Lumos5G-v1.0/Lumos5G-v1.0.csv

# If not, the path in notebook might need adjustment
```

---

## 📞 Next Steps After Data Collection

Once you have all three datasets:

1. **Feature Engineering** (Phase 5)
   - Merge M-Lab + RIPE + Lumos5G
   - Create derived features
   - Handle missing values

2. **ML Models** (Phase 6)
   - Train RTT-only baseline
   - Train multi-metric models
   - Compare performance

3. **CDN Selection Algorithm** (Phase 7)
   - Implement selection strategies
   - Simulate 1000 scenarios
   - Measure improvement

---

## ⚡ Quick Commands

```bash
# Activate environment
cd /Users/ankitraj2/558/cdn-multimetric-selection
source venv/bin/activate

# Start Jupyter
jupyter notebook

# Check API keys
cat .env | grep RIPE

# Check BigQuery
gcloud config get-value project
```

---

**Ready to start? I recommend beginning with Lumos5G exploration!**

Run: `jupyter notebook notebooks/exploratory/04_lumos5g_exploration.ipynb`
