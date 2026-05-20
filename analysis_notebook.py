"""
analysis_notebook.py
────────────────────
Full EDA pipeline: Part A (prep), Part B (analysis), Part C (strategy).
Run:  python analysis_notebook.py
Outputs: charts/ folder + prints a markdown summary to stdout.
"""

import warnings
warnings.filterwarnings("ignore")

import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

import pandas as pd
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
import seaborn as sns
from pathlib import Path

from src.analysis import load_all

# ─── style ───────────────────────────────────────────────────────────────────
PALETTE = {"Fear": "#e05c5c", "Neutral": "#f0a500", "Greed": "#4caf50"}
sns.set_theme(style="whitegrid", font_scale=1.1)
CHARTS = Path("charts")
CHARTS.mkdir(exist_ok=True)

print("Loading data …")
d = load_all()
fg          = d["fg"]
trades      = d["trades"]
merged      = d["merged"]
daily       = d["daily"]
t_stats     = d["trader_stats"]
summary     = d["sentiment_summary"]
seg_cross   = d["segment_cross"]

# ════════════════════════════════════════════════════════════════════════════
# PART A — DATA PREPARATION REPORT
# ════════════════════════════════════════════════════════════════════════════
print("\n" + "="*60)
print("PART A — DATA PREPARATION")
print("="*60)
print(f"\nFear/Greed index  : {fg.shape[0]:,} rows × {fg.shape[1]} cols")
print(f"  Date range      : {fg['date'].min().date()} → {fg['date'].max().date()}")
print(f"  Missing values  : {fg.isnull().sum().sum()}")
print(f"  Duplicates      : {fg.duplicated().sum()}")
print(f"\nTrader data (raw) : {trades.shape[0]:,} rows × {trades.shape[1]} cols")
print(f"  Unique accounts : {trades['Account'].nunique():,}")
print(f"  Unique coins    : {trades['Coin'].nunique()}")
print(f"  Date range      : {trades['date'].min().date()} → {trades['date'].max().date()}")
print(f"  Missing values  : {trades.isnull().sum().sum()}")
print(f"\nMerged (overlap)  : {merged.shape[0]:,} rows")
print(f"  Overlap dates   : {merged['date'].nunique()} days")
print(f"\nSentiment distribution (full FG):")
print(fg["classification"].value_counts().to_string())

# ════════════════════════════════════════════════════════════════════════════
# PART B — ANALYSIS
# ════════════════════════════════════════════════════════════════════════════
print("\n" + "="*60)
print("PART B — ANALYSIS")
print("="*60)

# ── Q1: Performance by sentiment ─────────────────────────────────────────────
print("\n[Q1] Performance (PnL, Win Rate) by Sentiment\n")
print(summary[["sentiment_bucket","days","avg_daily_pnl","median_daily_pnl","avg_win_rate"]].to_string(index=False))

# Chart 1 — Avg Daily PnL by Sentiment
fig, axes = plt.subplots(1, 3, figsize=(15, 5))
order = ["Fear", "Neutral", "Greed"]

ax = axes[0]
bars = ax.bar(order, summary.set_index("sentiment_bucket").loc[order, "avg_daily_pnl"],
              color=[PALETTE[s] for s in order], edgecolor="white", linewidth=1.5)
ax.bar_label(bars, fmt="%.0f", padding=3, fontsize=9)
ax.set_title("Avg Daily PnL by Sentiment", fontweight="bold")
ax.set_ylabel("USD")
ax.axhline(0, color="black", linewidth=0.7)

ax = axes[1]
bars = ax.bar(order, summary.set_index("sentiment_bucket").loc[order, "avg_win_rate"] * 100,
              color=[PALETTE[s] for s in order], edgecolor="white", linewidth=1.5)
ax.bar_label(bars, fmt="%.1f%%", padding=3, fontsize=9)
ax.set_title("Avg Win Rate (%) by Sentiment", fontweight="bold")
ax.set_ylabel("%")
ax.set_ylim(0, 80)

ax = axes[2]
# PnL distribution violin
plot_data = []
for bucket in order:
    subset = daily[daily["sentiment_bucket"] == bucket]["total_pnl"]
    plot_data.append(subset.values)
vp = ax.violinplot(plot_data, positions=[1, 2, 3], showmedians=True)
for i, (body, color) in enumerate(zip(vp["bodies"], [PALETTE[s] for s in order])):
    body.set_facecolor(color)
    body.set_alpha(0.7)
ax.set_xticks([1, 2, 3])
ax.set_xticklabels(order)
ax.set_title("Daily PnL Distribution", fontweight="bold")
ax.set_ylabel("USD")
ax.axhline(0, color="black", linewidth=0.7, linestyle="--")

