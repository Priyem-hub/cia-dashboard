# 🛰 Global Conflict Intelligence Dashboard

> A CIA-style geopolitical intelligence platform that visualizes global conflict
> hotspots, ranks threat zones, and simulates risk scenarios using machine learning.

---

## Overview

The **Global Conflict Intelligence Dashboard (GCID)** is a full-stack Python
data application built with Streamlit, PyDeck, and Plotly. It ingests a
geopolitical conflict dataset and presents analysts with:

| Feature | Description |
|---------|-------------|
| 🌍 **Interactive 3D Globe** | PyDeck ScatterplotLayer with glowing red hotspot markers and hover tooltips |
| ⚠️ **Threat Ranking Table** | All indexed nations ranked by risk score with visual risk bars and badges |
| 📊 **Analytics Suite** | Distribution histograms, regional averages, scatter correlations, treemaps, feature-importance donut |
| 🤖 **Scenario Simulator** | Adjust 4 geopolitical sliders → ML model returns risk score, level, confidence interval, and per-factor contribution |
| 🔬 **Sensitivity Analysis** | Live chart showing how each parameter independently drives risk |

**Aesthetic**: dark intelligence-console theme with Orbitron / Share Tech Mono
typography, glowing red threat markers, and scanline overlay.

---

## Project Structure

```
global-conflict-intelligence/
│
├── app.py              ← Streamlit dashboard (UI, maps, charts, simulator)
├── conflict_model.py   ← ML model (GradientBoostingRegressor + scikit-learn)
├── dataset.csv         ← 40-row geopolitical dataset
├── requirements.txt    ← Python dependencies
└── README.md           ← This file
```

---

## Installation

### Prerequisites
- Python 3.10 or higher
- pip

### Steps

```bash
# 1. Clone / download the project folder
cd global-conflict-intelligence

# 2. (Recommended) Create a virtual environment
python -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate

# 3. Install dependencies
pip install -r requirements.txt
```

---

## Running the App

```bash
streamlit run app.py
```

The dashboard will open automatically at **http://localhost:8501**

---

## Machine Learning Model

`conflict_model.py` implements a `ConflictRiskModel` class backed by a
scikit-learn `GradientBoostingRegressor` inside a `Pipeline` (with `StandardScaler`).

### Input Features

| Feature | Range | Effect |
|---------|-------|--------|
| `military_spending` | 0–25 % GDP | Higher → more risk |
| `sanctions` | 0–10 index | Higher → more risk |
| `trade_dependency` | 0–10 index | Higher → **less** risk |
| `diplomatic_stability` | 0–10 index | Higher → **less** risk |

### Training

The model is trained on the 40-row CSV **plus 600 synthetic samples** generated
from domain-encoded rules. This prevents overfitting on the small real dataset
while encoding geopolitical logic.

### API

```python
from conflict_model import get_model

model = get_model()           # lazy-init singleton

result = model.predict(
    military_spending=8.5,
    sanctions=9.0,
    trade_dependency=2.0,
    diplomatic_stability=1.5,
)
# result = {
#   "risk_score": 91.3,
#   "risk_level": "CRITICAL",
#   "risk_level_color": "#FF0000",
#   "confidence_band": (87.1, 95.5),
#   "contributing_factors": {...}
# }
```

---

## Deployment to Streamlit Cloud

1. **Push to GitHub**

   ```bash
   git init
   git add .
   git commit -m "Initial commit – GCID"
   git remote add origin https://github.com/<you>/global-conflict-intelligence.git
   git push -u origin main
   ```

2. **Log in** at [share.streamlit.io](https://share.streamlit.io)

3. **New app** → connect your GitHub repo → set:
   - **Main file path**: `app.py`
   - **Python version**: 3.11

4. Click **Deploy** — Streamlit Cloud installs `requirements.txt` automatically.

5. (Optional) Add a `secrets.toml` via the Streamlit Cloud dashboard if you
   wire in a real Mapbox token:
   ```toml
   MAPBOX_TOKEN = "pk.eyJ1IjoiL..."
   ```
   Then in `app.py` pass it to `pdk.Deck(mapbox_key=st.secrets["MAPBOX_TOKEN"])`.

---

## Customisation

| What | Where |
|------|-------|
| Add countries / update scores | `dataset.csv` |
| Tune ML hyper-parameters | `conflict_model.py` → `GradientBoostingRegressor(...)` |
| Change colour scheme | `app.py` → `GLOBAL CSS` block |
| Add new analytics charts | `app.py` → TAB 3 section |
| Swap map style | `app.py` → `map_style=` argument in `pdk.Deck` |

---

## Data Disclaimer

All data in `dataset.csv` is **synthetic / illustrative** and intended solely
for demonstration purposes. Risk scores do not represent real intelligence
assessments. This project is **NOT for operational use**.

---

## Tech Stack

| Library | Version | Purpose |
|---------|---------|---------|
| `streamlit` | ≥1.35 | Web framework + UI |
| `pydeck` | ≥0.9 | WebGL geospatial map |
| `plotly` | ≥5.22 | Interactive charts |
| `pandas` | ≥2.2 | Data manipulation |
| `numpy` | ≥1.26 | Numerical ops |
| `scikit-learn` | ≥1.4 | ML model |

---

*Global Conflict Intelligence Dashboard — demonstration project*
