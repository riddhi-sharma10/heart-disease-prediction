import streamlit as st
import requests
import pandas as pd
import plotly.graph_objects as go
import numpy as np

st.set_page_config(page_title="CardioScan · Prediction Analytics", layout="wide", page_icon="📈")

# ─────────────────────────────────────────────
# GLOBAL STYLES
# ─────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=DM+Serif+Display&family=DM+Sans:wght@300;400;500;600&display=swap');

html, body, [class*="css"] {
    font-family: 'DM Sans', sans-serif;
    background-color: #0D0F14;
    color: #E8EAF0;
}

[data-testid="stAppViewContainer"] {
    background: radial-gradient(ellipse 70% 40% at 50% -5%, rgba(251,191,36,0.09) 0%, #0D0F14 55%);
}

#MainMenu, footer, header { visibility: hidden; }

/* ── Hero ── */
.hero-badge {
    display: inline-block;
    background: rgba(251,191,36,0.10);
    border: 1px solid rgba(251,191,36,0.28);
    border-radius: 999px;
    padding: 4px 14px;
    font-size: 11px;
    font-weight: 600;
    letter-spacing: 0.12em;
    text-transform: uppercase;
    color: #FCD34D;
    margin-bottom: 14px;
}

.hero-title {
    font-family: 'DM Serif Display', serif;
    font-size: clamp(30px, 4vw, 54px);
    font-weight: 400;
    line-height: 1.1;
    letter-spacing: -0.02em;
    margin: 0 0 8px 0;
    color: #F1F5F9;
}
.hero-title span { color: #FCD34D; }

.hero-subtitle {
    font-size: 14px;
    color: #475569;
    font-weight: 300;
    margin: 0 0 36px 0;
}

/* ── Divider ── */
.fancy-divider {
    border: none;
    height: 1px;
    background: linear-gradient(90deg, transparent, rgba(255,255,255,0.07), transparent);
    margin: 36px 0;
}

/* ── KPI Cards ── */
.kpi-card {
    background: rgba(255,255,255,0.025);
    border: 1px solid rgba(255,255,255,0.06);
    border-radius: 16px;
    padding: 24px 22px 20px;
    position: relative;
    overflow: hidden;
}
.kpi-card::before {
    content: '';
    position: absolute;
    top: 0; left: 0; right: 0;
    height: 2px;
    border-radius: 16px 16px 0 0;
    background: var(--stripe);
}
.kpi-label {
    font-size: 11px;
    font-weight: 600;
    letter-spacing: 0.12em;
    text-transform: uppercase;
    color: #475569;
    margin-bottom: 10px;
}
.kpi-value {
    font-family: 'DM Serif Display', serif;
    font-size: 42px;
    font-weight: 400;
    line-height: 1;
    color: var(--val-color, #F1F5F9);
}
.kpi-suffix {
    font-size: 18px;
    color: #475569;
    font-family: 'DM Sans', sans-serif;
}
.kpi-sub { font-size: 12px; color: #334155; margin-top: 6px; }

/* ── Section labels ── */
.section-header {
    font-family: 'DM Serif Display', serif;
    font-size: 22px;
    color: #F1F5F9;
    margin: 0 0 2px 0;
}
.section-sub {
    font-size: 13px;
    color: #475569;
    margin-bottom: 20px;
}

/* ── Stat strip ── */
.stat-strip {
    display: flex; gap: 12px; flex-wrap: wrap; margin-bottom: 24px;
}
.stat-pill {
    background: rgba(255,255,255,0.03);
    border: 1px solid rgba(255,255,255,0.06);
    border-radius: 10px;
    padding: 10px 16px;
    display: flex; flex-direction: column; gap: 2px;
}
.stat-pill-label {
    font-size: 10px; font-weight: 600; letter-spacing: 0.1em;
    text-transform: uppercase; color: #334155;
}
.stat-pill-value {
    font-size: 15px; font-weight: 600; color: var(--pv, #94A3B8);
}

/* ── Empty state ── */
.empty-state {
    text-align: center; padding: 80px 40px;
    background: rgba(255,255,255,0.02);
    border: 1px solid rgba(255,255,255,0.05);
    border-radius: 20px;
}
.empty-state-icon { font-size: 48px; margin-bottom: 16px; }
.empty-state-title {
    font-family: 'DM Serif Display', serif;
    font-size: 24px; color: #334155; margin-bottom: 8px;
}
.empty-state-desc { font-size: 14px; color: #1E293B; }
</style>
""", unsafe_allow_html=True)

PLOT_CFG = dict(
    paper_bgcolor='rgba(0,0,0,0)',
    plot_bgcolor='rgba(0,0,0,0)',
    font=dict(family='DM Sans', color='#64748B'),
    margin=dict(t=24, b=24, l=10, r=10),
)
GRID = dict(gridcolor='rgba(255,255,255,0.05)', zerolinecolor='rgba(255,255,255,0.04)')

def risk_color(pct):
    if pct < 30:   return "#34D399"
    if pct < 60:   return "#FBBF24"
    return "#F87171"

def hex_to_rgba(hex_color, alpha=0.1):
    hex_color = hex_color.lstrip("#")
    r = int(hex_color[0:2], 16)
    g = int(hex_color[2:4], 16)
    b = int(hex_color[4:6], 16)
    return f"rgba({r}, {g}, {b}, {alpha})"

# ─────────────────────────────────────────────
# HERO
# ─────────────────────────────────────────────
st.markdown('<div class="hero-badge">Live Data</div>', unsafe_allow_html=True)
st.markdown('<h1 class="hero-title">Prediction <span>Analytics</span></h1>', unsafe_allow_html=True)
st.markdown('<p class="hero-subtitle">Aggregated risk scores and temporal trends across all patient predictions.</p>', unsafe_allow_html=True)


# ─────────────────────────────────────────────
# DATA FETCH
# ─────────────────────────────────────────────
try:
    response = requests.get("https://heart-disease-prediction-lrve.onrender.com/history", timeout=5)
    records  = response.json()
except Exception:
    st.markdown("""
    <div class="empty-state">
        <div class="empty-state-icon">⚡</div>
        <div class="empty-state-title">Backend Unreachable</div>
        <div class="empty-state-desc">Start the Flask server at <code>http://127.0.0.1:5000</code> and refresh.</div>
    </div>
    """, unsafe_allow_html=True)
    st.stop()

if len(records) == 0:
    st.markdown("""
    <div class="empty-state">
        <div class="empty-state-icon">🫀</div>
        <div class="empty-state-title">No predictions yet</div>
        <div class="empty-state-desc">Run your first cardiac risk prediction to populate this dashboard.</div>
    </div>
    """, unsafe_allow_html=True)
    st.stop()


# ─────────────────────────────────────────────
# PREPARE DATA
# ─────────────────────────────────────────────
df = pd.DataFrame(records)
df["risk_percent"] = df["probability"] * 100
df["timestamp"]    = pd.to_datetime(df["timestamp"])
df["risk_label"]   = df["risk_percent"].apply(
    lambda x: "Low" if x < 30 else ("Moderate" if x < 60 else "High")
)
df = df.sort_values("timestamp").reset_index(drop=True)

total    = len(df)
avg_risk = df["risk_percent"].mean()
high_n   = len(df[df["risk_percent"] > 60])
low_n    = len(df[df["risk_percent"] < 30])
peak     = df["risk_percent"].max()
recent   = df["risk_percent"].iloc[-1]


# ─────────────────────────────────────────────
# KPI CARDS
# ─────────────────────────────────────────────
k1, k2, k3, k4 = st.columns(4, gap="medium")

cards = [
    (k1, "Total Predictions", total,       "",   "#60A5FA",  "All-time records"),
    (k2, "Avg. Risk Score",   f"{avg_risk:.1f}", "%", risk_color(avg_risk), "Population mean"),
    (k3, "High Risk Cases",   high_n,      "",   "#F87171",  f"{high_n/total*100:.0f}% of total"),
    (k4, "Latest Prediction", f"{recent:.1f}", "%", risk_color(recent), "Most recent score"),
]

for col, label, val, suffix, color, sub in cards:
    col.markdown(f"""
    <div class="kpi-card" style="--stripe:{color}; --val-color:{color};">
        <div class="kpi-label">{label}</div>
        <div class="kpi-value">{val}<span class="kpi-suffix">{suffix}</span></div>
        <div class="kpi-sub">{sub}</div>
    </div>
    """, unsafe_allow_html=True)

st.markdown('<hr class="fancy-divider"/>', unsafe_allow_html=True)


# ─────────────────────────────────────────────
# DISTRIBUTION + TIMELINE
# ─────────────────────────────────────────────
dist_col, time_col = st.columns([1, 2], gap="large")

with dist_col:
    st.markdown('<p class="section-header">Risk Distribution</p>', unsafe_allow_html=True)
    st.markdown('<p class="section-sub">Histogram of all recorded risk scores.</p>', unsafe_allow_html=True)

    bins     = np.linspace(0, 100, 12)
    counts, edges = np.histogram(df["risk_percent"], bins=bins)
    centers  = (edges[:-1] + edges[1:]) / 2
    colors   = [risk_color(c) for c in centers]

    fig_hist = go.Figure()
    for i, (count, center, color) in enumerate(zip(counts, centers, colors)):
        fig_hist.add_trace(go.Bar(
            x=[center], y=[count],
            width=[(edges[i+1] - edges[i]) * 0.85],
            marker=dict(color=color, opacity=0.75, line=dict(color='rgba(0,0,0,0)')),
            hovertemplate=f"<b>{edges[i]:.0f}–{edges[i+1]:.0f}%</b><br>{count} predictions<extra></extra>",
            showlegend=False,
        ))

    # Zone annotations
    for x0, x1, label, c in [(0,30,"Low","#34D399"), (30,60,"Moderate","#FBBF24"), (60,100,"High","#F87171")]:
        fig_hist.add_vrect(x0=x0, x1=x1, fillcolor=c, opacity=0.04, line_width=0)
        fig_hist.add_annotation(x=(x0+x1)/2, y=counts.max()*1.08, text=label,
                                showarrow=False, font=dict(size=10, color=c, family='DM Sans'))

    fig_hist.update_layout(
        **PLOT_CFG, height=310, bargap=0.04,
        xaxis=dict(**GRID, ticksuffix="%", range=[0,100], tickfont=dict(size=11)),
        yaxis=dict(**GRID, title="Patients", tickfont=dict(size=11)),
    )
    st.plotly_chart(fig_hist, use_container_width=True)

with time_col:
    st.markdown('<p class="section-header">Risk Score Over Time</p>', unsafe_allow_html=True)
    st.markdown('<p class="section-sub">Individual prediction scores and rolling average trend.</p>', unsafe_allow_html=True)

    rolling = df["risk_percent"].rolling(window=max(1, total//5), min_periods=1).mean()

    fig_time = go.Figure()

    # Risk zone bands
    for y0, y1, c in [(0,30,"#34D399"), (30,60,"#FBBF24"), (60,100,"#F87171")]:
        fig_time.add_hrect(y0=y0, y1=y1, fillcolor=c, opacity=0.04, line_width=0)

    # Threshold dashes
    for val, c, lbl in [(30,"#34D399","Low / Moderate"), (60,"#F87171","Moderate / High")]:
        fig_time.add_hline(y=val, line_dash="dot", line_color=c, line_width=1,
                           opacity=0.4, annotation_text=lbl,
                           annotation_font=dict(color=c, size=10),
                           annotation_position="right")

    # Scatter points colored by risk
    for label, color in [("Low","#34D399"), ("Moderate","#FBBF24"), ("High","#F87171")]:
        mask = df["risk_label"] == label
        fig_time.add_trace(go.Scatter(
            x=df.loc[mask, "timestamp"],
            y=df.loc[mask, "risk_percent"],
            mode="markers",
            name=label,
            marker=dict(color=color, size=8, opacity=0.85,
                        line=dict(color='#0D0F14', width=1.5)),
            hovertemplate="<b>" + label + " Risk</b><br>%{x|%b %d, %H:%M}<br>%{y:.1f}%<extra></extra>",
        ))

    # Rolling mean line
    fig_time.add_trace(go.Scatter(
        x=df["timestamp"], y=rolling,
        mode="lines", name="Rolling avg",
        line=dict(color='rgba(255,255,255,0.2)', width=2, dash='solid'),
        hoverinfo='skip', showlegend=True,
    ))

    fig_time.update_layout(
        **PLOT_CFG, height=310,
        xaxis=dict(**GRID, tickfont=dict(size=11)),
        yaxis=dict(**GRID, ticksuffix="%", range=[0,105], tickfont=dict(size=11)),
        legend=dict(orientation="h", y=-0.18, x=0.5, xanchor='center',
                    bgcolor='rgba(0,0,0,0)', font=dict(size=12, color='#94A3B8')),
        hovermode="x unified",
    )
    st.plotly_chart(fig_time, use_container_width=True)

st.markdown('<hr class="fancy-divider"/>', unsafe_allow_html=True)


# ─────────────────────────────────────────────
# PERCENTILE STRIP + BOX PLOT
# ─────────────────────────────────────────────
pct_col, box_col = st.columns([1, 2], gap="large")

with pct_col:
    st.markdown('<p class="section-header">Score Breakdown</p>', unsafe_allow_html=True)
    st.markdown('<p class="section-sub">Key percentile statistics.</p>', unsafe_allow_html=True)

    stats = [
        ("Minimum",   df["risk_percent"].min(),                  "#60A5FA"),
        ("25th pct",  df["risk_percent"].quantile(0.25),         "#94A3B8"),
        ("Median",    df["risk_percent"].median(),                "#FCD34D"),
        ("75th pct",  df["risk_percent"].quantile(0.75),         "#94A3B8"),
        ("Maximum",   peak,                                       "#F87171"),
        ("Std Dev",   df["risk_percent"].std(),                  "#A78BFA"),
    ]

    for label, val, color in stats:
        st.markdown(f"""
        <div style="display:flex; justify-content:space-between; align-items:center;
                    padding: 10px 16px; margin-bottom:8px;
                    background:rgba(255,255,255,0.025);
                    border:1px solid rgba(255,255,255,0.06);
                    border-radius:10px;">
            <span style="font-size:12px; color:#475569; font-weight:500;">{label}</span>
            <span style="font-size:15px; font-weight:600; color:{color};">{val:.1f}%</span>
        </div>
        """, unsafe_allow_html=True)

with box_col:
    st.markdown('<p class="section-header">Risk by Category</p>', unsafe_allow_html=True)
    st.markdown('<p class="section-sub">Score spread within each risk classification.</p>', unsafe_allow_html=True)

    fig_box = go.Figure()

    for label, color in [("Low","#34D399"), ("Moderate","#FBBF24"), ("High","#F87171")]:
        sub = df[df["risk_label"] == label]["risk_percent"]
        if len(sub) == 0:
            continue

        fig_box.add_trace(go.Box(
            y=sub,
            name=label,
            marker=dict(
                color=color,
                size=5,
                line=dict(color='#0D0F14', width=1)
            ),
            line=dict(color=color),
            fillcolor=hex_to_rgba(color, 0.10),   # ✅ FIXED
            boxmean='sd',
            hovertemplate="<b>" + label + "</b><br>%{y:.1f}%<extra></extra>",
        ))

    fig_box.update_layout(
        **PLOT_CFG,
        height=310,
        showlegend=False,
        xaxis=dict(**GRID, tickfont=dict(size=12, color='#94A3B8')),
        yaxis=dict(**GRID, ticksuffix="%", range=[0,105], tickfont=dict(size=11)),
    )

    st.plotly_chart(fig_box, use_container_width=True)
