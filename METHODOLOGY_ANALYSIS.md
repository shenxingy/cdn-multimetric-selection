# Critical Methodology Analysis: Teammate's Screenshot vs Dashboard Claims

**Date:** November 18, 2025  
**Status:** CRITICAL ISSUE IDENTIFIED

---

## Executive Summary

Your teammate's screenshot reveals a **fundamental flaw** in our dashboard's 610% improvement claim. The validation confirms:

- **Dashboard's claim:** 474% improvement (varies by dataset, ~610% in some runs)
- **Realistic improvement:** **13.8%** when using only predictive metrics
- **Root cause:** Dashboard uses historical throughput in the composite score

---

## The Two Methodologies Compared

### Teammate's Approach (Screenshot) ✓ CORRECT

**What they did:**
1. Train ML models to **predict** throughput using RTT, loss, and other features
2. For server selection: Use predicted throughput to choose which server
3. Compare actual throughput outcomes

**Results from screenshot:**
- Method 1 (Min RTT): **142.86 Mbps** ← BEST
- Model A (Linear Regression): 123.32 Mbps (-13.67%)
- Model B (Ridge Regression): 122.31 Mbps (-14.38%)
- Model C (Neural Network): 140.27 Mbps (-1.81%)

**Why this is valid:**
- Uses only predictive features (RTT, loss, etc.)
- Cannot see future throughput before selection
- Represents real-world CDN selection scenario
- R² values (5.7%, 11.7%, 20.5%) correctly show weak predictability

**Conclusion:** RTT-only wins because throughput is hard to predict

---

### Dashboard's Approach (Current) ✗ FLAWED

**What it does:**
```python
# From dashboard.py lines 140-144
df['composite_score'] = (
    0.3 * df['rtt_score'] + 
    0.4 * df['throughput_score'] +  # ← PROBLEM: Uses actual throughput!
    0.3 * df['loss_score']
)
```

**The flaw:**
- `throughput_score` is normalized actual throughput from the measurement
- This is **future knowledge** - you don't know throughput until AFTER selection
- It's circular reasoning: "Use throughput to predict throughput"

**Why it shows 610% improvement:**
- Of course selecting servers with highest throughput gives high throughput!
- It's essentially: "If we choose the servers that turned out to be fast, we get fast speeds"
- This is **oracle-level performance**, not a selection algorithm

---

## Validation Results

I created `validate_methodology.py` which tests both approaches:

### Dashboard's Method (Using Future Throughput)
```
RTT-only median:     161.0 Mbps
Multi-metric median: 924.3 Mbps
Improvement:         474.1%  ← Inflated by cheating
```

### Realistic Method (Only Predictive Metrics)
```
RTT-only median:     161.0 Mbps
Multi-metric median: 183.3 Mbps
Improvement:         13.8%   ← Actual improvement
```

**Conclusion:** The 610% claim collapses to 13.8% when methodology is corrected.

---

## Why Your Teammate's Skepticism is Valid

Your teammate correctly identified that:

1. **Prediction models fail:** R² < 21% for all models means throughput is hard to predict
2. **RTT-only wins:** Among predictive approaches, minimum RTT is best
3. **Something is wrong:** Dashboard claims 610% improvement, but prediction fails

The screenshot shows **exactly what should happen** when you try to predict throughput:
- RTT has some signal (r = -0.161, explains 2.6% variance)
- But it's weak, so RTT-only is still best among weak predictors
- Complex models don't help because the signal is inherently noisy

---

## What This Means for the Research

### The Good News
- Variable importance analysis is **correct**: RTT explains only 2.6% of variance ✓
- Correlation studies are **valid**: r = -0.161 for RTT vs throughput ✓
- The insight that "RTT alone is insufficient" is **true** ✓
- RSRP analysis (22.3% R²) for 5G is **valuable** ✓

