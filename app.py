"""
app.py — Streamlit Dashboard
Trader Performance vs Market Sentiment (Hyperliquid × Fear/Greed Index)
Run: streamlit run app.py
"""

import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import sys, os
sys.path.insert(0, os.path.dirname(__file__))

from src.analysis import load_all

# ─── page config ──────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Trader Sentiment Dashboard",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ─── colour palette ──────────────────────────────────────────────────────────
PALETTE = {"Fear": "#ef5350", "Neutral": "#ffa726", "Greed": "#66bb6a"}

# ─── cached data load ────────────────────────────────────────────────────────
@st.cache_data(show_spinner="Loading & processing datasets …")
def get_data():
    return load_all()

d = get_data()
fg          = d["fg"]
merged      = d["merged"]
daily       = d["daily"]
t_stats     = d["trader_stats"]
summary     = d["sentiment_summary"]
seg_cross   = d["segment_cross"]


# ════════════════════════════════════════════════════════════════════════════════
# SIDEBAR
# ════════════════════════════════════════════════════════════════════════════════
with st.sidebar:
    st.title("🎛️ Filters")
    st.markdown("---")

    sentiment_options = ["All", "Fear", "Neutral", "Greed"]
    selected_sentiment = st.selectbox("Sentiment Regime", sentiment_options)

    date_min = daily["date"].min().date()
    date_max = daily["date"].max().date()
    date_range = st.date_input("Date Range", value=(date_min, date_max),
                               min_value=date_min, max_value=date_max)

    top_n_traders = st.slider("Top-N Traders (PnL leaderboard)", 5, 50, 20)

    st.markdown("---")
    st.markdown("**Dataset Stats**")
    st.metric("Total Trades", f"{len(merged):,}")
    st.metric("Unique Traders", f"{merged['Account'].nunique():,}")
    st.metric("Days Covered", f"{merged['date'].nunique()}")
    st.markdown("---")
    st.caption("Primetrade.ai — DS Intern Assignment")


# ─── filter daily by sidebar ─────────────────────────────────────────────────
def apply_filters(df):
    d0, d1 = pd.Timestamp(date_range[0]), pd.Timestamp(date_range[1])
    mask = (df["date"] >= d0) & (df["date"] <= d1)
    if selected_sentiment != "All":
        mask &= df["sentiment_bucket"] == selected_sentiment
    return df[mask]

daily_f = apply_filters(daily)
merged_f = merged.copy()
d0, d1 = pd.Timestamp(date_range[0]), pd.Timestamp(date_range[1])
merged_f = merged_f[(merged_f["date"] >= d0) & (merged_f["date"] <= d1)]
if selected_sentiment != "All":
    merged_f = merged_f[merged_f["sentiment_bucket"] == selected_sentiment]


# ════════════════════════════════════════════════════════════════════════════════
# HEADER
# ════════════════════════════════════════════════════════════════════════════════
st.title("📊 Trader Performance vs Market Sentiment")
st.caption("Hyperliquid historical trades × Bitcoin Fear/Greed Index")

# ─── KPI row ─────────────────────────────────────────────────────────────────
kpi1, kpi2, kpi3, kpi4, kpi5 = st.columns(5)
kpi1.metric("Avg Daily PnL", f"${daily_f['total_pnl'].mean():,.0f}")
kpi2.metric("Avg Win Rate", f"{daily_f['win_rate'].mean()*100:.1f}%")
kpi3.metric("Avg Trades/Day", f"{daily_f['trade_count'].mean():.0f}")
kpi4.metric("Avg Leverage", f"{daily_f['avg_leverage'].mean():.1f}x")
kpi5.metric("Avg L/S Ratio", f"{daily_f['long_short_ratio'].mean():.2f}")

st.markdown("---")


# ════════════════════════════════════════════════════════════════════════════════
# TAB LAYOUT
# ════════════════════════════════════════════════════════════════════════════════
tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "📈 Sentiment Overview",
    "🔍 Behavior Analysis",
    "👥 Trader Segments",
    "🌡️ Heatmaps",
    "🏆 Leaderboard & Strategy"
])


