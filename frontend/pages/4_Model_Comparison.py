import streamlit as st
import json
import pandas as pd
import plotly.graph_objects as go

st.set_page_config(page_title="CardioScan · Model Comparison", layout="wide", page_icon="🏆")

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=DM+Serif+Display&family=DM+Sans:wght@300;400;500;600&display=swap');

html, body, [class*="css"] {
    font-family: 'DM Sans', sans-serif;
    background-color: #0D0F14;
    color: #E8EAF0;
}

[data-testid="stAppViewContainer"] {
    background: radial-gradient(ellipse 70% 40% at 50% -5%, rgba(16,185,129,0.10) 0%, #0D0F14 55%);
}

#MainMenu, footer, header { visibility: hidden; }

.hero-badge {
    display: inline-block;
    background: rgba(16,185,129,0.10);
    border: 1px solid rgba(16,185,129,0.30);
    border-radius: 999px;
    padding: 4px 14px;
    font-size: 11px;
    font-weight: 600;
    letter-spacing: 0.12em;
    text-transform: uppercase;
    color: #34D399;
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
.hero-title span { color: #34D399; }

.hero-subtitle {
    font-size: 14px;
    color: #475569;
    font-weight: 300;
    margin: 0 0 36px 0;
}

.fancy-divider {
    border: none;
    height: 1px;
    background: linear-gradient(90deg, transparent, rgba(255,255,255,0.07), transparent);
    margin: 36px 0;
}

.winner-card {
    background: rgba(255,255,255,0.025);
    border: 1px solid rgba(255,255,255,0.07);
    border-radius: 18px;
    padding: 26px 24px 22px;
    position: relative;
    overflow: hidden;
}
.winner-card::before {
    content: '';
    position: absolute;
    top: 0; left: 0; right: 0;
    height: 2px;
    border-radius: 18px 18px 0 0;
    background: var(--stripe);
}
.winner-eyebrow {
    font-size: 10px; font-weight: 600; letter-spacing: 0.14em;
    text-transform: uppercase; color: #334155; margin-bottom: 8px;
}
.winner-model {
    font-family: 'DM Serif Display', serif;
    font-size: 26px; font-weight: 400; color: #F1F5F9; margin-bottom: 6px;
}
.winner-score { font-size: 13px; color: var(--score-color); font-weight: 500; }
.winner-icon {
    position: absolute; top: 20px; right: 22px;
    font-size: 28px; opacity: 0.5;
}

.rank-row {
    display: flex; align-items: center; gap: 16px;
    background: rgba(255,255,255,0.025);
    border: 1px solid rgba(255,255,255,0.06);
    border-radius: 12px; padding: 14px 20px; margin-bottom: 10px;
    transition: border-color 0.2s;
}
.rank-row:hover { border-color: rgba(255,255,255,0.12); }
.rank-medal { font-size: 18px; flex-shrink: 0; }
.rank-name  { font-weight: 500; font-size: 14px; color: #CBD5E1; flex: 1; }
.rank-bar-wrap {
    flex: 2; background: rgba(255,255,255,0.05);
    border-radius: 999px; height: 6px; overflow: hidden;
}
.rank-bar  { height: 6px; border-radius: 999px; }
.rank-val  { font-size: 13px; font-weight: 600; width: 52px; text-align: right; flex-shrink: 0; }

.section-header {
    font-family: 'DM Serif Display', serif;
    font-size: 22px; color: #F1F5F9; margin: 0 0 2px 0;
}
.section-sub { font-size: 13px; color: #475569; margin-bottom: 20px; }

.stSelectbox > div > div {
    background: rgba(255,255,255,0.04) !important;
    border: 1px solid rgba(255,255,255,0.08) !important;
    border-radius: 10px !important;
    color: #E8EAF0 !important;
}
</style>
""", unsafe_allow_html=True)

PLOT_CFG = dict(
    paper_bgcolor='rgba(0,0,0,0)',
    plot_bgcolor='rgba(0,0,0,0)',
    font=dict(family='DM Sans', color='#64748B'),
    margin=dict(t=24, b=24, l=10, r=10),
)
GRID = dict(gridcolor='rgba(255,255,255,0.05)', zerolinecolor='rgba(255,255,255,0.04)')

MODEL_COLORS = {
    "random_forest":       "#34D399",
    "logistic_regression": "#60A5FA",
    "gradient_boosting":   "#FBBF24",
}
DEFAULT_COLORS = ["#34D399", "#60A5FA", "#FBBF24", "#F87171", "#A78BFA"]
MEDALS = ["🥇", "🥈", "🥉"]


# ── Helper: safe hex → rgba ────────────────────────────────────
def hex_rgba(hex_color, alpha):
    """Convert #RRGGBB to rgba(r,g,b,alpha) correctly."""
    h = hex_color.lstrip('#')
    r, g, b = int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)
    return f'rgba({r},{g},{b},{alpha})'


# ── Hero ───────────────────────────────────────────────────────
st.markdown('<div class="hero-badge">Head-to-Head</div>', unsafe_allow_html=True)
st.markdown('<h1 class="hero-title">Model <span>Comparison</span></h1>', unsafe_allow_html=True)
st.markdown('<p class="hero-subtitle">Side-by-side evaluation of all trained classifiers across key performance metrics.</p>', unsafe_allow_html=True)


# ── Load Data ──────────────────────────────────────────────────
try:
    with open("../model/model_comparison.json") as f:
        raw = json.load(f)
except FileNotFoundError:
    st.error("⚠  `model_comparison.json` not found. Please re-run the training script.")
    st.stop()

df = pd.DataFrame(raw).T.reset_index()
df.columns  = ["Model", "Accuracy", "ROC_AUC"]
df["Display"] = df["Model"].str.replace("_", " ").str.title()
df["Color"]   = df["Model"].apply(lambda m: MODEL_COLORS.get(m, DEFAULT_COLORS[0]))

df_acc = df.sort_values("Accuracy", ascending=False).reset_index(drop=True)
df_auc = df.sort_values("ROC_AUC",  ascending=False).reset_index(drop=True)

best_acc = df_acc.iloc[0]
best_auc = df_auc.iloc[0]


# ── Winner Cards ───────────────────────────────────────────────
w1, w2 = st.columns(2, gap="large")

with w1:
    st.markdown(f"""
    <div class="winner-card" style="--stripe:{best_acc['Color']};">
        <div class="winner-icon">🎯</div>
        <div class="winner-eyebrow">Best Accuracy</div>
        <div class="winner-model">{best_acc['Display']}</div>
        <div class="winner-score" style="--score-color:{best_acc['Color']};">
            {best_acc['Accuracy']*100:.2f}% accuracy
        </div>
    </div>""", unsafe_allow_html=True)

with w2:
    st.markdown(f"""
    <div class="winner-card" style="--stripe:{best_auc['Color']};">
        <div class="winner-icon">📐</div>
        <div class="winner-eyebrow">Best ROC-AUC</div>
        <div class="winner-model">{best_auc['Display']}</div>
        <div class="winner-score" style="--score-color:{best_auc['Color']};">
            {best_auc['ROC_AUC']*100:.2f}% AUC
        </div>
    </div>""", unsafe_allow_html=True)

st.markdown('<hr class="fancy-divider"/>', unsafe_allow_html=True)


# ── Bar Charts ─────────────────────────────────────────────────
ch1, ch2 = st.columns(2, gap="large")

with ch1:
    st.markdown('<p class="section-header">Accuracy</p>', unsafe_allow_html=True)
    st.markdown('<p class="section-sub">Percentage of correctly classified samples.</p>', unsafe_allow_html=True)

    fig_acc = go.Figure()
    for _, row in df_acc.iterrows():
        fig_acc.add_trace(go.Bar(
            x=[row["Display"]], y=[row["Accuracy"] * 100],
            name=row["Display"],
            marker=dict(color=row["Color"], opacity=0.85,
                        line=dict(color='rgba(0,0,0,0)', width=0)),
            hovertemplate=f"<b>{row['Display']}</b><br>Accuracy: %{{y:.2f}}%<extra></extra>",
            width=0.45,
        ))
    fig_acc.update_layout(
        **PLOT_CFG, height=300, showlegend=False, bargap=0.35,
        xaxis=dict(**GRID, tickfont=dict(size=12, color='#94A3B8')),
        yaxis=dict(**GRID, ticksuffix="%",
                   range=[max(0, df["Accuracy"].min()*100-5), 100],
                   tickfont=dict(size=11)),
    )
    fig_acc.add_annotation(
        x=best_acc["Display"], y=best_acc["Accuracy"]*100+0.8,
        text="★ Best", showarrow=False,
        font=dict(color=best_acc["Color"], size=11, family="DM Sans"),
    )
    st.plotly_chart(fig_acc, use_container_width=True)

with ch2:
    st.markdown('<p class="section-header">ROC-AUC</p>', unsafe_allow_html=True)
    st.markdown('<p class="section-sub">Area under the receiver operating characteristic curve.</p>', unsafe_allow_html=True)

    fig_auc = go.Figure()
    for _, row in df_auc.iterrows():
        fig_auc.add_trace(go.Bar(
            x=[row["Display"]], y=[row["ROC_AUC"] * 100],
            name=row["Display"],
            marker=dict(color=row["Color"], opacity=0.85,
                        line=dict(color='rgba(0,0,0,0)', width=0)),
            hovertemplate=f"<b>{row['Display']}</b><br>ROC-AUC: %{{y:.2f}}%<extra></extra>",
            width=0.45,
        ))
    fig_auc.update_layout(
        **PLOT_CFG, height=300, showlegend=False, bargap=0.35,
        xaxis=dict(**GRID, tickfont=dict(size=12, color='#94A3B8')),
        yaxis=dict(**GRID, ticksuffix="%",
                   range=[max(0, df["ROC_AUC"].min()*100-5), 100],
                   tickfont=dict(size=11)),
    )
    fig_auc.add_annotation(
        x=best_auc["Display"], y=best_auc["ROC_AUC"]*100+0.8,
        text="★ Best", showarrow=False,
        font=dict(color=best_auc["Color"], size=11, family="DM Sans"),
    )
    st.plotly_chart(fig_auc, use_container_width=True)

st.markdown('<hr class="fancy-divider"/>', unsafe_allow_html=True)


# ── Radar Chart ────────────────────────────────────────────────
st.markdown('<p class="section-header">Multi-Metric Overview</p>', unsafe_allow_html=True)
st.markdown('<p class="section-sub">Radar comparison across both metrics for every model.</p>', unsafe_allow_html=True)

categories  = ["Accuracy", "ROC-AUC"]
fig_radar   = go.Figure()

for _, row in df.iterrows():
    vals = [row["Accuracy"] * 100, row["ROC_AUC"] * 100]
    fig_radar.add_trace(go.Scatterpolar(
        r     = vals + [vals[0]],
        theta = categories + [categories[0]],
        fill  = 'toself',
        name  = row["Display"],
        line  = dict(color=row["Color"], width=2),
        marker= dict(color=row["Color"], size=7),
        # ✔ FIX: use hex_rgba() — old code produced invalid 'rgba(34D399,0.08)'
        fillcolor = hex_rgba(row["Color"], 0.08),
        hovertemplate = "<b>%{theta}</b>: %{r:.2f}%<extra>" + row["Display"] + "</extra>",
    ))

fig_radar.update_layout(
    **PLOT_CFG, height=340,
    polar=dict(
        bgcolor='rgba(255,255,255,0.02)',
        radialaxis=dict(
            visible=True,
            range=[max(0, min(df["Accuracy"].min(), df["ROC_AUC"].min())*100-5), 100],
            tickfont=dict(size=9, color='#334155'),
            gridcolor='rgba(255,255,255,0.06)',
            linecolor='rgba(255,255,255,0.06)',
        ),
        angularaxis=dict(
            tickfont=dict(size=12, color='#94A3B8'),
            gridcolor='rgba(255,255,255,0.06)',
            linecolor='rgba(255,255,255,0.08)',
        ),
    ),
    legend=dict(
        orientation="h", y=-0.12, x=0.5, xanchor='center',
        font=dict(size=12, color='#94A3B8'),
        bgcolor='rgba(0,0,0,0)',
    ),
)
st.plotly_chart(fig_radar, use_container_width=True)

st.markdown('<hr class="fancy-divider"/>', unsafe_allow_html=True)


# ── Ranking Table ──────────────────────────────────────────────
metric_options = {"Accuracy": "Accuracy", "ROC-AUC": "ROC_AUC"}
sort_by_label  = st.selectbox("Rank by", list(metric_options.keys()), label_visibility="collapsed")
sort_col       = metric_options[sort_by_label]

st.markdown('<p class="section-header">Model Rankings</p>', unsafe_allow_html=True)
st.markdown(f'<p class="section-sub">Sorted by {sort_by_label} — highest to lowest.</p>', unsafe_allow_html=True)

df_ranked = df.sort_values(sort_col, ascending=False).reset_index(drop=True)
max_val   = df_ranked[sort_col].max()

for i, row in df_ranked.iterrows():
    val     = row[sort_col]
    bar_pct = val / max_val * 100
    medal   = MEDALS[i] if i < 3 else f"#{i+1}"
    color   = row["Color"]

    st.markdown(f"""
    <div class="rank-row">
        <div class="rank-medal">{medal}</div>
        <div class="rank-name">{row['Display']}</div>
        <div class="rank-bar-wrap">
            <div class="rank-bar" style="width:{bar_pct:.1f}%; background:{color};"></div>
        </div>
        <div class="rank-val" style="color:{color};">{val*100:.2f}%</div>
    </div>""", unsafe_allow_html=True)