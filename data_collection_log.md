# Data Collection Progress Log

**Project:** CDN Multi-Metric Server Selection
**Started:** November 11, 2025
**Goal:** Collect real-world network performance data from three sources to analyze multi-metric CDN selection

---

## Data Sources Overview

| Source | Status | Records Available | Collection Method |
|--------|--------|------------------|-------------------|
| M-Lab | ✅ **WORKING** | 144,248,971+ | BigQuery API |
| Lumos5G | ✅ **WORKING** | ~Dataset loaded~ | CSV file |
| RIPE Atlas | ❌ **BLOCKED** | N/A | API (needs credits) |

---

## Session Log

### 2025-11-11 00:46 - M-Lab Data Successfully Collected ✅

**Action:** Executed M-Lab data collection script

**Script:** `src/utils/mlab_data_collector.py`

**Result:** ✅ SUCCESS
- **Records Collected:** 50,000 measurements
- **Time Period:** October 12 - November 9, 2025 (30 days)
- **Data Processed:** 107.4 GB queried
- **Query Cost:** $0 (M-Lab Discuss member benefit)
- **Output File:** `data/raw/mlab_ndt_us_30days_20251111_004612.csv`

**Data Quality Metrics:**
- **Mean Download Speed:** 210.44 Mbps
- **Mean RTT:** 24.56 ms  
- **Mean Packet Loss:** 2.087%
- **Geographic Coverage:** 4,343 unique US cities
- **Server Coverage:** 126 unique M-Lab servers

**Top Measurement Locations:**
1. Chicago (1,801 measurements, 175.7 Mbps, 17.0 ms RTT)
2. New York (1,392 measurements, 236.0 Mbps, 16.6 ms RTT)
3. Los Angeles (1,271 measurements, 191.9 Mbps, 20.7 ms RTT)
4. Seattle (818 measurements, 179.2 Mbps, 15.5 ms RTT)
5. Miami (794 measurements, 225.7 Mbps, 13.7 ms RTT)