# ════════════════════════════════════════════════════════════════════════════════
# TAB 1 — SENTIMENT OVERVIEW
# ════════════════════════════════════════════════════════════════════════════════
with tab1:
    st.subheader("Performance by Sentiment Regime")

    order = ["Fear", "Neutral", "Greed"]
    sum_f = summary[summary["sentiment_bucket"].isin(order)].set_index("sentiment_bucket")

    col1, col2 = st.columns(2)

    with col1:
        fig = px.bar(
            sum_f.loc[order].reset_index(),
            x="sentiment_bucket", y="avg_daily_pnl",
            color="sentiment_bucket",
            color_discrete_map=PALETTE,
            text="avg_daily_pnl",
            title="Avg Daily PnL by Sentiment",
            labels={"sentiment_bucket": "Sentiment", "avg_daily_pnl": "USD"}
        )
        fig.update_traces(texttemplate="$%{text:.0f}", textposition="outside")
        fig.update_layout(showlegend=False, height=380)
        st.plotly_chart(fig, use_container_width=True)

    with col2:
        fig = px.bar(
            sum_f.loc[order].reset_index(),
            x="sentiment_bucket", y="avg_win_rate",
            color="sentiment_bucket",
            color_discrete_map=PALETTE,
            text="avg_win_rate",
            title="Avg Win Rate by Sentiment",
            labels={"sentiment_bucket": "Sentiment", "avg_win_rate": "Win Rate"}
        )
        fig.update_traces(texttemplate="%{text:.1%}", textposition="outside")
        fig.update_layout(showlegend=False, height=380, yaxis_tickformat=".0%")
        st.plotly_chart(fig, use_container_width=True)

    st.subheader("Daily PnL Time Series")
    daily_sorted = daily.sort_values("date")
    fig = go.Figure()

    # shade by sentiment
    for bucket, color in PALETTE.items():
        mask = daily_sorted["sentiment_bucket"] == bucket
        sub = daily_sorted[mask]
        fig.add_trace(go.Scatter(
            x=sub["date"], y=sub["total_pnl"].rolling(7, min_periods=1).mean(),
            mode="lines", line=dict(width=0),
            fill="tozeroy", fillcolor=color.replace(")", ",0.18)").replace("rgb", "rgba") if color.startswith("rgb") else color + "30",
            name=bucket, showlegend=True,
        ))

    fig.add_trace(go.Scatter(
        x=daily_sorted["date"],
        y=daily_sorted["total_pnl"].rolling(7, min_periods=1).mean(),
        mode="lines", line=dict(color="#1565C0", width=2),
        name="7-day rolling PnL"
    ))
    fig.add_hline(y=0, line_dash="dash", line_color="gray")
    fig.update_layout(height=380, xaxis_title="Date", yaxis_title="USD",
                      legend=dict(orientation="h", y=1.05))
    st.plotly_chart(fig, use_container_width=True)

    st.subheader("Sentiment Distribution in Dataset")
    dist = fg["classification"].value_counts().reset_index()
    dist.columns = ["classification", "count"]
    fig = px.pie(dist, names="classification", values="count",
                 color_discrete_sequence=px.colors.sequential.RdYlGn,
                 title="Fear/Greed Classification Distribution")
    fig.update_layout(height=360)
    st.plotly_chart(fig, use_container_width=True)


