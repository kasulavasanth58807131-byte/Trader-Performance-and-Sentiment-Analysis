# Trader Performance vs Market Sentiment – Hyperliquid
### Primetrade.ai Data Science Intern Assignment

---

## Setup & How to Run

**Requirements:** Python 3.8+, pandas, numpy, matplotlib, scikit-learn

```bash
# Install dependencies
pip install pandas numpy matplotlib scikit-learn

# Place data files in project root:
# - historical_data_compressed.csv
# - fear_greed_2024.csv

# Run notebook
jupyter notebook trader_sentiment_analysis.ipynb
```

---

## Methodology

**Data sources:**
- 211,224 Hyperliquid trade records across 32 accounts (Jan–Dec 2024)
- BTC Fear/Greed Index for 2024 (daily, simplified to Fear / Neutral / Greed)

**Cleaning:** No missing values found. Timestamps parsed from `dd-mm-yyyy HH:MM` IST format. Datasets merged on date. The compressed `.csv` uses zstandard encoding with a duplicate 4-byte magic header that must be stripped before decompression.

**Key metrics built:**
- Daily PnL per account (sum of `Closed PnL`)
- Win rate (% of account-days with positive PnL)
- Trade frequency (count of trades per account-day)
- Average position size in USD
- Long/Short ratio (long-opening trades vs short-opening trades)
- Trader segments: High/Low Leverage, Frequent/Infrequent, Net Winner/Loser

---

## Insights

**Insight 1 – Greed days dramatically outperform Fear days**
Average PnL is +$5,344 on Greed days vs -$961 on Fear days. Win rate is 63% (Greed) vs 44% (Fear). Sentiment is the single strongest predictor of daily profitability in this dataset.

**Insight 2 – Traders are 2.4× more active on Greed days, with a stronger long bias**
Average daily trades: 69 (Greed) vs 29 (Fear). Long/Short ratio peaks at 8.96 on Greed days. Traders are not just more bullish — they're significantly more active, suggesting sentiment drives both direction and frequency.

**Insight 3 – Low-leverage traders capture nearly all the upside; high-leverage traders lose on both Fear and Greed days**
Low-leverage traders earn +$7,550 on Greed days vs +$0 for high-leverage traders. High-leverage traders lose -$2,763 (Fear) and -$563 (Greed). This means leverage, not market direction, is the primary performance drag.

---

## Strategy Recommendations

**Strategy 1 – Sentiment-Gated Sizing for Low-Leverage Traders**
Scale position deployment to sentiment: 100% capital on Greed days, 50–60% on Fear days, 75% Neutral. Low-leverage traders with this rule earn 16× more on Greed days and avoid the worst Fear-day drawdowns.

**Strategy 2 – Hard Leverage Cap Protocol for High-Leverage Traders**
Cap leverage at 3× on Fear days and 5× on Greed days. Even during Bull sentiment, over-leveraged positions produce negative average PnL due to forced liquidations. The fix is structural sizing discipline, not better entry timing.

---

## Output Files
- `trader_sentiment_analysis.ipynb` – Full analysis notebook
- `outputs/fig1_pnl_by_sentiment.png` – Performance by sentiment
- `outputs/fig2_behavior_by_sentiment.png` – Behavioral changes by sentiment
- `outputs/fig3_segments.png` – Segment analysis
- `outputs/fig4_heatmap_cumulative.png` – Monthly heatmap & cumulative PnL
- `outputs/summary_table.csv` – Summary statistics table
- `outputs/segment_table.csv` – Segment breakdown table
