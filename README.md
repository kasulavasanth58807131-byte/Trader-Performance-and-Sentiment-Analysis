# 📊 Trader Performance vs Market Sentiment
**Primetrade.ai — Data Science Intern Assignment**

Analyzes how Bitcoin market sentiment (Fear/Greed Index) relates to trader behavior and performance on Hyperliquid.

---

## 🗂️ Project Structure

```
primetrade_project/
├── app.py                   # Streamlit dashboard (main entry point)
├── analysis_notebook.py     # Standalone analysis script (generates charts)
├── src/
│   └── analysis.py          # Core data loading, cleaning & metric computation
├── data/
│   ├── fear_greed_index.csv
│   └── historical_data.csv
├── charts/                  # Auto-generated chart PNGs
├── requirements.txt
└── README.md
```

---

## 🚀 Setup & Run

### 1. Clone / download
```bash
git clone <your-repo-url>
cd primetrade_project
```

### 2. Install dependencies
```bash
pip install -r requirements.txt
```

### 3. Add data files
Place your CSVs in the `data/` directory:
- `data/fear_greed_index.csv`
- `data/historical_data.csv`

### 4a. Run the Streamlit dashboard
```bash
streamlit run app.py
```
Opens at `http://localhost:8501`

### 4b. Or run the standalone analysis script
```bash
python analysis_notebook.py
```
Prints a full analysis report to stdout and saves 5 charts to `charts/`.

---

## 🌐 Deploy to Streamlit Cloud

1. Push this repo to GitHub (include `data/` folder or update paths if using a remote source)
2. Go to [share.streamlit.io](https://share.streamlit.io)
3. Connect your GitHub repo
4. Set **Main file path** to `app.py`
5. Click **Deploy**

> ⚠️ For large data files (>100MB), consider hosting them on S3/GDrive and loading via URL in `src/analysis.py`.

---

## 📋 Methodology

### Data Preparation (Part A)
- **Fear/Greed Index**: 2,644 daily records (2018–2025), no missing values. Classified into 3 buckets: Fear, Neutral, Greed.
- **Hyperliquid Trades**: 211,224 trade records across hundreds of wallets. Timestamp parsed from IST strings. Filtered to meaningful trade directions (Open/Close Long/Short, Buy/Sell).
- **Merge**: Inner join on date — overlapping period used for analysis.
- **Key derived metrics**: leverage proxy (Size USD / |Start Position|), is_close flag, long/short flags, daily PnL aggregations.

### Analysis (Part B)
- **Q1 — Performance**: Compared avg/median daily PnL, win rate, and PnL distribution across sentiment buckets.
- **Q2 — Behavior**: Examined trade frequency, leverage, long/short ratio, and position size by sentiment regime.
- **Q3 — Segments**: Traders segmented into leverage tiers (Low/Mid/High), frequency tiers (Frequent/Infrequent), and consistency tiers (Consistent Winner / Inconsistent Winner / Loser).
- **Cross-analysis**: Heatmaps of PnL and win rate across segment × sentiment combinations.

---

## 💡 Key Insights

1. **Greed days outperform on every metric** — highest avg PnL, win rate, and trade activity. Long bias pays off.
2. **High leverage amplifies losses on Fear days disproportionately** — low-leverage traders show more stable returns across all regimes.
3. **Overtrading on Fear days is penalised** — days with above-median trade counts during Fear show lower average PnL than restrained Fear days.

---

## 📌 Strategy Recommendations (Part C)

### Strategy 1 — Fear Pullback Rule
- High-leverage traders: reduce leverage ≥30% on Fear days
- Reduce trade frequency; overtrading in fear regimes destroys value
- Avoid long bias — win rates don't support dip-buying during fear

### Strategy 2 — Greed Momentum Rule
- Increase position **size** (not leverage) by up to 20% on confirmed Greed days
- Lean long: L/S ratio above 1.0 is validated by higher win rates
- Frequent, low-leverage traders benefit most — maintain/increase trade frequency

### Strategy 3 — Neutral Days = Reduce Exposure
- Reduce trade size 15–25%; prefer closing existing positions over opening new ones
- Use neutral days for rebalancing, not active speculation

---

## 🔧 Tech Stack
- **Python** 3.9+
- **pandas / numpy** — data wrangling
- **plotly** — interactive charts in dashboard
- **matplotlib / seaborn** — static charts (notebook script)
- **Streamlit** — interactive dashboard