# ════════════════════════════════════════════════════════════════════════════════
# TAB 2 — BEHAVIOR ANALYSIS
# ════════════════════════════════════════════════════════════════════════════════
with tab2:
    st.subheader("How Traders Behave Under Different Sentiment Regimes")

    order = ["Fear", "Neutral", "Greed"]
    sum_o = summary[summary["sentiment_bucket"].isin(order)].set_index("sentiment_bucket")

    col1, col2 = st.columns(2)

    with col1:
        fig = px.bar(sum_o.loc[order].reset_index(),
                     x="sentiment_bucket", y="avg_trades",
                     color="sentiment_bucket", color_discrete_map=PALETTE,
                     text="avg_trades",
                     title="Avg Trades per Day",
                     labels={"avg_trades": "Trades/Day", "sentiment_bucket": "Sentiment"})
        fig.update_traces(texttemplate="%{text:.0f}", textposition="outside")
        fig.update_layout(showlegend=False, height=360)
        st.plotly_chart(fig, use_container_width=True)

    with col2:
        fig = px.bar(sum_o.loc[order].reset_index(),
                     x="sentiment_bucket", y="avg_leverage",
                     color="sentiment_bucket", color_discrete_map=PALETTE,
                     text="avg_leverage",
                     title="Median Leverage Proxy",
                     labels={"avg_leverage": "Leverage", "sentiment_bucket": "Sentiment"})
        fig.update_traces(texttemplate="%{text:.1f}x", textposition="outside")
        fig.update_layout(showlegend=False, height=360)
        st.plotly_chart(fig, use_container_width=True)

    col3, col4 = st.columns(2)

    with col3:
        fig = px.bar(sum_o.loc[order].reset_index(),
                     x="sentiment_bucket", y="avg_long_short_ratio",
                     color="sentiment_bucket", color_discrete_map=PALETTE,
                     text="avg_long_short_ratio",
                     title="Long/Short Ratio",
                     labels={"avg_long_short_ratio": "L/S Ratio", "sentiment_bucket": "Sentiment"})
        fig.update_traces(texttemplate="%{text:.2f}", textposition="outside")
        fig.add_hline(y=1.0, line_dash="dash", line_color="gray", annotation_text="balanced")
        fig.update_layout(showlegend=False, height=360)
        st.plotly_chart(fig, use_container_width=True)

    with col4:
        fig = px.bar(sum_o.loc[order].reset_index(),
                     x="sentiment_bucket", y="avg_size_usd",
                     color="sentiment_bucket", color_discrete_map=PALETTE,
                     text="avg_size_usd",
                     title="Avg Trade Size (USD)",
                     labels={"avg_size_usd": "USD", "sentiment_bucket": "Sentiment"})
        fig.update_traces(texttemplate="$%{text:,.0f}", textposition="outside")
        fig.update_layout(showlegend=False, height=360)
        st.plotly_chart(fig, use_container_width=True)

    st.subheader("PnL Distribution by Sentiment (Box)")
    fig = px.box(daily_f, x="sentiment_bucket", y="total_pnl",
                 color="sentiment_bucket", color_discrete_map=PALETTE,
                 title="Daily PnL Distribution",
                 labels={"sentiment_bucket": "Sentiment", "total_pnl": "Daily PnL (USD)"},
                 category_orders={"sentiment_bucket": ["Fear", "Neutral", "Greed"]})
    fig.add_hline(y=0, line_dash="dash", line_color="gray")
    fig.update_layout(showlegend=False, height=400)
    st.plotly_chart(fig, use_container_width=True)