**Top M-Lab Servers:**
1. chs02 (Charleston) - 2,490 measurements (5.0%)
2. lax04 (Los Angeles) - 2,250 measurements (4.5%)
3. ord06 (Chicago O'Hare) - 2,195 measurements (4.4%)
4. lax06 (Los Angeles) - 2,191 measurements (4.4%)
5. ord03 (Chicago O'Hare) - 2,134 measurements (4.3%)

**Files Created:**
- `src/utils/mlab_data_collector.py` - Collection script with BigQuery integration
- `data/raw/mlab_ndt_us_30days_20251111_004612.csv` - 50K real measurements

---

### 2025-11-11 00:22 - M-Lab Access Verified

**Action:** Tested M-Lab BigQuery access after group membership propagation

**Command:**
```python
from google.cloud import bigquery
client = bigquery.Client(project='cdn-adv-comp-network-project')
query = 'SELECT COUNT(*) as count FROM `measurement-lab.ndt.unified_downloads` WHERE date >= "2025-10-01" LIMIT 1'
result = list(client.query(query).result())
```

**Result:** ✅ SUCCESS
- **Status:** M-Lab Discuss group membership active
- **Available Records:** 144,248,971 measurements (since Oct 1, 2025)
- **Cost:** $0 (M-Lab covers query costs for group members)
- **Next Step:** Create data collection script to pull relevant CDN measurements

---

### 2025-11-11 00:17-00:22 - RIPE Atlas Credit Issue

**Action:** Attempted to launch RIPE Atlas measurements via Python script

**Script:** `src/utils/ripe_atlas_test.py`
- Configuration: 2 probes, 10 minutes, 5-minute intervals
- Targets tested: OpenDNS, Quad9, Cloudflare, Google DNS

**Result:** ❌ FAILED - Insufficient credits
- **Credit Balance:** 0 credits
- **Required:** ~15 credits for minimal measurement
- **Error:** "You do not have enough credit to schedule this measurement"

**Blocker Analysis:**
- RIPE Atlas requires credits to schedule measurements
- Credits earned by:
  1. Initial grant: 5,000 credits for verified researchers
  2. Hosting probe: 50 credits/day
  3. Special contributions

**Action Required:**
- [ ] Request initial 5,000 credits at https://atlas.ripe.net/get-involved/benefits/
- [ ] Estimated wait time: 1-2 business days
- [ ] Alternative: Apply to host RIPE Atlas probe (50 credits/day)

---

### 2025-11-10 - Lumos5G Dataset Verified

**Action:** Tested Lumos5G exploration notebook

**Dataset:** `Lumos5G-v1.0/Lumos5G-v1.0.csv`
- **Source:** IMC'20 paper - Real 5G measurements from Minneapolis
- **Metrics:** Throughput, RSRP, RSRQ, SINR, GPS coordinates, mobility mode
- **Status:** ✅ Successfully loaded and readable
- **Notebook:** `notebooks/exploratory/04_lumos5g_exploration.ipynb`

---

## Current Status Summary

### ✅ Working Data Sources (2/3)

1. **M-Lab NDT Data** ✅ **COLLECTED**
   - **Status:** 50,000 measurements downloaded
   - **File:** `data/raw/mlab_ndt_us_30days_20251111_004612.csv`
   - **Coverage:** 4,343 US cities, 126 servers, 30 days
   - **Metrics:** Download throughput (210.44 Mbps avg), RTT (24.56 ms avg), packet loss (2.09% avg)
   - **Ready for analysis:** Yes

2. **Lumos5G Dataset** ✅ **READY**
   - Real 5G mobile network data
   - Minneapolis downtown area
   - Metrics: Throughput, signal strength, location

### ❌ Blocked Data Source (1/3)

3. **RIPE Atlas**
   - API working, probes accessible (13,095 active)
   - Cannot schedule measurements (0 credits)
   - Waiting for credit approval

---

## Next Steps

### ✅ Completed
- [x] Verify M-Lab access - **COMPLETED** ✅
- [x] Create M-Lab data collection script - **COMPLETED** ✅
- [x] Pull sample M-Lab CDN measurements - **COMPLETED** ✅ (50K records)
- [ ] Analyze Lumos5G dataset structure

### Ready for Analysis (Now)
- [ ] **Exploratory Data Analysis** on M-Lab dataset
  - RTT vs throughput correlation
  - Geographic performance patterns
  - Server performance comparison
  - Temporal patterns (by date/hour)
- [ ] **Combine with Lumos5G** for multi-network analysis
  - Compare wired/WiFi (M-Lab) vs 5G mobile (Lumos5G)
  - Identify network-specific patterns
- [ ] **Feature Engineering**
  - Distance calculations (client-server)
  - Network quality scores
  - Multi-metric composite features

### Pending (1-2 days)
- [ ] Submit RIPE Atlas credit request
- [ ] Wait for credit approval
- [ ] Launch RIPE Atlas CDN measurements

### Analysis Phase (After data collection)
- [ ] Compare RTT-throughput correlations across sources
- [ ] Identify multi-metric patterns
- [ ] Build predictive models
- [ ] Validate 15-30% improvement hypothesis

---

## Technical Configuration

**Environment:**
- Python 3.12.7 in virtual environment
- Google Cloud Project: `cdn-adv-comp-network-project`
- BigQuery billing: Enabled
- RIPE Atlas API: 9 keys configured (0 credits)

**Key Libraries:**
- google-cloud-bigquery 3.38.0
- ripe.atlas.cousteau 2.0.0
- pandas 2.3.3
- scikit-learn 1.7.2

---

## Notes

- **Data Quality Requirement:** ONLY real measurements (no synthetic data)
- **M-Lab Access:** Gained via M-Lab Discuss group membership (joined Nov 10)
- **RIPE Atlas Limitation:** 25 concurrent measurements per target IP
- **Popular DNS targets:** Often at concurrent limit (1.1.1.1, 8.8.8.8, 208.67.222.222)

---

*Last Updated: 2025-11-11 00:46 PST*

---

## Quick Reference: Available Datasets

| Dataset | File | Size | Records | Status |
|---------|------|------|---------|--------|
| M-Lab NDT | `data/raw/mlab_ndt_us_30days_20251111_004612.csv` | 7.0 MB | 50,000 | ✅ Ready |
| Lumos5G | `Lumos5G-v1.0/Lumos5G-v1.0.csv` | ~500 KB | ~5,000 | ✅ Ready |
| RIPE Atlas | N/A | N/A | 0 | ❌ Blocked (needs credits) |

**Total Real Measurements Collected:** 55,000+

**Analysis Ready:** YES - Can proceed with M-Lab + Lumos5G analysis while waiting for RIPE Atlas credits