### The Bad News
- The 610% improvement claim is **invalid** ✗
- The composite scoring approach is **unrealistic** ✗
- The "96.7% of oracle" claim is **circular** ✗
- Statistical validation (Cohen's d = 1.77) validates a **flawed methodology** ✗

### What Actually Works
From the validation script:
- RTT + Loss scoring: **13.8% improvement** ← This is real
- This aligns with literature suggesting 15-30% improvement
- More modest, but scientifically sound

---

## Recommendations

### Option 1: Honest Revision (Recommended)
1. Remove 610% claim from all documents and dashboard
2. Update to realistic 13.8% improvement (RTT + Loss only)
3. Add section explaining why prediction is difficult (low R²)
4. Frame research around "modest but consistent improvement"
5. Emphasize 5G RSRP findings (22.3% R² is significant)

### Option 2: Reframe as Oracle Study
1. Keep 610% but clearly state it's "oracle with perfect historical knowledge"
2. Change claim: "If you had historical throughput data, you could achieve 610%"
3. Show 13.8% as "realistic without historical data"
4. Useful for caching scenarios where you DO have historical data

### Option 3: Pivot to Different Approach
1. Focus on time-series prediction (historical → future throughput)
2. Use composite score for **re-selection** not initial selection
3. Investigate when historical data is available (CDN with memory)
4. This validates current methodology for specific use case

---

## Comparison with Google's "Beyond RTT" Research

**Google's approach (correct):**
- Used TTFB (Time To First Byte) as predictive metric
- TTFB measured by active probing BEFORE full data transfer
- Proprietary features from Google's infrastructure
- Reported modest improvements (not 600%+)

**Our approach (current):**
- Uses actual throughput (measured AFTER data transfer)
- Public datasets with limited predictive features
- Claims 610% improvement via circular methodology

**The difference:**
- Google predicts future performance from signals
- We "predict" performance by using the performance itself

---

## Action Items

### Immediate (Today)
- [ ] Run `validate_methodology.py` to confirm findings
- [ ] Share validation results with team
- [ ] Decide on Option 1, 2, or 3 above
- [ ] Update dashboard claims

### Short-term (This Week)
- [ ] Revise all documentation (README, RESULTS, DISCUSSION)
- [ ] Update Executive Summary metrics
- [ ] Retrain models using only predictive features
- [ ] Re-run statistical validation on correct methodology

### Medium-term (Before Submission)
- [ ] Investigate if historical data improves re-selection
- [ ] Analyze temporal patterns (does past predict future?)
- [ ] Compare with teammate's ML approach
- [ ] Write honest limitations section

---

## Technical Details

### Why Throughput is Hard to Predict

From the data:
- RTT correlation: r = -0.161 (R² = 2.6%)
- Loss correlation: r = -0.111 (R² = 1.2%)
- Combined R² < 4% (very weak)

**Reasons:**
1. **Server-side factors:** CPU load, cache state, bandwidth
2. **Network congestion:** Dynamic, not captured by single RTT
3. **Client factors:** Device capability, local network
4. **Application layer:** TCP slow start, window sizing
5. **Measurement noise:** Single throughput test is noisy

### Why Dashboard's Score "Works"

```python
# If you select by this score:
score = 0.3 * RTT_score + 0.4 * THROUGHPUT_score + 0.3 * Loss_score

# And THROUGHPUT_score is normalized actual throughput:
THROUGHPUT_score = normalize(actual_throughput)

# Then of course you select high-throughput servers!
# But you can't do this in practice because you don't know
# actual_throughput until AFTER the selection
```

It's like saying: "If we could see the future, we'd make better decisions" - technically true, but not useful.

---

## Conclusion

**Your teammate's screenshot is correct.** It shows that:
1. Predicting throughput from RTT/loss is difficult (R² < 21%)
2. Among prediction approaches, RTT-only is actually best
3. The dashboard's 610% claim uses future knowledge (cheating)

**The validation confirms:**
- Dashboard method: 474% (uses throughput in score)
- Realistic method: 13.8% (RTT + loss only)
- Teammate's result: RTT-only wins when predicting

**Recommendation:** Revise claims to 13.8% improvement, acknowledge teammate's finding, and focus on realistic methodology or pivot to historical-data use case.