# ════════════════════════════════════════════════════════════════════════════════
# TAB 3 — TRADER SEGMENTS
# ════════════════════════════════════════════════════════════════════════════════
with tab3:
    st.subheader("Trader Segmentation")

    col1, col2 = st.columns(2)

    with col1:
        st.markdown("**Leverage Tiers**")
        lev_sum = t_stats.groupby("leverage_tier", observed=True).agg(
            Traders=("Account", "count"),
            Avg_PnL=("total_pnl", "mean"),
            Win_Rate=("win_rate", "mean"),
            Avg_Leverage=("avg_leverage", "mean"),
        ).reset_index()
        lev_sum.columns = ["Leverage Tier", "Traders", "Avg PnL ($)", "Win Rate", "Avg Leverage"]
        lev_sum["Avg PnL ($)"] = lev_sum["Avg PnL ($)"].map("${:,.0f}".format)
        lev_sum["Win Rate"] = lev_sum["Win Rate"].map("{:.1%}".format)
        lev_sum["Avg Leverage"] = lev_sum["Avg Leverage"].map("{:.1f}x".format)
        st.dataframe(lev_sum, use_container_width=True, hide_index=True)

    with col2:
        st.markdown("**Consistency Tiers**")
        con_sum = t_stats.groupby("consistency_tier").agg(
            Traders=("Account", "count"),
            Avg_PnL=("total_pnl", "mean"),
            Win_Rate=("win_rate", "mean"),
        ).reset_index().sort_values("Avg_PnL", ascending=False)
        con_sum.columns = ["Consistency", "Traders", "Avg PnL ($)", "Win Rate"]
        con_sum["Avg PnL ($)"] = con_sum["Avg PnL ($)"].map("${:,.0f}".format)
        con_sum["Win Rate"] = con_sum["Win Rate"].map("{:.1%}".format)
        st.dataframe(con_sum, use_container_width=True, hide_index=True)

    st.markdown("---")
    st.subheader("Leverage vs Total PnL Scatter")

    fig = px.scatter(
        t_stats[t_stats["leverage_tier"].notna()],
        x="avg_leverage", y="total_pnl",
        color="leverage_tier",
        color_discrete_map={
            "Low Leverage": "#66bb6a",
            "Mid Leverage": "#ffa726",
            "High Leverage": "#ef5350"
        },
        hover_data={"Account": False, "win_rate": ":.2f", "trade_count": True},
        title="Leverage vs Total PnL per Trader",
        labels={"avg_leverage": "Avg Leverage (proxy)", "total_pnl": "Total PnL (USD)"},
        opacity=0.55,
        size_max=12,
    )
    fig.add_hline(y=0, line_dash="dash", line_color="gray")
    fig.update_layout(height=430)
    st.plotly_chart(fig, use_container_width=True)

    st.subheader("Trade Frequency vs Win Rate")
    fig = px.scatter(
        t_stats[t_stats["frequency_tier"].notna()],
        x="trades_per_day", y="win_rate",
        color="frequency_tier",
        color_discrete_map={"Infrequent": "#42a5f5", "Frequent": "#ab47bc"},
        title="Trades per Day vs Win Rate",
        labels={"trades_per_day": "Avg Trades/Day", "win_rate": "Win Rate"},
        opacity=0.55,
    )
    fig.update_layout(height=400, yaxis_tickformat=".0%")
    st.plotly_chart(fig, use_container_width=True)


# ════════════════════════════════════════════════════════════════════════════════
# TAB 4 — HEATMAPS
# ════════════════════════════════════════════════════════════════════════════════
with tab4:
    st.subheader("Cross-Segment × Sentiment Heatmaps")

    col1, col2 = st.columns(2)

    with col1:
        pivot_pnl = seg_cross.pivot(index="leverage_tier", columns="sentiment_bucket", values="avg_pnl")
        cols_order = [c for c in ["Fear", "Neutral", "Greed"] if c in pivot_pnl.columns]
        pivot_pnl = pivot_pnl[cols_order]

        fig = px.imshow(pivot_pnl,
                        text_auto=".0f",
                        color_continuous_scale="RdYlGn",
                        title="Avg PnL: Leverage Tier × Sentiment",
                        labels={"color": "Avg PnL ($)"})
        fig.update_layout(height=380)
        st.plotly_chart(fig, use_container_width=True)

    with col2:
        pivot_wr = seg_cross.pivot(index="leverage_tier", columns="sentiment_bucket", values="win_rate")
        pivot_wr = pivot_wr[[c for c in ["Fear", "Neutral", "Greed"] if c in pivot_wr.columns]]

        fig = px.imshow(pivot_wr,
                        text_auto=".2f",
                        color_continuous_scale="RdYlGn",
                        title="Win Rate: Leverage Tier × Sentiment",
                        labels={"color": "Win Rate"})
        fig.update_layout(height=380)
        st.plotly_chart(fig, use_container_width=True)

    st.subheader("Avg Trade Count: Leverage Tier × Sentiment")
    pivot_tc = seg_cross.pivot(index="leverage_tier", columns="sentiment_bucket", values="trade_count")
    pivot_tc = pivot_tc[[c for c in ["Fear", "Neutral", "Greed"] if c in pivot_tc.columns]]
    fig = px.imshow(pivot_tc, text_auto=".0f", color_continuous_scale="Blues",
                    title="Total Trade Count",
                    labels={"color": "Trades"})
    fig.update_layout(height=340)
    st.plotly_chart(fig, use_container_width=True)


