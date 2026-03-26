# Beyond Round-Trip Time: A Multi-Metric Approach to Client-Driven CDN Server Selection

**Authors:** Wajiha Naveed · Ankit Raj · Alex Shen  
**Affiliation:** Duke University  
**Date:** October 17, 2025

---

## 📖 Overview

Recent measurement studies show that the fastest CDN paths are not always those with the lowest round-trip time (RTT). Factors like congestion, cache load, and routing policies can degrade throughput even with low latency.

This project investigates how clients can make better CDN server choices by combining RTT with **Time to First Byte (TTFB)** and **packet loss** — resulting in a lightweight, interpretable selection metric.

> **Goal:** Demonstrate that a simple multi-metric approach can improve median and tail throughput compared to RTT-only selection.

---

## 🧪 Methods

1. **Synthetic Data Generation**  
   - 100–500 samples simulating CDN metrics (RTT, TTFB, loss, throughput).

2. **Real Dataset Analysis**  
   - RIPE Atlas: global ping/loss measurements.  
   - M-Lab: throughput and latency data across regions.

3. **Metric Design**  
   - Composite score:  
     \[
     Score = α(1/RTT) + β(1/TTFB) - γ(Loss)
     \]
   - Evaluate against baseline RTT-only selection.

4. **Evaluation Metrics**  
   - Median and 90th percentile throughput improvements.

---

## 📊 Project Structure

```

data/         → raw & processed datasets
notebooks/    → exploratory & regression notebooks
src/          → data collection + scoring scripts
docs/         → figures, reports, and paper drafts
results/      → final visualizations and analysis outputs

````

---

## 🧰 Tools & Dependencies

- **Languages & Libraries:** Python 3.8+, pandas, numpy, scikit-learn, matplotlib, seaborn
- **Measurement:** RIPE Atlas API, M-Lab
- **Optional:** TensorFlow or PyTorch (for extended analysis)

```bash
# Install dependencies
pip install -r requirements.txt
````

---

## 🌐 Data Sources

* [RIPE Atlas](https://atlas.ripe.net/)
* [M-Lab](https://www.measurementlab.net/data/)
* [Lumos5G Dataset (IEEE DataPort)](https://ieee-dataport.org/)

---

## 🚀 Getting Started

```bash
# Clone repo
git clone https://github.com/shenxingy/cdn-multimetric-selection.git
cd cdn-multimetric-selection

# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Set up environment variables
cp .env.example .env
# Edit .env and fill in RIPE_ATLAS_PRIMARY_KEY and GCP_PROJECT_ID
```

Run Jupyter Notebook:

```bash
jupyter notebook notebooks/
```

---

## 🧭 Contributing

We welcome contributions! Please:

1. Create a feature branch (`git checkout -b feature/xyz`)
2. Commit changes (`git commit -m "Add feature xyz"`)
3. Push branch (`git push origin feature/xyz`)
4. Open a Pull Request.

---

## 📜 License

This project is released under the [MIT License](LICENSE).

---

## 🧾 Citation

If you use this repository in your research, please cite:

> Naveed, W., Raj, A., & Shen, A. (2025). *Beyond Round-Trip Time: A Multi-Metric Approach to Client-Driven CDN Server Selection*. Duke University.

---

## 📬 Contact

* Alex Shen — [GitHub](https://github.com/shenxingy)
* Wajiha Naveed — Duke University
* Ankit Raj — Duke University
