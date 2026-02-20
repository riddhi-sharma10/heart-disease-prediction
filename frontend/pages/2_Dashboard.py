import streamlit as st
import requests
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

st.set_page_config(page_title="CardioScan · Analytics", layout="wide", page_icon="📊")

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=DM+Serif+Display&family=DM+Sans:wght@300;400;500;600&display=swap');
html, body, [class*="css"] { font-family:'DM Sans',sans-serif; background-color:#0D0F14; color:#E8EAF0; }
[data-testid="stAppViewContainer"] { background:radial-gradient(ellipse 70% 40% at 50% -5%,rgba(220,38,38,0.12) 0%,#0D0F14 55%); }
#MainMenu, footer, header { visibility:hidden; }
.hero-badge { display:inline-block; background:rgba(220,38,38,0.12); border:1px solid rgba(220,38,38,0.35); border-radius:999px; padding:4px 14px; font-size:11px; font-weight:600; letter-spacing:0.12em; text-transform:uppercase; color:#F87171; margin-bottom:14px; }
.hero-title { font-family:'DM Serif Display',serif; font-size:clamp(30px,4vw,54px); font-weight:400; line-height:1.1; letter-spacing:-0.02em; margin:0 0 8px 0; color:#F1F5F9; }
.hero-title span { color:#F87171; }
.hero-subtitle { font-size:14px; color:#475569; font-weight:300; margin:0 0 36px 0; }
.fancy-divider { border:none; height:1px; background:linear-gradient(90deg,transparent,rgba(255,255,255,0.07),transparent); margin:36px 0; }
.kpi-card { background:rgba(255,255,255,0.03); border:1px solid rgba(255,255,255,0.06); border-radius:16px; padding:24px 22px 20px; position:relative; overflow:hidden; }
.kpi-card::before { content:''; position:absolute; top:0; left:0; right:0; height:2px; border-radius:16px 16px 0 0; }
.kpi-card.total::before { background:linear-gradient(90deg,#60A5FA,#3B82F6); }
.kpi-card.high::before  { background:linear-gradient(90deg,#F87171,#DC2626); }
.kpi-card.mod::before   { background:linear-gradient(90deg,#FBBF24,#D97706); }
.kpi-card.low::before   { background:linear-gradient(90deg,#34D399,#059669); }
.kpi-label { font-size:11px; font-weight:600; letter-spacing:0.12em; text-transform:uppercase; color:#475569; margin-bottom:10px; }
.kpi-value { font-family:'DM Serif Display',serif; font-size:44px; font-weight:400; line-height:1; color:#F1F5F9; }
.kpi-sub { font-size:12px; color:#334155; margin-top:6px; }
.section-header { font-family:'DM Serif Display',serif; font-size:22px; color:#F1F5F9; margin:0 0 2px 0; }
.section-sub { font-size:13px; color:#475569; margin-bottom:20px; }
.empty-state { text-align:center; padding:80px 40px; background:rgba(255,255,255,0.02); border:1px solid rgba(255,255,255,0.05); border-radius:20px; }
.empty-icon { font-size:48px; margin-bottom:16px; }
.empty-title { font-family:'DM Serif Display',serif; font-size:24px; color:#334155; margin-bottom:8px; }
.empty-desc { font-size:14px; color:#1E293B; }
</style>
""", unsafe_allow_html=True)

PLOT_CONFIG = dict(paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
                   font=dict(family='DM Sans',color='#64748B'), margin=dict(t=20,b=20,l=10,r=10))
GRID_STYLE  = dict(gridcolor='rgba(255,255,255,0.05)', zerolinecolor='rgba(255,255,255,0.05)')


# ─────────────────────────────────────────────
# CACHED DATA FETCH
# ttl=30 → Streamlit reuses the result for 30 s instead of hitting
# the Flask API on every widget interaction.  The "Refresh" button
# below calls st.cache_data.clear() to force an immediate reload.
# ─────────────────────────────────────────────
@st.cache_data(ttl=30, show_spinner=False)
def fetch_history():
    resp = requests.get("http://127.0.0.1:5000/history", timeout=5)
    return resp.json()


# ── Hero ───────────────────────────────────────────────────────
st.markdown('<div class="hero-badge">Live Analytics</div>', unsafe_allow_html=True)
st.markdown('<h1 class="hero-title">Cardiac Risk <span>Analytics</span></h1>', unsafe_allow_html=True)
st.markdown('<p class="hero-subtitle">Real-time overview of all prediction results and patient risk trends.</p>',
            unsafe_allow_html=True)

# Refresh button so user can pull latest without navigating away
if st.button("↻  Refresh data", type="secondary"):
    st.cache_data.clear()
    st.rerun()


# ── Data Fetch ─────────────────────────────────────────────────
try:
    data = fetch_history()
except Exception:
    data = []
    st.error("⚠  Backend unreachable. Start Flask at http://127.0.0.1:5000")

if not data:
    st.markdown("""
    <div class="empty-state">
        <div class="empty-icon">🫀</div>
        <div class="empty-title">No predictions yet</div>
        <div class="empty-desc">Run your first cardiac risk prediction to see analytics populate here.</div>
    </div>""", unsafe_allow_html=True)
    st.stop()


# ── Prepare DataFrame ──────────────────────────────────────────
df = pd.DataFrame(data)
df["risk_category"] = df["probability"].apply(
    lambda x: "Low" if x < 0.3 else ("Moderate" if x < 0.6 else "High")
)
df["timestamp"] = pd.to_datetime(df["timestamp"])
df = df.sort_values("timestamp")

total    = len(df)
high     = len(df[df["risk_category"] == "High"])
moderate = len(df[df["risk_category"] == "Moderate"])
low      = len(df[df["risk_category"] == "Low"])
avg_risk = df["probability"].mean()


# ── KPI Cards ──────────────────────────────────────────────────
k1, k2, k3, k4, k5 = st.columns(5, gap="medium")

with k1:
    st.markdown(f"""<div class="kpi-card total"><div class="kpi-label">Total Predictions</div>
    <div class="kpi-value">{total}</div><div class="kpi-sub">All-time records</div></div>""",
    unsafe_allow_html=True)
with k2:
    st.markdown(f"""<div class="kpi-card high"><div class="kpi-label">High Risk</div>
    <div class="kpi-value" style="color:#F87171;">{high}</div>
    <div class="kpi-sub">{high/total*100:.0f}% of total</div></div>""", unsafe_allow_html=True)
with k3:
    st.markdown(f"""<div class="kpi-card mod"><div class="kpi-label">Moderate Risk</div>
    <div class="kpi-value" style="color:#FBBF24;">{moderate}</div>
    <div class="kpi-sub">{moderate/total*100:.0f}% of total</div></div>""", unsafe_allow_html=True)
with k4:
    st.markdown(f"""<div class="kpi-card low"><div class="kpi-label">Low Risk</div>
    <div class="kpi-value" style="color:#34D399;">{low}</div>
    <div class="kpi-sub">{low/total*100:.0f}% of total</div></div>""", unsafe_allow_html=True)
with k5:
    avg_color = "#F87171" if avg_risk >= 0.6 else ("#FBBF24" if avg_risk >= 0.3 else "#34D399")
    st.markdown(f"""<div class="kpi-card total"><div class="kpi-label">Avg. Risk Score</div>
    <div class="kpi-value" style="color:{avg_color};">{avg_risk*100:.0f}<span style="font-size:22px;">%</span></div>
    <div class="kpi-sub">Population mean</div></div>""", unsafe_allow_html=True)

st.markdown('<hr class="fancy-divider"/>', unsafe_allow_html=True)


# ── Chart Row 1: Pie + Timeline ────────────────────────────────
c1, c2 = st.columns([1, 2], gap="large")

with c1:
    st.markdown('<p class="section-header">Risk Distribution</p>', unsafe_allow_html=True)
    st.markdown('<p class="section-sub">Breakdown of prediction outcomes.</p>', unsafe_allow_html=True)

    risk_counts = df["risk_category"].value_counts().reset_index()
    risk_counts.columns = ["category", "count"]

    fig_pie = go.Figure(go.Pie(
        labels=risk_counts["category"], values=risk_counts["count"], hole=0.6,
        marker=dict(colors=["#34D399","#FBBF24","#F87171"],
                    line=dict(color='#0D0F14',width=3)),
        textfont=dict(family='DM Sans',size=13,color='#E8EAF0'),
        hovertemplate="<b>%{label}</b><br>Count: %{value}<br>Share: %{percent}<extra></extra>",
    ))
    fig_pie.update_layout(**PLOT_CONFIG, height=300, showlegend=True,
        legend=dict(orientation="v",x=1.0,y=0.5,font=dict(size=12,color='#94A3B8'),bgcolor='rgba(0,0,0,0)'),
        annotations=[dict(text=f"<b>{total}</b><br><span style='font-size:10px'>total</span>",
                          x=0.5,y=0.5,font=dict(size=18,color='#F1F5F9',family='DM Serif Display'),showarrow=False)])
    st.plotly_chart(fig_pie, use_container_width=True)

with c2:
    st.markdown('<p class="section-header">Risk Probability Over Time</p>', unsafe_allow_html=True)
    st.markdown('<p class="section-sub">Trend of individual prediction scores.</p>', unsafe_allow_html=True)

    color_map = {"Low":"#34D399","Moderate":"#FBBF24","High":"#F87171"}
    fig_line  = go.Figure()

    fig_line.add_hrect(y0=0,   y1=0.3,  fillcolor="rgba(52,211,153,0.05)",  line_width=0)
    fig_line.add_hrect(y0=0.3, y1=0.6,  fillcolor="rgba(251,191,36,0.05)",  line_width=0)
    fig_line.add_hrect(y0=0.6, y1=1.0,  fillcolor="rgba(248,113,113,0.05)", line_width=0)

    for val, col, lbl in [(0.3,"#34D399","Low/Moderate"), (0.6,"#F87171","Moderate/High")]:
        fig_line.add_hline(y=val, line_dash="dot", line_color=col, line_width=1, opacity=0.4,
                           annotation_text=lbl, annotation_font=dict(color=col,size=10),
                           annotation_position="right")

    for cat, color in color_map.items():
        sub = df[df["risk_category"] == cat]
        fig_line.add_trace(go.Scatter(
            x=sub["timestamp"], y=sub["probability"], mode="markers", name=cat,
            marker=dict(color=color,size=8,opacity=0.9,line=dict(color='#0D0F14',width=1.5)),
            hovertemplate=f"<b>{cat} Risk</b><br>%{{x|%b %d, %H:%M}}<br>Score: %{{y:.2%}}<extra></extra>",
        ))
    fig_line.add_trace(go.Scatter(
        x=df["timestamp"], y=df["probability"], mode="lines", name="Trend",
        line=dict(color='rgba(255,255,255,0.12)',width=1.5), showlegend=False, hoverinfo='skip',
    ))

    fig_line.update_layout(**PLOT_CONFIG, height=300,
        xaxis=dict(title=None,**GRID_STYLE,tickfont=dict(size=11)),
        yaxis=dict(title="Risk Score",tickformat=".0%",**GRID_STYLE,range=[0,1],tickfont=dict(size=11)),
        legend=dict(orientation="h",y=-0.15,x=0.5,xanchor='center',
                    font=dict(size=12,color='#94A3B8'),bgcolor='rgba(0,0,0,0)'),
        hovermode="x unified")
    st.plotly_chart(fig_line, use_container_width=True)

st.markdown('<hr class="fancy-divider"/>', unsafe_allow_html=True)


# ── Chart Row 2: Age & Cholesterol ─────────────────────────────
d1, d2 = st.columns(2, gap="large")

if "age" in df.columns and df["age"].notna().any():
    with d1:
        st.markdown('<p class="section-header">Age vs. Risk Score</p>', unsafe_allow_html=True)
        st.markdown('<p class="section-sub">Correlation between patient age and cardiac probability.</p>',
                    unsafe_allow_html=True)
        fig_age = px.scatter(df.dropna(subset=["age"]), x="age", y="probability",
            color="risk_category",
            color_discrete_map={"Low":"#34D399","Moderate":"#FBBF24","High":"#F87171"},
            trendline="ols", trendline_color_override="rgba(255,255,255,0.2)",
            labels={"probability":"Risk Score","age":"Age"})
        fig_age.update_traces(marker=dict(size=9,line=dict(color='#0D0F14',width=1.2)))
        fig_age.update_layout(**PLOT_CONFIG, height=280,
            xaxis=dict(**GRID_STYLE,tickfont=dict(size=11)),
            yaxis=dict(tickformat=".0%",**GRID_STYLE,tickfont=dict(size=11)),
            legend=dict(bgcolor='rgba(0,0,0,0)',font=dict(color='#94A3B8',size=11)))
        st.plotly_chart(fig_age, use_container_width=True)

if "chol" in df.columns and df["chol"].notna().any():
    with d2:
        st.markdown('<p class="section-header">Cholesterol Distribution</p>', unsafe_allow_html=True)
        st.markdown('<p class="section-sub">Cholesterol levels segmented by risk category.</p>',
                    unsafe_allow_html=True)
        fig_chol = go.Figure()
        for cat, color in {"Low":"#34D399","Moderate":"#FBBF24","High":"#F87171"}.items():
            sub = df[df["risk_category"] == cat].dropna(subset=["chol"])
            if len(sub) == 0:
                continue
            # ✔ use proper rgba — not the broken .replace() pattern
            h = color.lstrip('#')
            fill = f"rgba({int(h[0:2],16)},{int(h[2:4],16)},{int(h[4:6],16)},0.15)"
            fig_chol.add_trace(go.Violin(
                x=sub["risk_category"], y=sub["chol"], name=cat,
                box_visible=True, meanline_visible=True,
                fillcolor=fill, line_color=color, points="outliers",
            ))
        fig_chol.update_layout(**PLOT_CONFIG, height=280,
            xaxis=dict(**GRID_STYLE,tickfont=dict(size=11)),
            yaxis=dict(title="Cholesterol (mg/dl)",**GRID_STYLE,tickfont=dict(size=11)),
            legend=dict(bgcolor='rgba(0,0,0,0)',font=dict(color='#94A3B8',size=11)),
            violingap=0.3)
        st.plotly_chart(fig_chol, use_container_width=True)

st.markdown('<hr class="fancy-divider"/>', unsafe_allow_html=True)


# ── Raw Data Table ─────────────────────────────────────────────
st.markdown('<p class="section-header">Prediction Records</p>', unsafe_allow_html=True)
st.markdown('<p class="section-sub">Full log of all patient predictions. Click column headers to sort.</p>',
            unsafe_allow_html=True)

display_df = df.copy()
display_df["probability"] = display_df["probability"].apply(lambda x: f"{x*100:.1f}%")
display_df["timestamp"]   = display_df["timestamp"].dt.strftime("%b %d %Y, %H:%M")

st.dataframe(display_df, use_container_width=True, height=320,
    column_config={
        "risk_category": st.column_config.TextColumn("Risk Level"),
        "probability":   st.column_config.TextColumn("Risk Score"),
        "timestamp":     st.column_config.TextColumn("Timestamp"),
    })