# ════════════════════════════════════════════════════════════════════════════════
# TAB 5 — LEADERBOARD & STRATEGY
# ════════════════════════════════════════════════════════════════════════════════
with tab5:
    st.subheader(f"🏆 Top {top_n_traders} Traders by Total PnL")

    leaderboard = t_stats.nlargest(top_n_traders, "total_pnl")[
        ["Account", "total_pnl", "win_rate", "trade_count", "avg_leverage",
         "trades_per_day", "consistency_tier", "leverage_tier"]
    ].copy()
    leaderboard["Account"] = leaderboard["Account"].str[:10] + "…"
    leaderboard.columns = ["Account", "Total PnL ($)", "Win Rate", "Trades",
                           "Avg Lev", "Trades/Day", "Consistency", "Lev Tier"]
    leaderboard["Total PnL ($)"] = leaderboard["Total PnL ($)"].map("${:,.0f}".format)
    leaderboard["Win Rate"] = leaderboard["Win Rate"].map("{:.1%}".format)
    leaderboard["Avg Lev"] = leaderboard["Avg Lev"].map("{:.1f}x".format)
    leaderboard["Trades/Day"] = leaderboard["Trades/Day"].map("{:.1f}".format)
    st.dataframe(leaderboard, use_container_width=True, hide_index=True)

    st.markdown("---")
    st.subheader("💡 Strategy Recommendations")

    with st.expander("📌 Strategy 1 — Fear Pullback Rule", expanded=True):
        st.markdown("""
        **Context:** On Fear/Extreme Fear days, aggregate PnL drops and high-leverage traders
        are disproportionately hurt.

        **Rules:**
        - **High-leverage traders**: Reduce leverage by ≥ 30% on Fear days. Data shows their
          avg PnL deteriorates most severely.
        - **Trade less, not more**: Fear days that see elevated trade counts show *lower*
          avg PnL — overtrading in choppy conditions destroys value.
        - **Long bias cautiously**: Long/Short ratio naturally rises on Fear days as traders
          try to catch dips, but win rates don't support this — remain neutral or short-biased.

        **Target segment:** High-leverage traders and Inconsistent Winners.
        """)

    with st.expander("📌 Strategy 2 — Greed Momentum Rule", expanded=True):
        st.markdown("""
        **Context:** Greed days show the highest avg PnL, best win rates, and a naturally
        long-biased market. Low-leverage frequent traders capture this best.

        **Rules:**
        - **Increase position size** (not leverage) by up to 20% on confirmed Greed days
          — let size do the work, not margin.
        - **Lean long**: L/S ratio above 1.0 on greed days is validated by higher win rates
          for long positions. Follow the trend.
        - **Frequent traders**: This is the segment that benefits most from Greed regimes —
          maintain or slightly increase trade frequency.

        **Target segment:** Low-leverage, frequent, consistent-winner traders.
        """)

    with st.expander("📌 Strategy 3 — Neutral Days = Reduce Exposure", expanded=True):
        st.markdown("""
        **Context:** Neutral sentiment days have the *lowest* average win rates and unpredictable
        PnL distributions — neither fear-driven dip-buying nor greed-driven momentum works well.

        **Rules:**
        - Reduce trade size by 15–25% on neutral days.
        - Avoid opening large new positions; prefer closing existing ones.
        - Use neutral days for portfolio rebalancing rather than active speculation.

        **Target segment:** All segments; most impactful for Inconsistent Winners.
        """)

    st.markdown("---")
    st.subheader("Key Insights Summary")
    st.info("""
    **Insight 1 — Greed days outperform on every metric**: avg PnL is highest, win rate is highest,
    and long/short ratio naturally aligns with trend momentum.

    **Insight 2 — High leverage amplifies losses on Fear days more than it amplifies gains on Greed days**:
    the leverage-tier heatmap consistently shows High Leverage traders suffering the worst on Fear days,
    while Low Leverage traders show more stable returns across regimes.

    **Insight 3 — Overtrading on Fear days is penalised**: days with above-median trade counts during
    Fear regimes have lower average PnL than quieter Fear days — restraint is rewarded.
    """)
