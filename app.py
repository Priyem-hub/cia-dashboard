"""
app.py  ─  Global Conflict Intelligence Dashboard
--------------------------------------------------
CIA-style geopolitical intelligence interface built with Streamlit + PyDeck + Plotly.
"""

import math
import pandas as pd
import numpy as np
import streamlit as st
import pydeck as pdk
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime

from conflict_model import get_model

# ═══════════════════════════════════════════════════════════════════════════════
#  PAGE CONFIG  ─  must be first Streamlit call
# ═══════════════════════════════════════════════════════════════════════════════

st.set_page_config(
    page_title="Global Conflict Intelligence",
    page_icon="🛰️",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ═══════════════════════════════════════════════════════════════════════════════
#  GLOBAL CSS  ─  terminal / intelligence-console aesthetic
# ═══════════════════════════════════════════════════════════════════════════════

st.markdown("""
<style>
/* ── Fonts ── */
@import url('https://fonts.googleapis.com/css2?family=Share+Tech+Mono&family=Rajdhani:wght@300;400;500;600;700&family=Orbitron:wght@400;700;900&display=swap');

/* ── Base ── */
html, body, [class*="css"] {
    background-color: #030a0e !important;
    color: #c8d8e0 !important;
    font-family: 'Rajdhani', sans-serif !important;
}

/* ── Streamlit root overrides ── */
.stApp { background: #030a0e; }
section[data-testid="stSidebar"] {
    background: #050d12 !important;
    border-right: 1px solid #0f2733;
}
section[data-testid="stSidebar"] * { color: #8ab4c0 !important; }

/* ── Hide default Streamlit chrome ── */
#MainMenu, footer, header { visibility: hidden; }

/* ── Scrollbar ── */
::-webkit-scrollbar { width: 4px; }
::-webkit-scrollbar-track { background: #030a0e; }
::-webkit-scrollbar-thumb { background: #1a3a4a; border-radius: 2px; }

/* ── Custom header banner ── */
.cia-header {
    background: linear-gradient(90deg, #000d14 0%, #051520 40%, #000d14 100%);
    border-top: 2px solid #cc0000;
    border-bottom: 1px solid #0f2733;
    padding: 18px 32px;
    margin-bottom: 0;
    display: flex;
    align-items: center;
    justify-content: space-between;
}
.cia-header-title {
    font-family: 'Orbitron', monospace;
    font-size: 22px;
    font-weight: 900;
    color: #ff2200;
    letter-spacing: 4px;
    text-transform: uppercase;
    text-shadow: 0 0 20px rgba(255,34,0,0.6), 0 0 40px rgba(255,34,0,0.2);
}
.cia-header-sub {
    font-family: 'Share Tech Mono', monospace;
    font-size: 11px;
    color: #4a7a8a;
    letter-spacing: 2px;
    margin-top: 4px;
}
.cia-header-time {
    font-family: 'Share Tech Mono', monospace;
    font-size: 13px;
    color: #cc4400;
    text-align: right;
}

/* ── Metric cards ── */
.metric-card {
    background: linear-gradient(135deg, #070f14 0%, #0a1a22 100%);
    border: 1px solid #0f2733;
    border-left: 3px solid #cc0000;
    border-radius: 4px;
    padding: 16px 20px;
    margin: 4px 0;
    position: relative;
    overflow: hidden;
}
.metric-card::before {
    content: '';
    position: absolute; top: 0; right: 0;
    width: 60px; height: 100%;
    background: linear-gradient(90deg, transparent, rgba(204,0,0,0.04));
}
.metric-label {
    font-family: 'Share Tech Mono', monospace;
    font-size: 10px;
    color: #4a7a8a;
    letter-spacing: 2px;
    text-transform: uppercase;
    margin-bottom: 6px;
}
.metric-value {
    font-family: 'Orbitron', monospace;
    font-size: 28px;
    font-weight: 700;
    color: #ff2200;
    text-shadow: 0 0 12px rgba(255,34,0,0.5);
    line-height: 1;
}
.metric-delta {
    font-family: 'Share Tech Mono', monospace;
    font-size: 11px;
    color: #4a7a8a;
    margin-top: 4px;
}

/* ── Section titles ── */
.section-title {
    font-family: 'Orbitron', monospace;
    font-size: 13px;
    font-weight: 700;
    color: #cc4400;
    letter-spacing: 3px;
    text-transform: uppercase;
    border-bottom: 1px solid #0f2733;
    padding-bottom: 8px;
    margin: 20px 0 14px 0;
}

/* ── Intel panel ── */
.intel-panel {
    background: #070f14;
    border: 1px solid #0f2733;
    border-radius: 4px;
    padding: 16px;
}

/* ── Risk badge ── */
.risk-badge {
    display: inline-block;
    padding: 3px 10px;
    border-radius: 2px;
    font-family: 'Share Tech Mono', monospace;
    font-size: 11px;
    font-weight: 700;
    letter-spacing: 1px;
}
.risk-critical { background: rgba(200,0,0,0.2); color: #ff2200; border: 1px solid #cc0000; }
.risk-high     { background: rgba(200,80,0,0.2); color: #ff6600; border: 1px solid #cc4400; }
.risk-elevated { background: rgba(200,140,0,0.2); color: #ffaa00; border: 1px solid #cc8800; }
.risk-moderate { background: rgba(180,180,0,0.2); color: #dddd00; border: 1px solid #aaaa00; }
.risk-low      { background: rgba(0,160,0,0.2);   color: #00cc44; border: 1px solid #008833; }

/* ── Dataframe ── */
.stDataFrame { border: 1px solid #0f2733 !important; }
.stDataFrame thead th {
    background: #050d12 !important;
    color: #cc4400 !important;
    font-family: 'Share Tech Mono', monospace !important;
    font-size: 11px !important;
    letter-spacing: 1px;
}
.stDataFrame tbody td {
    background: #070f14 !important;
    color: #c8d8e0 !important;
    font-family: 'Rajdhani', sans-serif !important;
    border-color: #0f2733 !important;
}

/* ── Sliders ── */
.stSlider > div > div > div > div {
    background: #cc0000 !important;
}

/* ── Buttons ── */
.stButton > button {
    background: linear-gradient(135deg, #200000, #3a0000) !important;
    color: #ff4444 !important;
    border: 1px solid #660000 !important;
    border-radius: 2px !important;
    font-family: 'Orbitron', monospace !important;
    font-size: 11px !important;
    letter-spacing: 2px !important;
    padding: 8px 20px !important;
}
.stButton > button:hover {
    background: linear-gradient(135deg, #3a0000, #600000) !important;
    border-color: #cc0000 !important;
    color: #ff0000 !important;
}

/* ── Tab overrides ── */
.stTabs [data-baseweb="tab-list"] {
    background: #050d12;
    border-bottom: 1px solid #0f2733;
}
.stTabs [data-baseweb="tab"] {
    font-family: 'Orbitron', monospace !important;
    font-size: 11px !important;
    letter-spacing: 2px;
    color: #4a7a8a !important;
}
.stTabs [aria-selected="true"] {
    color: #ff2200 !important;
    border-bottom: 2px solid #cc0000 !important;
}

/* ── Scan-line overlay ── */
.scanlines {
    position: fixed; top: 0; left: 0; right: 0; bottom: 0;
    background: repeating-linear-gradient(
        0deg,
        transparent,
        transparent 2px,
        rgba(0, 255, 80, 0.012) 2px,
        rgba(0, 255, 80, 0.012) 4px
    );
    pointer-events: none;
    z-index: 9999;
}

/* ── Prediction result box ── */
.prediction-result {
    background: linear-gradient(135deg, #0a0005, #12000a);
    border: 1px solid #330011;
    border-left: 4px solid #cc0000;
    border-radius: 4px;
    padding: 20px;
    margin-top: 12px;
}
.prediction-score {
    font-family: 'Orbitron', monospace;
    font-size: 56px;
    font-weight: 900;
    text-align: center;
    text-shadow: 0 0 30px currentColor;
    line-height: 1;
}
.prediction-label {
    font-family: 'Share Tech Mono', monospace;
    font-size: 13px;
    letter-spacing: 3px;
    text-align: center;
    margin-top: 6px;
}

/* ── Sidebar labels ── */
.sidebar-section {
    font-family: 'Orbitron', monospace;
    font-size: 10px;
    color: #cc4400;
    letter-spacing: 2px;
    text-transform: uppercase;
    margin: 16px 0 8px 0;
    border-bottom: 1px solid #0f2733;
    padding-bottom: 4px;
}
</style>

<div class="scanlines"></div>
""", unsafe_allow_html=True)


# ═══════════════════════════════════════════════════════════════════════════════
#  DATA & MODEL LOADING
# ═══════════════════════════════════════════════════════════════════════════════

@st.cache_data
def load_data() -> pd.DataFrame:
    df = pd.read_csv("dataset.csv")
    df["risk_score"] = pd.to_numeric(df["risk_score"], errors="coerce").fillna(50)
    df["latitude"]   = pd.to_numeric(df["latitude"],   errors="coerce")
    df["longitude"]  = pd.to_numeric(df["longitude"],  errors="coerce")
    return df.dropna(subset=["latitude", "longitude"])

@st.cache_resource
def load_model():
    m = get_model("dataset.csv")
    return m

df   = load_data()
model = load_model()

# Risk helpers
def risk_class(score: float) -> str:
    if score >= 80: return "CRITICAL"
    if score >= 65: return "HIGH"
    if score >= 45: return "ELEVATED"
    if score >= 25: return "MODERATE"
    return "LOW"

def risk_color(score: float) -> list:
    if score >= 80: return [220,  20,  20, 230]
    if score >= 65: return [220, 100,   0, 210]
    if score >= 45: return [220, 160,   0, 190]
    if score >= 25: return [180, 180,   0, 170]
    return              [  0, 160,  60, 150]

def risk_hex(score: float) -> str:
    if score >= 80: return "#cc1414"
    if score >= 65: return "#cc6400"
    if score >= 45: return "#cca000"
    if score >= 25: return "#b4b400"
    return "#00a03c"

df["risk_level"] = df["risk_score"].apply(risk_class)
df["color"]      = df["risk_score"].apply(risk_color)
df["risk_hex"]   = df["risk_score"].apply(risk_hex)
df["radius"]     = df["risk_score"].apply(lambda s: int(80000 + s * 6000))


# ═══════════════════════════════════════════════════════════════════════════════
#  SIDEBAR
# ═══════════════════════════════════════════════════════════════════════════════

with st.sidebar:
    st.markdown("""
    <div style="text-align:center; padding:12px 0 8px 0;">
        <div style="font-family:'Orbitron',monospace; font-size:14px; color:#cc0000;
                    letter-spacing:3px; text-shadow:0 0 10px rgba(204,0,0,0.5);">
            ◈ GCID SYSTEM ◈
        </div>
        <div style="font-family:'Share Tech Mono',monospace; font-size:10px;
                    color:#2a4a5a; margin-top:4px; letter-spacing:1px;">
            CLASSIFICATION: RESTRICTED
        </div>
    </div>
    """, unsafe_allow_html=True)

    st.divider()

    st.markdown('<div class="sidebar-section">▸ Filters</div>', unsafe_allow_html=True)

    risk_filter = st.multiselect(
        "Risk Level",
        options=["CRITICAL","HIGH","ELEVATED","MODERATE","LOW"],
        default=["CRITICAL","HIGH","ELEVATED","MODERATE","LOW"],
    )

    region_options = sorted(df["region"].unique().tolist())
    region_filter  = st.multiselect("Region", region_options, default=region_options)

    score_range = st.slider("Risk Score Range", 0, 100, (0, 100))

    st.markdown('<div class="sidebar-section">▸ Map Settings</div>', unsafe_allow_html=True)

    map_pitch   = st.slider("Map Pitch",  0, 60, 30)
    pulse_alpha = st.slider("Pulse Intensity", 50, 255, 180)

    st.divider()
    st.markdown(f"""
    <div style="font-family:'Share Tech Mono',monospace; font-size:10px; color:#1a3a4a; text-align:center;">
        ACTIVE NODES: {len(df)}<br>
        MODEL: RF-ENSEMBLE v2.4<br>
        STATUS: <span style="color:#00cc44;">ONLINE</span>
    </div>
    """, unsafe_allow_html=True)


# ═══════════════════════════════════════════════════════════════════════════════
#  FILTER DATA
# ═══════════════════════════════════════════════════════════════════════════════

fdf = df[
    df["risk_level"].isin(risk_filter) &
    df["region"].isin(region_filter)   &
    df["risk_score"].between(score_range[0], score_range[1])
].copy()


# ═══════════════════════════════════════════════════════════════════════════════
#  HEADER
# ═══════════════════════════════════════════════════════════════════════════════

now = datetime.utcnow().strftime("%Y-%m-%d  %H:%M:%S  UTC")
st.markdown(f"""
<div class="cia-header">
  <div>
    <div class="cia-header-title">🛰 Global Conflict Intelligence</div>
    <div class="cia-header-sub">GEOPOLITICAL THREAT ASSESSMENT SYSTEM  ·  CLASSIFICATION LEVEL: RESTRICTED</div>
  </div>
  <div class="cia-header-time">
    <div style="font-size:16px; color:#cc0000; font-family:'Orbitron',monospace;">{now[:10]}</div>
    <div style="font-size:12px; margin-top:2px;">{now[11:]}</div>
    <div style="font-size:10px; margin-top:4px; color:#2a4a5a; letter-spacing:1px;">LIVE FEED</div>
  </div>
</div>
""", unsafe_allow_html=True)


# ═══════════════════════════════════════════════════════════════════════════════
#  GLOBAL METRICS ROW
# ═══════════════════════════════════════════════════════════════════════════════

st.markdown('<div style="height:14px"></div>', unsafe_allow_html=True)

critical_n  = int((fdf["risk_score"] >= 80).sum())
high_n      = int(((fdf["risk_score"] >= 65) & (fdf["risk_score"] < 80)).sum())
avg_risk    = round(float(fdf["risk_score"].mean()), 1) if len(fdf) else 0
hottest     = fdf.loc[fdf["risk_score"].idxmax(), "country"] if len(fdf) else "—"

c1, c2, c3, c4 = st.columns(4)
with c1:
    st.markdown(f"""
    <div class="metric-card">
      <div class="metric-label">◈ Active Zones Monitored</div>
      <div class="metric-value">{len(fdf)}</div>
      <div class="metric-delta">of {len(df)} total indexed regions</div>
    </div>""", unsafe_allow_html=True)

with c2:
    st.markdown(f"""
    <div class="metric-card">
      <div class="metric-label">⚠ Critical Threat Zones</div>
      <div class="metric-value" style="color:#ff0000">{critical_n}</div>
      <div class="metric-delta">{high_n} HIGH  ·  risk ≥ 80</div>
    </div>""", unsafe_allow_html=True)

with c3:
    color = risk_hex(avg_risk)
    st.markdown(f"""
    <div class="metric-card">
      <div class="metric-label">◈ Global Average Risk</div>
      <div class="metric-value" style="color:{color}">{avg_risk}</div>
      <div class="metric-delta">composite threat index  /  100</div>
    </div>""", unsafe_allow_html=True)

with c4:
    st.markdown(f"""
    <div class="metric-card">
      <div class="metric-label">◈ Highest Threat Nation</div>
      <div class="metric-value" style="font-size:20px; padding-top:4px; color:#ff2200">{hottest}</div>
      <div class="metric-delta">primary watch zone</div>
    </div>""", unsafe_allow_html=True)


# ═══════════════════════════════════════════════════════════════════════════════
#  TABS
# ═══════════════════════════════════════════════════════════════════════════════

tab1, tab2, tab3, tab4 = st.tabs([
    "◈  GLOBAL THREAT MAP",
    "◈  HOTSPOT RANKING",
    "◈  ANALYTICS",
    "◈  SCENARIO SIMULATOR",
])


# ─── TAB 1: GLOBAL THREAT MAP ──────────────────────────────────────────────────

with tab1:
    st.markdown('<div class="section-title">◈ Geospatial Conflict Distribution</div>', unsafe_allow_html=True)

    if len(fdf) == 0:
        st.warning("No data matches current filters.")
    else:
        # Pulsing scatter layer (main hotspot markers)
        scatter_layer = pdk.Layer(
            "ScatterplotLayer",
            data=fdf,
            get_position=["longitude", "latitude"],
            get_radius="radius",
            get_fill_color="color",
            pickable=True,
            opacity=0.85,
            stroked=True,
            get_line_color=[255, 255, 255, 30],
            line_width_min_pixels=1,
        )

        # Halo ring (outer glow)
        halo_df = fdf.copy()
        halo_df["halo_color"] = halo_df["risk_score"].apply(
            lambda s: [220, 20, 20, 35] if s >= 80 else
                      [220, 100, 0, 25] if s >= 65 else
                      [180, 140, 0, 20] if s >= 45 else
                      [0, 140, 40, 15]
        )
        halo_df["halo_radius"] = halo_df["risk_score"].apply(lambda s: int(120000 + s * 9000))

        halo_layer = pdk.Layer(
            "ScatterplotLayer",
            data=halo_df,
            get_position=["longitude", "latitude"],
            get_radius="halo_radius",
            get_fill_color="halo_color",
            pickable=False,
            opacity=1.0,
            stroked=False,
        )

        # Text labels for critical zones
        crit_df = fdf[fdf["risk_score"] >= 75].copy()
        text_layer = pdk.Layer(
            "TextLayer",
            data=crit_df,
            get_position=["longitude", "latitude"],
            get_text="country",
            get_size=14,
            get_color=[255, 100, 80, 220],
            get_angle=0,
            get_alignment_baseline="'bottom'",
            get_pixel_offset=[0, -18],
            font_family="'Share Tech Mono'",
        )

        view_state = pdk.ViewState(
            latitude=20,
            longitude=10,
            zoom=1.4,
            pitch=map_pitch,
            bearing=0,
        )

        tooltip = {
            "html": """
            <div style="background:#050d12; border:1px solid #cc0000; border-radius:4px;
                        padding:10px 14px; font-family:'Share Tech Mono',monospace;">
              <div style="color:#ff2200; font-size:13px; font-weight:bold;">{country}</div>
              <div style="color:#4a7a8a; font-size:10px; margin:2px 0;">{region}</div>
              <hr style="border-color:#0f2733; margin:6px 0;">
              <div style="color:#cc8800;">RISK SCORE: <span style="color:#ffaa00">{risk_score}</span></div>
              <div style="color:#4a7a8a;">LEVEL: {risk_level}</div>
              <div style="color:#4a7a8a;">LAT {latitude:.2f}  ·  LON {longitude:.2f}</div>
            </div>
            """,
            "style": {"backgroundColor": "transparent", "border": "none"},
        }

        deck = pdk.Deck(
            layers=[halo_layer, scatter_layer, text_layer],
            initial_view_state=view_state,
            map_style="mapbox://styles/mapbox/dark-v11",
            tooltip=tooltip,
        )

        st.pydeck_chart(deck, use_container_width=True, height=520)

        # Quick legend
        st.markdown("""
        <div style="display:flex; gap:20px; padding:10px 4px;
                    font-family:'Share Tech Mono',monospace; font-size:11px; color:#4a7a8a;">
          <span>🔴 CRITICAL ≥80</span>
          <span>🟠 HIGH 65–79</span>
          <span>🟡 ELEVATED 45–64</span>
          <span>🟤 MODERATE 25–44</span>
          <span>🟢 LOW &lt;25</span>
        </div>
        """, unsafe_allow_html=True)


# ─── TAB 2: HOTSPOT RANKING ────────────────────────────────────────────────────

with tab2:
    st.markdown('<div class="section-title">◈ Conflict Hotspot Intelligence Ranking</div>', unsafe_allow_html=True)

    ranked = fdf.sort_values("risk_score", ascending=False).reset_index(drop=True)
    ranked.index += 1

    def badge(level):
        cls = f"risk-{level.lower()}"
        return f'<span class="risk-badge {cls}">{level}</span>'

    def bar(score, maxw=120):
        color = risk_hex(score)
        w = int(score / 100 * maxw)
        return f"""
        <div style="background:#0a1a22; border-radius:2px; height:10px; width:{maxw}px; display:inline-block; vertical-align:middle;">
          <div style="background:{color}; height:10px; width:{w}px; border-radius:2px;
                      box-shadow:0 0 6px {color};"></div>
        </div>
        <span style="font-family:'Share Tech Mono',monospace; font-size:11px;
                     color:{color}; margin-left:6px;">{score:.0f}</span>
        """

    # Build HTML table
    rows_html = ""
    for rank, row in ranked.iterrows():
        rows_html += f"""
        <tr style="border-bottom:1px solid #0a1822;">
          <td style="color:#4a7a8a; font-family:'Share Tech Mono',monospace;
                     padding:8px 12px; font-size:12px;">#{rank:02d}</td>
          <td style="color:#e0eef5; font-family:'Rajdhani',sans-serif;
                     font-weight:600; padding:8px 12px;">{row['country']}</td>
          <td style="color:#4a7a8a; font-family:'Share Tech Mono',monospace;
                     padding:8px 12px; font-size:11px;">{row['region']}</td>
          <td style="padding:8px 12px;">{bar(row['risk_score'])}</td>
          <td style="padding:8px 12px;">{badge(row['risk_level'])}</td>
          <td style="color:#6a9ab0; font-family:'Share Tech Mono',monospace;
                     padding:8px 12px; font-size:11px;">{row.get('active_conflicts','—')}</td>
          <td style="color:#6a9ab0; font-family:'Share Tech Mono',monospace;
                     padding:8px 12px; font-size:11px;">{row.get('military_spending','—'):.1f}%</td>
        </tr>
        """

    table_html = f"""
    <div class="intel-panel" style="overflow-x:auto;">
    <table style="width:100%; border-collapse:collapse;">
      <thead>
        <tr style="border-bottom:2px solid #cc0000;">
          <th style="color:#cc4400; font-family:'Share Tech Mono',monospace; font-size:10px;
                     letter-spacing:2px; padding:10px 12px; text-align:left;">RANK</th>
          <th style="color:#cc4400; font-family:'Share Tech Mono',monospace; font-size:10px;
                     letter-spacing:2px; padding:10px 12px; text-align:left;">NATION</th>
          <th style="color:#cc4400; font-family:'Share Tech Mono',monospace; font-size:10px;
                     letter-spacing:2px; padding:10px 12px; text-align:left;">REGION</th>
          <th style="color:#cc4400; font-family:'Share Tech Mono',monospace; font-size:10px;
                     letter-spacing:2px; padding:10px 12px; text-align:left;">RISK INDEX</th>
          <th style="color:#cc4400; font-family:'Share Tech Mono',monospace; font-size:10px;
                     letter-spacing:2px; padding:10px 12px; text-align:left;">LEVEL</th>
          <th style="color:#cc4400; font-family:'Share Tech Mono',monospace; font-size:10px;
                     letter-spacing:2px; padding:10px 12px; text-align:left;">CONFLICTS</th>
          <th style="color:#cc4400; font-family:'Share Tech Mono',monospace; font-size:10px;
                     letter-spacing:2px; padding:10px 12px; text-align:left;">MIL. SPEND</th>
        </tr>
      </thead>
      <tbody>{rows_html}</tbody>
    </table>
    </div>
    """
    st.markdown(table_html, unsafe_allow_html=True)


# ─── TAB 3: ANALYTICS ─────────────────────────────────────────────────────────

with tab3:
    st.markdown('<div class="section-title">◈ Geopolitical Analytics Intelligence</div>', unsafe_allow_html=True)

    col_a, col_b = st.columns(2)

    PLOTLY_LAYOUT = dict(
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="#070f14",
        font=dict(family="Share Tech Mono", color="#6a9ab0", size=11),
        margin=dict(l=40, r=20, t=40, b=40),
        xaxis=dict(gridcolor="#0a1822", linecolor="#0f2733", tickfont=dict(color="#4a7a8a")),
        yaxis=dict(gridcolor="#0a1822", linecolor="#0f2733", tickfont=dict(color="#4a7a8a")),
        coloraxis_showscale=False,
    )

    with col_a:
        # ── Risk distribution histogram
        fig_hist = go.Figure()
        colors_bins = ["#00a03c","#b4b400","#cca000","#cc6400","#cc1414"]
        bins = [0,25,45,65,80,100]
        labels = ["LOW","MODERATE","ELEVATED","HIGH","CRITICAL"]
        for i in range(len(bins)-1):
            subset = fdf[(fdf["risk_score"] >= bins[i]) & (fdf["risk_score"] < bins[i+1])]
            fig_hist.add_trace(go.Bar(
                x=[labels[i]], y=[len(subset)],
                marker_color=colors_bins[i],
                marker_line_color="rgba(0,0,0,0.3)",
                marker_line_width=1,
                name=labels[i],
                showlegend=False,
            ))
        fig_hist.update_layout(
            title=dict(text="THREAT LEVEL DISTRIBUTION", font=dict(color="#cc4400", size=12, family="Orbitron")),
            **PLOTLY_LAYOUT,
            barmode="group",
        )
        st.plotly_chart(fig_hist, use_container_width=True)

    with col_b:
        # ── Regional average risk radar / bar
        reg_avg = (fdf.groupby("region")["risk_score"].mean().sort_values(ascending=True).reset_index())
        fig_reg = go.Figure(go.Bar(
            x=reg_avg["risk_score"],
            y=reg_avg["region"],
            orientation="h",
            marker=dict(
                color=reg_avg["risk_score"],
                colorscale=[[0,"#004020"],[0.4,"#6a6a00"],[0.7,"#aa4400"],[1.0,"#cc0000"]],
                line=dict(color="rgba(0,0,0,0.3)", width=1),
            ),
            text=reg_avg["risk_score"].round(1),
            textposition="outside",
            textfont=dict(color="#cc8800", size=10, family="Share Tech Mono"),
        ))
        fig_reg.update_layout(
            title=dict(text="AVERAGE RISK BY REGION", font=dict(color="#cc4400", size=12, family="Orbitron")),
            **PLOTLY_LAYOUT,
        )
        st.plotly_chart(fig_reg, use_container_width=True)

    # ── Second row
    col_c, col_d = st.columns(2)

    with col_c:
        # Scatter: military spending vs risk
        if "military_spending" in fdf.columns:
            fig_sc = go.Figure()
            for lvl, col in [("CRITICAL","#cc1414"),("HIGH","#cc6400"),("ELEVATED","#cca000"),("MODERATE","#b4b400"),("LOW","#00a03c")]:
                sub = fdf[fdf["risk_level"] == lvl]
                if len(sub):
                    fig_sc.add_trace(go.Scatter(
                        x=sub["military_spending"],
                        y=sub["risk_score"],
                        mode="markers+text",
                        text=sub["country"],
                        textposition="top center",
                        textfont=dict(size=9, color=col),
                        marker=dict(color=col, size=9, line=dict(color="rgba(0,0,0,0.4)", width=1),
                                    symbol="circle"),
                        name=lvl,
                        showlegend=True,
                    ))
            fig_sc.update_layout(
                title=dict(text="MILITARY SPEND vs RISK SCORE", font=dict(color="#cc4400", size=12, family="Orbitron")),
                xaxis_title="Military Spending (% GDP)",
                yaxis_title="Risk Score",
                legend=dict(font=dict(color="#4a7a8a", size=10), bgcolor="rgba(0,0,0,0)"),
                **PLOTLY_LAYOUT,
            )
            st.plotly_chart(fig_sc, use_container_width=True)

    with col_d:
        # Feature importance from model
        fi = model.feature_importances
        labels_fi = [k.replace("_", " ").title() for k in fi.keys()]
        vals_fi   = list(fi.values())
        fig_fi = go.Figure(go.Pie(
            labels=labels_fi,
            values=vals_fi,
            hole=0.55,
            marker=dict(
                colors=["#cc0000","#cc6400","#0066aa","#008855"],
                line=dict(color="#030a0e", width=2),
            ),
            textfont=dict(family="Share Tech Mono", size=10, color="#ffffff"),
            textinfo="label+percent",
        ))
        fig_fi.update_layout(
            title=dict(text="MODEL FEATURE IMPORTANCE", font=dict(color="#cc4400", size=12, family="Orbitron")),
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
            font=dict(family="Share Tech Mono", color="#6a9ab0"),
            margin=dict(l=10, r=10, t=40, b=10),
            legend=dict(font=dict(color="#4a7a8a", size=10), bgcolor="rgba(0,0,0,0)"),
            annotations=[dict(text=f"MAE<br>{model.metrics.get('mae','—')}",
                              x=0.5, y=0.5, font_size=16,
                              font_color="#cc4400", font_family="Orbitron",
                              showarrow=False)],
        )
        st.plotly_chart(fig_fi, use_container_width=True)

    # ── Top 10 treemap
    st.markdown('<div class="section-title">◈ Threat Landscape Treemap</div>', unsafe_allow_html=True)
    top10 = fdf.nlargest(20, "risk_score")
    fig_tree = px.treemap(
        top10,
        path=["region","country"],
        values="risk_score",
        color="risk_score",
        color_continuous_scale=[[0,"#003020"],[0.3,"#505000"],[0.6,"#a03000"],[1.0,"#cc0000"]],
        hover_data={"risk_score":True},
    )
    fig_tree.update_layout(
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(family="Share Tech Mono", color="#c0d0d8"),
        margin=dict(l=0, r=0, t=10, b=0),
        coloraxis_showscale=False,
    )
    fig_tree.update_traces(
        textfont=dict(family="Rajdhani", size=13, color="#ffffff"),
        marker_line_color="#030a0e",
        marker_line_width=2,
    )
    st.plotly_chart(fig_tree, use_container_width=True, height=340)


# ─── TAB 4: SCENARIO SIMULATOR ────────────────────────────────────────────────

with tab4:
    st.markdown('<div class="section-title">◈ Conflict Risk Scenario Simulator</div>', unsafe_allow_html=True)

    col_sim, col_out = st.columns([1, 1], gap="large")

    with col_sim:
        st.markdown("""
        <div style="font-family:'Share Tech Mono',monospace; font-size:11px; color:#4a7a8a;
                    margin-bottom:16px; padding:10px; background:#050d12;
                    border-left:3px solid #cc4400; border-radius:2px;">
          Adjust geopolitical parameters to simulate conflict risk for a hypothetical
          scenario. The ML ensemble model outputs a calibrated threat score.
        </div>
        """, unsafe_allow_html=True)

        st.markdown('<div style="font-family:\'Share Tech Mono\',monospace; font-size:10px; color:#cc4400; letter-spacing:2px; margin-bottom:4px;">MILITARY SPENDING (% GDP)</div>', unsafe_allow_html=True)
        mil_spend = st.slider("Military Spending", 0.0, 25.0, 4.0, 0.1, label_visibility="collapsed")

        st.markdown('<div style="font-family:\'Share Tech Mono\',monospace; font-size:10px; color:#cc4400; letter-spacing:2px; margin-bottom:4px; margin-top:12px;">SANCTIONS INTENSITY (0 = None · 10 = Total)</div>', unsafe_allow_html=True)
        sanctions = st.slider("Sanctions", 0.0, 10.0, 3.0, 0.1, label_visibility="collapsed")

        st.markdown('<div style="font-family:\'Share Tech Mono\',monospace; font-size:10px; color:#cc4400; letter-spacing:2px; margin-bottom:4px; margin-top:12px;">TRADE DEPENDENCY (0 = Isolated · 10 = Integrated)</div>', unsafe_allow_html=True)
        trade_dep = st.slider("Trade Dependency", 0.0, 10.0, 5.5, 0.1, label_visibility="collapsed")

        st.markdown('<div style="font-family:\'Share Tech Mono\',monospace; font-size:10px; color:#cc4400; letter-spacing:2px; margin-bottom:4px; margin-top:12px;">DIPLOMATIC STABILITY (0 = Hostile · 10 = Stable)</div>', unsafe_allow_html=True)
        dip_stab = st.slider("Diplomatic Stability", 0.0, 10.0, 4.5, 0.1, label_visibility="collapsed")

        st.markdown('<div style="height:16px"></div>', unsafe_allow_html=True)

        run_btn = st.button("⚡  RUN THREAT ASSESSMENT")

    with col_out:
        if run_btn or True:  # auto-run on load
            result = model.predict(mil_spend, sanctions, trade_dep, dip_stab)
            score  = result["risk_score"]
            level  = result["risk_level"]
            color  = result["risk_level_color"]
            ci_lo, ci_hi = result["confidence_band"]

            st.markdown(f"""
            <div class="prediction-result">
              <div style="font-family:'Share Tech Mono',monospace; font-size:10px;
                          color:#4a7a8a; letter-spacing:2px; margin-bottom:12px;">
                THREAT ASSESSMENT OUTPUT
              </div>
              <div class="prediction-score" style="color:{color};">{score}</div>
              <div class="prediction-label" style="color:{color};">{level}</div>
              <div style="font-family:'Share Tech Mono',monospace; font-size:11px;
                          color:#4a7a8a; text-align:center; margin-top:8px;">
                95% CI: [{ci_lo} – {ci_hi}]
              </div>
              <hr style="border-color:#1a2a32; margin:16px 0;">
              <div style="font-family:'Share Tech Mono',monospace; font-size:10px;
                          color:#4a7a8a; letter-spacing:2px; margin-bottom:10px;">
                CONTRIBUTING FACTORS
              </div>
            """, unsafe_allow_html=True)

            # Factor bars
            for factor, pct in result["contributing_factors"].items():
                w = int(pct * 2)
                fcolor = "#cc0000" if pct > 35 else "#cc6400" if pct > 25 else "#cca000" if pct > 15 else "#4a7a8a"
                st.markdown(f"""
                <div style="margin-bottom:8px;">
                  <div style="display:flex; justify-content:space-between; margin-bottom:3px;">
                    <span style="font-family:'Share Tech Mono',monospace; font-size:10px; color:#6a9ab0;">{factor.upper()}</span>
                    <span style="font-family:'Share Tech Mono',monospace; font-size:10px; color:{fcolor};">{pct}%</span>
                  </div>
                  <div style="background:#0a1822; border-radius:2px; height:6px;">
                    <div style="background:{fcolor}; height:6px; width:{min(w,200)}px;
                                border-radius:2px; box-shadow:0 0 6px {fcolor}; max-width:100%;"></div>
                  </div>
                </div>
                """, unsafe_allow_html=True)

            st.markdown("</div>", unsafe_allow_html=True)

        # Sensitivity chart: vary one factor at a time
        st.markdown('<div class="section-title" style="margin-top:20px;">◈ Parameter Sensitivity Analysis</div>', unsafe_allow_html=True)

        sweep_vals = np.linspace(0, 10, 30)
        fig_sens = go.Figure()
        sens_params = [
            ("Sanctions",            sanctions,  trade_dep, dip_stab, "#cc0000"),
            ("Trade Dep.",           mil_spend,  sweep_vals,dip_stab, "#0066cc"),
            ("Diplomatic Stability", mil_spend,  trade_dep, sweep_vals,"#00aa44"),
        ]

        # Sanctions sweep (x = sanctions 0-10)
        sanc_scores = [model.predict(mil_spend, s, trade_dep, dip_stab)["risk_score"] for s in sweep_vals]
        fig_sens.add_trace(go.Scatter(x=sweep_vals, y=sanc_scores, name="Sanctions ↑",
            line=dict(color="#cc0000", width=2), mode="lines"))

        trade_scores = [model.predict(mil_spend, sanctions, t, dip_stab)["risk_score"] for t in sweep_vals]
        fig_sens.add_trace(go.Scatter(x=sweep_vals, y=trade_scores, name="Trade Dep ↑",
            line=dict(color="#0066cc", width=2, dash="dash"), mode="lines"))

        dip_scores = [model.predict(mil_spend, sanctions, trade_dep, d)["risk_score"] for d in sweep_vals]
        fig_sens.add_trace(go.Scatter(x=sweep_vals, y=dip_scores, name="Dip. Stability ↑",
            line=dict(color="#00aa44", width=2, dash="dot"), mode="lines"))

        fig_sens.add_hline(y=80, line_color="#cc0000", line_dash="dot", line_width=1,
                           annotation_text="CRITICAL", annotation_font_color="#cc0000",
                           annotation_font_size=9)
        fig_sens.add_hline(y=65, line_color="#cc6400", line_dash="dot", line_width=1,
                           annotation_text="HIGH", annotation_font_color="#cc6400",
                           annotation_font_size=9)

        fig_sens.update_layout(
            xaxis_title="Parameter Value (0–10)",
            yaxis_title="Predicted Risk Score",
            yaxis_range=[0, 100],
            legend=dict(font=dict(color="#4a7a8a", size=10, family="Share Tech Mono"),
                        bgcolor="rgba(0,0,0,0)"),
            **PLOTLY_LAYOUT,
        )
        st.plotly_chart(fig_sens, use_container_width=True)


# ═══════════════════════════════════════════════════════════════════════════════
#  FOOTER
# ═══════════════════════════════════════════════════════════════════════════════

st.markdown(f"""
<div style="margin-top:32px; border-top:1px solid #0a1822; padding:14px 0 4px 0;
            font-family:'Share Tech Mono',monospace; font-size:10px; color:#1a3a4a;
            text-align:center; letter-spacing:2px;">
  GLOBAL CONFLICT INTELLIGENCE DASHBOARD  ·  SYNTHETIC DEMO DATA  ·
  MODEL R²={model.metrics.get('r2','—')}  MAE={model.metrics.get('mae','—')}  ·
  NOT FOR OPERATIONAL USE
</div>
""", unsafe_allow_html=True)