plt.tight_layout()
plt.savefig(CHARTS / "chart1_pnl_by_sentiment.png", dpi=150, bbox_inches="tight")
plt.close()
print("  → Saved chart1_pnl_by_sentiment.png")

# ── Q2: Behavior by sentiment ─────────────────────────────────────────────────
print("\n[Q2] Trader Behavior by Sentiment\n")
print(summary[["sentiment_bucket","avg_trades","avg_leverage","avg_long_short_ratio","avg_size_usd"]].to_string(index=False))

# Chart 2 — Behavior metrics
fig, axes = plt.subplots(1, 4, figsize=(18, 5))
metrics = [
    ("avg_trades",           "Avg Trades / Day",     "count"),
    ("avg_leverage",         "Avg Leverage (proxy)",  "x"),
    ("avg_long_short_ratio", "Long/Short Ratio",      ""),
    ("avg_size_usd",         "Avg Trade Size (USD)",  "$"),
]
for ax, (col, title, unit) in zip(axes, metrics):
    vals = summary.set_index("sentiment_bucket").loc[order, col]
    bars = ax.bar(order, vals, color=[PALETTE[s] for s in order], edgecolor="white", linewidth=1.5)
    ax.bar_label(bars, fmt=f"%.1f{unit}", padding=3, fontsize=9)
    ax.set_title(title, fontweight="bold")
    if col == "avg_long_short_ratio":
        ax.axhline(1.0, color="black", linewidth=0.8, linestyle="--", label="Balanced")
        ax.legend(fontsize=8)

plt.suptitle("Trader Behavior Across Sentiment Regimes", fontsize=13, fontweight="bold", y=1.02)
plt.tight_layout()
plt.savefig(CHARTS / "chart2_behavior_by_sentiment.png", dpi=150, bbox_inches="tight")
plt.close()
print("  → Saved chart2_behavior_by_sentiment.png")

# ── Q3: Trader Segments ────────────────────────────────────────────────────────
print("\n[Q3] Trader Segments\n")

# Leverage tiers
lev_summary = t_stats.groupby("leverage_tier", observed=True).agg(
    traders=("Account", "count"),
    avg_total_pnl=("total_pnl", "mean"),
    avg_win_rate=("win_rate", "mean"),
    avg_leverage=("avg_leverage", "mean"),
).reset_index()
print("Leverage Tiers:")
print(lev_summary.to_string(index=False))

# Consistency tiers
con_summary = t_stats.groupby("consistency_tier").agg(
    traders=("Account", "count"),
    avg_total_pnl=("total_pnl", "mean"),
    avg_win_rate=("win_rate", "mean"),
    avg_trades=("trade_count", "mean"),
).reset_index().sort_values("avg_total_pnl", ascending=False)
print("\nConsistency Tiers:")
print(con_summary.to_string(index=False))

# Chart 3 — Segment performance
fig, axes = plt.subplots(1, 3, figsize=(18, 5))

# Leverage scatter
ax = axes[0]
colors_lev = {"Low Leverage": "#4caf50", "Mid Leverage": "#f0a500", "High Leverage": "#e05c5c"}
for tier in t_stats["leverage_tier"].dropna().unique():
    sub = t_stats[t_stats["leverage_tier"] == tier]
    ax.scatter(sub["avg_leverage"], sub["total_pnl"],
               alpha=0.5, label=str(tier), color=colors_lev.get(str(tier), "grey"), s=20)
ax.axhline(0, color="black", linewidth=0.7, linestyle="--")
ax.set_xlabel("Avg Leverage Proxy")
ax.set_ylabel("Total PnL (USD)")
ax.set_title("Leverage vs Total PnL", fontweight="bold")
ax.legend(fontsize=8)

# Frequency tier win rates
ax = axes[1]
freq_data = t_stats.groupby("frequency_tier", observed=True)["win_rate"].mean().reset_index()
bars = ax.bar(freq_data["frequency_tier"].astype(str),
              freq_data["win_rate"] * 100,
              color=["#4caf50", "#2196F3"], edgecolor="white", linewidth=1.5)
ax.bar_label(bars, fmt="%.1f%%", padding=3)
ax.set_title("Win Rate by Trade Frequency", fontweight="bold")
ax.set_ylabel("%")

# Consistency tier total PnL
ax = axes[2]
con_order = ["Consistent Winner", "Inconsistent Winner", "Loser"]
con_vals = con_summary.set_index("consistency_tier")
con_colors = {"Consistent Winner": "#4caf50", "Inconsistent Winner": "#f0a500", "Loser": "#e05c5c"}
present = [c for c in con_order if c in con_vals.index]
bars = ax.bar(present,
              [con_vals.loc[c, "avg_total_pnl"] for c in present],
              color=[con_colors[c] for c in present], edgecolor="white", linewidth=1.5)
ax.bar_label(bars, fmt="%.0f", padding=3, fontsize=9)
ax.axhline(0, color="black", linewidth=0.7)
ax.set_title("Avg Total PnL by Consistency Tier", fontweight="bold")
ax.set_ylabel("USD")

plt.suptitle("Trader Segments", fontsize=13, fontweight="bold", y=1.02)
plt.tight_layout()
plt.savefig(CHARTS / "chart3_trader_segments.png", dpi=150, bbox_inches="tight")
plt.close()
print("  → Saved chart3_trader_segments.png")

# Chart 4 — Leverage tier x Sentiment heatmap
pivot_pnl = seg_cross.pivot(index="leverage_tier", columns="sentiment_bucket", values="avg_pnl")
pivot_wr  = seg_cross.pivot(index="leverage_tier", columns="sentiment_bucket", values="win_rate")

fig, axes = plt.subplots(1, 2, figsize=(14, 4))

for ax, pivot, title, fmt in zip(
    axes,
    [pivot_pnl, pivot_wr],
    ["Avg PnL: Leverage Tier × Sentiment", "Win Rate: Leverage Tier × Sentiment"],
    [".0f", ".2f"]
):
    sns.heatmap(pivot, annot=True, fmt=fmt, cmap="RdYlGn", ax=ax,
                linewidths=0.5, linecolor="white", annot_kws={"fontsize": 11})
    ax.set_title(title, fontweight="bold")
    ax.set_xlabel("Sentiment")
    ax.set_ylabel("Leverage Tier")

plt.tight_layout()
plt.savefig(CHARTS / "chart4_heatmap_segment_x_sentiment.png", dpi=150, bbox_inches="tight")
plt.close()
print("  → Saved chart4_heatmap_segment_x_sentiment.png")

# Chart 5 — Time series: rolling PnL + sentiment overlay
daily_sorted = daily.sort_values("date")
fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(16, 7), sharex=True)

ax1.plot(daily_sorted["date"], daily_sorted["total_pnl"].rolling(7).mean(),
         color="#2196F3", linewidth=1.5, label="7-day rolling PnL")
ax1.axhline(0, color="black", linewidth=0.7, linestyle="--")
for bucket, color in PALETTE.items():
    mask = daily_sorted["sentiment_bucket"] == bucket
    ax1.fill_between(daily_sorted["date"], daily_sorted["total_pnl"].rolling(7).mean(),
                     where=mask, alpha=0.15, color=color, label=bucket)
ax1.set_ylabel("Total PnL (USD)")
ax1.set_title("Daily Aggregate PnL with Sentiment Overlay", fontweight="bold")
ax1.legend(fontsize=8)

ax2.plot(daily_sorted["date"], daily_sorted["trade_count"].rolling(7).mean(),
         color="#9C27B0", linewidth=1.5)
ax2.set_ylabel("Trade Count (7d avg)")
ax2.set_xlabel("Date")
ax2.set_title("Trade Activity Over Time", fontweight="bold")

plt.tight_layout()
plt.savefig(CHARTS / "chart5_timeseries.png", dpi=150, bbox_inches="tight")
plt.close()
print("  → Saved chart5_timeseries.png")

# ════════════════════════════════════════════════════════════════════════════
# PART C — STRATEGY IDEAS
# ════════════════════════════════════════════════════════════════════════════
print("\n" + "="*60)
print("PART C — STRATEGY RECOMMENDATIONS")
print("="*60)
print("""
Strategy 1 — "Fear Pullback Rule"
  During Fear/Extreme Fear days:
  • Consistent Winner traders should REDUCE leverage by ≥30% (data shows
    high-leverage traders lose the most on Fear days).
  • Maintain a long bias only if win rate historically holds above 50%
    for that trader on fear days; otherwise go neutral.
  • Trade frequency should stay LOW — fear days show worse avg PnL with
    higher activity, suggesting overtrading is penalised.

Strategy 2 — "Greed Momentum Rule"  
  During Greed/Extreme Greed days:
  • Frequent traders (top-50th percentile trades/day) show meaningfully
    higher win rates — increase position sizes by up to 20% but DO NOT
    raise leverage; let size do the work, not margin.
  • Long/Short ratio rises above 1.0 on greed days system-wide, confirming
    trend-following long bias is rewarded.
  • Low-leverage, frequent traders are the segment with the best
    risk-adjusted return on greed days — prioritise this regime.
""")

print("\nAll charts saved to charts/")
print("Run `streamlit run app.py` for the interactive dashboard.\n")
