"""
app.py  ─  Global Conflict Intelligence Dashboard  v2.0
---------------------------------------------------------
Upgrades over v1:
  🌍  3D rotating Earth       (globe.gl via Streamlit HTML component)
  🚀  Animated missile arcs   (PyDeck ArcLayer from top-risk zones)
  📡  Satellite-style map     (Carto dark basemap — free, no token)
  📰  Live geopolitical news  (BBC / Reuters / Al Jazeera via feedparser RSS)
"""

import json
import pandas as pd
import numpy as np
import streamlit as st
import pydeck as pdk
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime
import feedparser

from conflict_model import get_model

# ═══════════════════════════════════════════════════════════════════════════════
#  PAGE CONFIG
# ═══════════════════════════════════════════════════════════════════════════════

st.set_page_config(
    page_title="Global Conflict Intelligence",
    page_icon="🛰️",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ═══════════════════════════════════════════════════════════════════════════════
#  GLOBAL CSS
# ═══════════════════════════════════════════════════════════════════════════════

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Share+Tech+Mono&family=Rajdhani:wght@300;400;500;600;700&family=Orbitron:wght@400;700;900&display=swap');

html, body, [class*="css"] {
    background-color: #030a0e !important;
    color: #c8d8e0 !important;
    font-family: 'Rajdhani', sans-serif !important;
}
.stApp { background: #030a0e; }
section[data-testid="stSidebar"] { background: #050d12 !important; border-right: 1px solid #0f2733; }
section[data-testid="stSidebar"] * { color: #8ab4c0 !important; }
#MainMenu, footer, header { visibility: hidden; }
::-webkit-scrollbar { width: 4px; }
::-webkit-scrollbar-track { background: #030a0e; }
::-webkit-scrollbar-thumb { background: #1a3a4a; border-radius: 2px; }

.cia-header {
    background: linear-gradient(90deg, #000d14 0%, #051520 40%, #000d14 100%);
    border-top: 2px solid #cc0000; border-bottom: 1px solid #0f2733;
    padding: 18px 32px; display: flex; align-items: center; justify-content: space-between;
}
.cia-header-title {
    font-family: 'Orbitron', monospace; font-size: 22px; font-weight: 900;
    color: #ff2200; letter-spacing: 4px; text-transform: uppercase;
    text-shadow: 0 0 20px rgba(255,34,0,0.6), 0 0 40px rgba(255,34,0,0.2);
}
.cia-header-sub { font-family: 'Share Tech Mono', monospace; font-size: 11px; color: #4a7a8a; letter-spacing: 2px; margin-top: 4px; }
.cia-header-time { font-family: 'Share Tech Mono', monospace; font-size: 13px; color: #cc4400; text-align: right; }

.metric-card {
    background: linear-gradient(135deg, #070f14 0%, #0a1a22 100%);
    border: 1px solid #0f2733; border-left: 3px solid #cc0000;
    border-radius: 4px; padding: 16px 20px; margin: 4px 0;
}
.metric-label { font-family: 'Share Tech Mono', monospace; font-size: 10px; color: #4a7a8a; letter-spacing: 2px; text-transform: uppercase; margin-bottom: 6px; }
.metric-value { font-family: 'Orbitron', monospace; font-size: 28px; font-weight: 700; color: #ff2200; text-shadow: 0 0 12px rgba(255,34,0,0.5); line-height: 1; }
.metric-delta { font-family: 'Share Tech Mono', monospace; font-size: 11px; color: #4a7a8a; margin-top: 4px; }

.section-title {
    font-family: 'Orbitron', monospace; font-size: 13px; font-weight: 700;
    color: #cc4400; letter-spacing: 3px; text-transform: uppercase;
    border-bottom: 1px solid #0f2733; padding-bottom: 8px; margin: 20px 0 14px 0;
}
.intel-panel { background: #070f14; border: 1px solid #0f2733; border-radius: 4px; padding: 16px; }

.risk-badge { display: inline-block; padding: 3px 10px; border-radius: 2px; font-family: 'Share Tech Mono', monospace; font-size: 11px; font-weight: 700; letter-spacing: 1px; }
.risk-critical { background: rgba(200,0,0,0.2);   color: #ff2200; border: 1px solid #cc0000; }
.risk-high     { background: rgba(200,80,0,0.2);  color: #ff6600; border: 1px solid #cc4400; }
.risk-elevated { background: rgba(200,140,0,0.2); color: #ffaa00; border: 1px solid #cc8800; }
.risk-moderate { background: rgba(180,180,0,0.2); color: #dddd00; border: 1px solid #aaaa00; }
.risk-low      { background: rgba(0,160,0,0.2);   color: #00cc44; border: 1px solid #008833; }

.stSlider > div > div > div > div { background: #cc0000 !important; }
.stButton > button {
    background: linear-gradient(135deg, #200000, #3a0000) !important;
    color: #ff4444 !important; border: 1px solid #660000 !important;
    border-radius: 2px !important; font-family: 'Orbitron', monospace !important;
    font-size: 11px !important; letter-spacing: 2px !important; padding: 8px 20px !important;
}
.stButton > button:hover { background: linear-gradient(135deg, #3a0000, #600000) !important; border-color: #cc0000 !important; color: #ff0000 !important; }
.stTabs [data-baseweb="tab-list"] { background: #050d12; border-bottom: 1px solid #0f2733; }
.stTabs [data-baseweb="tab"] { font-family: 'Orbitron', monospace !important; font-size: 11px !important; letter-spacing: 2px; color: #4a7a8a !important; }
.stTabs [aria-selected="true"] { color: #ff2200 !important; border-bottom: 2px solid #cc0000 !important; }

.news-ticker-wrap { background: #050d12; border: 1px solid #0f2733; border-left: 3px solid #cc0000; border-radius: 4px; overflow: hidden; margin: 8px 0; }
.news-item { padding: 10px 16px; border-bottom: 1px solid #0a1a22; display: flex; gap: 12px; align-items: flex-start; }
.news-item:last-child { border-bottom: none; }
.news-source { font-family: 'Share Tech Mono', monospace; font-size: 10px; color: #cc4400; letter-spacing: 1px; white-space: nowrap; padding-top: 2px; min-width: 70px; }
.news-title { font-family: 'Rajdhani', sans-serif; font-size: 14px; color: #c8d8e0; line-height: 1.4; }
.news-title a { color: #c8d8e0; text-decoration: none; }
.news-title a:hover { color: #ff6644; }
.news-time { font-family: 'Share Tech Mono', monospace; font-size: 10px; color: #2a4a5a; white-space: nowrap; padding-top: 2px; }

.prediction-result { background: linear-gradient(135deg, #0a0005, #12000a); border: 1px solid #330011; border-left: 4px solid #cc0000; border-radius: 4px; padding: 20px; margin-top: 12px; }
.prediction-score { font-family: 'Orbitron', monospace; font-size: 56px; font-weight: 900; text-align: center; text-shadow: 0 0 30px currentColor; line-height: 1; }
.prediction-label { font-family: 'Share Tech Mono', monospace; font-size: 13px; letter-spacing: 3px; text-align: center; margin-top: 6px; }
.sidebar-section { font-family: 'Orbitron', monospace; font-size: 10px; color: #cc4400; letter-spacing: 2px; text-transform: uppercase; margin: 16px 0 8px 0; border-bottom: 1px solid #0f2733; padding-bottom: 4px; }
.scanlines { position: fixed; top: 0; left: 0; right: 0; bottom: 0; background: repeating-linear-gradient(0deg, transparent, transparent 2px, rgba(0,255,80,0.012) 2px, rgba(0,255,80,0.012) 4px); pointer-events: none; z-index: 9999; }
</style>
<div class="scanlines"></div>
""", unsafe_allow_html=True)


# ═══════════════════════════════════════════════════════════════════════════════
#  DATA & MODEL
# ═══════════════════════════════════════════════════════════════════════════════

@st.cache_data
def load_data() -> pd.DataFrame:
    df = pd.read_csv("dataset.csv")
    df["risk_score"] = pd.to_numeric(df["risk_score"], errors="coerce").fillna(50)
    df["latitude"]   = pd.to_numeric(df["latitude"],   errors="coerce")
    df["longitude"]  = pd.to_numeric(df["longitude"],  errors="coerce")
    return df.dropna(subset=["latitude","longitude"])

@st.cache_resource
def load_model():
    return get_model("dataset.csv")

df    = load_data()
model = load_model()

def risk_class(s):
    if s >= 80: return "CRITICAL"
    if s >= 65: return "HIGH"
    if s >= 45: return "ELEVATED"
    if s >= 25: return "MODERATE"
    return "LOW"

def risk_color(s):
    if s >= 80: return [220, 20, 20, 230]
    if s >= 65: return [220,100,  0, 210]
    if s >= 45: return [220,160,  0, 190]
    if s >= 25: return [180,180,  0, 170]
    return              [  0,160, 60, 150]

def risk_hex(s):
    if s >= 80: return "#cc1414"
    if s >= 65: return "#cc6400"
    if s >= 45: return "#cca000"
    if s >= 25: return "#b4b400"
    return "#00a03c"

df["risk_level"] = df["risk_score"].apply(risk_class)
df["color"]      = df["risk_score"].apply(risk_color)
df["risk_hex"]   = df["risk_score"].apply(risk_hex)
df["radius"]     = df["risk_score"].apply(lambda s: int(80000 + s * 6000))


# ═══════════════════════════════════════════════════════════════════════════════
#  RSS LIVE NEWS
# ═══════════════════════════════════════════════════════════════════════════════

RSS_FEEDS = {
    "BBC":     "http://feeds.bbci.co.uk/news/world/rss.xml",
    "Reuters": "https://feeds.reuters.com/reuters/worldNews",
    "AlJaz":   "https://www.aljazeera.com/xml/rss/all.xml",
}

CONFLICT_KEYWORDS = [
    "war","conflict","attack","missile","military","troops","sanction",
    "crisis","bomb","strike","invasion","ceasefire","nato","nuclear",
    "rebel","coup","protest","refugee","siege","airstrike","tension",
    "violence","terror","hostage","offensive","withdrawal","peacekeeping",
]

@st.cache_data(ttl=900)
def fetch_news(max_per_feed: int = 8) -> list:
    articles = []
    for source, url in RSS_FEEDS.items():
        try:
            feed  = feedparser.parse(url)
            count = 0
            for entry in feed.entries:
                if count >= max_per_feed:
                    break
                title   = entry.get("title", "")
                summary = entry.get("summary", "")
                link    = entry.get("link", "#")
                pub     = entry.get("published", "")
                text    = (title + " " + summary).lower()
                relevant = any(kw in text for kw in CONFLICT_KEYWORDS)
                articles.append({
                    "source":   source,
                    "title":    title,
                    "link":     link,
                    "pub":      pub[:16] if pub else "",
                    "relevant": relevant,
                })
                count += 1
        except Exception:
            pass
    articles.sort(key=lambda x: (not x["relevant"], 0))
    return articles


# ═══════════════════════════════════════════════════════════════════════════════
#  MISSILE ARC DATA
# ═══════════════════════════════════════════════════════════════════════════════

STRATEGIC_TARGETS = [
    (51.5074, -0.1278, "London"),
    (48.8566,  2.3522, "Paris"),
    (55.7558, 37.6173, "Moscow"),
    (39.9042,116.4074, "Beijing"),
    (38.9072,-77.0369, "Washington"),
    (35.6762,139.6503, "Tokyo"),
    (28.6139, 77.2090, "New Delhi"),
    (41.9028, 12.4964, "Rome"),
    (-33.868,151.2093, "Sydney"),
]

def build_arc_data(df: pd.DataFrame, top_n: int = 12) -> pd.DataFrame:
    top  = df.nlargest(top_n, "risk_score")
    rng  = np.random.default_rng(42)
    arcs = []
    for _, row in top.iterrows():
        risk   = float(row["risk_score"])
        chosen = rng.choice(len(STRATEGIC_TARGETS), size=min(2, len(STRATEGIC_TARGETS)), replace=False)
        for idx in chosen:
            tlat, tlon, tname = STRATEGIC_TARGETS[idx]
            arcs.append({
                "source_lat":  float(row["latitude"]),
                "source_lon":  float(row["longitude"]),
                "target_lat":  tlat,
                "target_lon":  tlon,
                "source_name": str(row["country"]),
                "target_name": tname,
                "risk_score":  risk,
                "color":       [220,20,20,180]  if risk >= 80 else
                               [220,100,0,150]  if risk >= 65 else
                               [180,140,0,120],
                "width":       max(1, int(risk / 22)),
            })
    return pd.DataFrame(arcs)


# ═══════════════════════════════════════════════════════════════════════════════
#  SIDEBAR
# ═══════════════════════════════════════════════════════════════════════════════

with st.sidebar:
    st.markdown("""
    <div style="text-align:center;padding:12px 0 8px 0;">
      <div style="font-family:'Orbitron',monospace;font-size:14px;color:#cc0000;
                  letter-spacing:3px;text-shadow:0 0 10px rgba(204,0,0,0.5);">◈ GCID v2.0 ◈</div>
      <div style="font-family:'Share Tech Mono',monospace;font-size:10px;color:#2a4a5a;
                  margin-top:4px;letter-spacing:1px;">CLASSIFICATION: RESTRICTED</div>
    </div>""", unsafe_allow_html=True)
    st.divider()

    st.markdown('<div class="sidebar-section">▸ Data Filters</div>', unsafe_allow_html=True)
    risk_filter   = st.multiselect("Risk Level", ["CRITICAL","HIGH","ELEVATED","MODERATE","LOW"],
                                   default=["CRITICAL","HIGH","ELEVATED","MODERATE","LOW"])
    region_opts   = sorted(df["region"].unique().tolist())
    region_filter = st.multiselect("Region", region_opts, default=region_opts)
    score_range   = st.slider("Risk Score Range", 0, 100, (0, 100))

    st.markdown('<div class="sidebar-section">▸ Map Settings</div>', unsafe_allow_html=True)
    map_pitch  = st.slider("Map Pitch", 0, 60, 45)
    show_arcs  = st.toggle("🚀 Missile Trajectories", value=True)
    arc_top_n  = st.slider("# Trajectory Sources", 4, 20, 10)

    st.markdown('<div class="sidebar-section">▸ Globe Settings</div>', unsafe_allow_html=True)
    globe_autorotate = st.toggle("🌍 Auto-Rotate Globe", value=True)
    globe_speed      = st.slider("Rotation Speed", 0.1, 2.0, 0.5, 0.1)

    st.divider()
    st.markdown(f"""
    <div style="font-family:'Share Tech Mono',monospace;font-size:10px;color:#1a3a4a;text-align:center;">
      ACTIVE NODES: {len(df)}<br>MODEL: GB-ENSEMBLE v2.4<br>
      STATUS: <span style="color:#00cc44;">ONLINE</span>
    </div>""", unsafe_allow_html=True)


# ─── APPLY FILTERS ─────────────────────────────────────────────────────────────

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
    <div class="cia-header-sub">GEOPOLITICAL THREAT ASSESSMENT SYSTEM  ·  v2.0  ·  CLASSIFICATION: RESTRICTED</div>
  </div>
  <div class="cia-header-time">
    <div style="font-size:16px;color:#cc0000;font-family:'Orbitron',monospace;">{now[:10]}</div>
    <div style="font-size:12px;margin-top:2px;">{now[11:]}</div>
    <div style="font-size:10px;margin-top:4px;color:#2a4a5a;letter-spacing:1px;">LIVE FEED</div>
  </div>
</div>""", unsafe_allow_html=True)

st.markdown('<div style="height:14px"></div>', unsafe_allow_html=True)


# ═══════════════════════════════════════════════════════════════════════════════
#  METRICS ROW
# ═══════════════════════════════════════════════════════════════════════════════

critical_n = int((fdf["risk_score"] >= 80).sum())
high_n     = int(((fdf["risk_score"] >= 65) & (fdf["risk_score"] < 80)).sum())
avg_risk   = round(float(fdf["risk_score"].mean()), 1) if len(fdf) else 0
hottest    = fdf.loc[fdf["risk_score"].idxmax(), "country"] if len(fdf) else "—"

c1, c2, c3, c4 = st.columns(4)
metrics = [
    (c1, "◈ Zones Monitored",  str(len(fdf)),   f"of {len(df)} total indexed"),
    (c2, "⚠ Critical Zones",   str(critical_n), f"{high_n} HIGH  ·  risk ≥ 80"),
    (c3, "◈ Global Avg Risk",  str(avg_risk),   "composite threat  /  100"),
    (c4, "◈ Highest Threat",   hottest,         "primary watch zone"),
]
for col, label, val, sub in metrics:
    with col:
        fs = "28px" if len(str(val)) < 7 else "16px"
        st.markdown(f"""
        <div class="metric-card">
          <div class="metric-label">{label}</div>
          <div class="metric-value" style="font-size:{fs};">{val}</div>
          <div class="metric-delta">{sub}</div>
        </div>""", unsafe_allow_html=True)


# ═══════════════════════════════════════════════════════════════════════════════
#  TABS
# ═══════════════════════════════════════════════════════════════════════════════

tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
    "🌍  3D GLOBE",
    "📡  SATELLITE MAP",
    "◈  HOTSPOT RANKING",
    "◈  ANALYTICS",
    "◈  SCENARIO SIMULATOR",
    "📰  LIVE INTEL FEED",
])


# ─────────────────────────────────────────────────────────────────────────────
#  TAB 1 · 3D ROTATING EARTH
# ─────────────────────────────────────────────────────────────────────────────

with tab1:
    st.markdown('<div class="section-title">🌍 3D Rotating Earth — Live Conflict Overlay</div>', unsafe_allow_html=True)

    # Build JSON point data for globe.gl
    points_js = []
    for _, row in fdf.iterrows():
        risk = float(row["risk_score"])
        color = (
            "rgba(220,20,20,0.95)"  if risk >= 80 else
            "rgba(220,100,0,0.9)"   if risk >= 65 else
            "rgba(200,150,0,0.85)"  if risk >= 45 else
            "rgba(160,160,0,0.75)"  if risk >= 25 else
            "rgba(0,160,60,0.7)"
        )
        points_js.append({
            "lat":      round(float(row["latitude"]),  4),
            "lng":      round(float(row["longitude"]), 4),
            "label":    str(row["country"]),
            "region":   str(row["region"]),
            "risk":     risk,
            "level":    str(row["risk_level"]),
            "color":    color,
            "altitude": round(risk / 800, 4),
            "radius":   round(0.35 + risk / 38, 2),
        })

    points_json   = json.dumps(points_js)
    autorotate_js = "true" if globe_autorotate else "false"
    speed_val     = globe_speed

    globe_html = f"""<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<style>
  * {{ margin:0; padding:0; box-sizing:border-box; }}
  body {{ background:#030a0e; overflow:hidden; }}
  #globeViz {{ width:100%; height:580px; }}
  #legend {{
    position:absolute; bottom:14px; left:14px;
    background:rgba(5,13,18,0.85); border:1px solid #0f2733;
    border-radius:4px; padding:8px 12px;
    font-size:10px; color:#4a7a8a;
    font-family:'Share Tech Mono',monospace; letter-spacing:1px;
    pointer-events:none;
  }}
  .dot {{ display:inline-block; width:10px; height:10px; border-radius:50%; margin-right:5px; vertical-align:middle; }}
</style>
</head>
<body>
<div style="position:relative;">
  <div id="globeViz"></div>
  <div id="legend">
    <span class="dot" style="background:#dc1414;box-shadow:0 0 6px #dc1414;"></span>CRITICAL ≥80 &nbsp;
    <span class="dot" style="background:#dc6400;box-shadow:0 0 6px #dc6400;"></span>HIGH 65–79 &nbsp;
    <span class="dot" style="background:#dca000;box-shadow:0 0 6px #dca000;"></span>ELEVATED 45–64 &nbsp;
    <span class="dot" style="background:#b4b400;box-shadow:0 0 4px #b4b400;"></span>MODERATE &nbsp;
    <span class="dot" style="background:#00a03c;box-shadow:0 0 4px #00a03c;"></span>LOW
  </div>
</div>

<script src="https://unpkg.com/globe.gl@2.30.0/dist/globe.gl.min.js"></script>
<script>
const POINTS        = {points_json};
const AUTO_ROTATE   = {autorotate_js};
const ROTATE_SPEED  = {speed_val};

const el = document.getElementById('globeViz');

const globe = Globe()(el)
  .globeImageUrl('https://unpkg.com/three-globe/example/img/earth-night.jpg')
  .bumpImageUrl('https://unpkg.com/three-globe/example/img/earth-topology.png')
  .backgroundImageUrl('https://unpkg.com/three-globe/example/img/night-sky.png')
  .atmosphereColor('rgba(80,0,0,0.4)')
  .atmosphereAltitude(0.18)
  .pointsData(POINTS)
  .pointLat('lat')
  .pointLng('lng')
  .pointAltitude('altitude')
  .pointRadius('radius')
  .pointColor('color')
  .pointResolution(16)
  .pointLabel(d =>
    `<div style="background:rgba(5,13,18,0.95);border:1px solid #cc0000;border-radius:4px;
                 padding:8px 12px;font-family:'Share Tech Mono',monospace;font-size:12px;
                 min-width:160px;">
       <div style="color:#ff2200;font-size:14px;font-weight:bold;margin-bottom:4px;">${{d.label}}</div>
       <div style="color:#4a7a8a;font-size:10px;margin-bottom:6px;">${{d.region}}</div>
       <div style="display:flex;justify-content:space-between;">
         <span style="color:#ffaa00;">RISK ${{d.risk}}</span>
         <span style="color:#cc4400;">${{d.level}}</span>
       </div>
     </div>`
  )
  .width(el.clientWidth || 900)
  .height(580);

globe.controls().autoRotate      = AUTO_ROTATE;
globe.controls().autoRotateSpeed = ROTATE_SPEED;
globe.controls().enableZoom      = true;
globe.pointOfView({{ lat: 20, lng: 10, altitude: 2.2 }}, 0);

window.addEventListener('resize', () => {{
  globe.width(el.clientWidth);
}});
</script>
</body>
</html>"""

    st.components.v1.html(globe_html, height=595, scrolling=False)
    st.caption("🖱️ Drag to rotate  ·  Scroll to zoom  ·  Hover for intel  ·  Toggle auto-rotate in sidebar")


# ─────────────────────────────────────────────────────────────────────────────
#  TAB 2 · SATELLITE MAP + MISSILE TRAJECTORIES
# ─────────────────────────────────────────────────────────────────────────────

with tab2:
    st.markdown('<div class="section-title">📡 Satellite Surveillance Map — Threat Trajectories</div>', unsafe_allow_html=True)

    if len(fdf) == 0:
        st.warning("No data matches current filters.")
    else:
        # Glow halo
        halo_df = fdf.copy()
        halo_df["halo_color"]  = halo_df["risk_score"].apply(
            lambda s: [220,20,20,30]  if s >= 80 else
                      [220,100,0,22]  if s >= 65 else
                      [180,140,0,18]  if s >= 45 else [0,140,40,14])
        halo_df["halo_radius"] = halo_df["risk_score"].apply(lambda s: int(130000 + s * 9500))

        layers = [
            pdk.Layer("ScatterplotLayer", data=halo_df,
                get_position=["longitude","latitude"], get_radius="halo_radius",
                get_fill_color="halo_color", pickable=False, opacity=1.0),
            pdk.Layer("ScatterplotLayer", data=fdf,
                get_position=["longitude","latitude"], get_radius="radius",
                get_fill_color="color", pickable=True, opacity=0.88,
                stroked=True, get_line_color=[255,255,255,40], line_width_min_pixels=1),
            pdk.Layer("TextLayer", data=fdf[fdf["risk_score"] >= 70].copy(),
                get_position=["longitude","latitude"], get_text="country",
                get_size=14, get_color=[255,100,80,220], get_angle=0,
                get_alignment_baseline="'bottom'", get_pixel_offset=[0,-20],
                font_family="'Share Tech Mono'"),
        ]

        if show_arcs:
            arc_df = build_arc_data(fdf, top_n=arc_top_n)
            if len(arc_df):
                layers.append(pdk.Layer(
                    "ArcLayer", data=arc_df,
                    get_source_position=["source_lon","source_lat"],
                    get_target_position=["target_lon","target_lat"],
                    get_source_color="color",
                    get_target_color=[255, 60, 0, 200],
                    get_width="width",
                    pickable=True, auto_highlight=True,
                ))

        tooltip = {
            "html": """
            <div style="background:#050d12;border:1px solid #cc0000;border-radius:4px;
                        padding:10px 14px;font-family:'Share Tech Mono',monospace;">
              <div style="color:#ff2200;font-size:13px;font-weight:bold;">{country}</div>
              <div style="color:#4a7a8a;font-size:10px;margin:2px 0;">{region}</div>
              <hr style="border-color:#0f2733;margin:6px 0;">
              <div style="color:#cc8800;">RISK: <span style="color:#ffaa00">{risk_score}</span></div>
              <div style="color:#4a7a8a;">{risk_level}</div>
            </div>""",
            "style": {"backgroundColor":"transparent","border":"none"},
        }

        deck = pdk.Deck(
            layers=layers,
            initial_view_state=pdk.ViewState(latitude=20, longitude=10, zoom=1.5,
                                             pitch=map_pitch, bearing=0),
            # Carto dark-matter: free satellite-adjacent dark basemap, no token needed
            map_style="https://basemaps.cartocdn.com/gl/dark-matter-gl-style/style.json",
            tooltip=tooltip,
        )
        st.pydeck_chart(deck, use_container_width=True, height=530)

        if show_arcs:
            arc_df_count = build_arc_data(fdf, top_n=arc_top_n)
            st.markdown(f"""
            <div style="font-family:'Share Tech Mono',monospace;font-size:11px;color:#4a7a8a;
                        padding:8px 4px;display:flex;gap:24px;">
              <span style="color:#cc0000;">🚀</span>
              <span>{len(arc_df_count)} projected trajectories from top-{arc_top_n} threat zones</span>
              <span style="color:#cc4400;">Arc width = risk intensity</span>
            </div>""", unsafe_allow_html=True)

        st.markdown("""
        <div style="display:flex;gap:20px;padding:4px;
                    font-family:'Share Tech Mono',monospace;font-size:11px;color:#4a7a8a;">
          <span>🔴 CRITICAL ≥80</span><span>🟠 HIGH 65–79</span>
          <span>🟡 ELEVATED 45–64</span><span>🟢 LOW &lt;45</span>
        </div>""", unsafe_allow_html=True)


# ─────────────────────────────────────────────────────────────────────────────
#  TAB 3 · HOTSPOT RANKING
# ─────────────────────────────────────────────────────────────────────────────

with tab3:
    st.markdown('<div class="section-title">◈ Conflict Hotspot Intelligence Ranking</div>', unsafe_allow_html=True)
    ranked = fdf.sort_values("risk_score", ascending=False).reset_index(drop=True)
    ranked.index += 1

    rows_html = ""
    for rank, row in ranked.iterrows():
        lvl = row["risk_level"].lower()
        sc  = row["risk_score"]
        color = risk_hex(sc)
        w = int(sc / 100 * 120)
        rows_html += f"""
        <tr style="border-bottom:1px solid #0a1822;">
          <td style="color:#4a7a8a;font-family:'Share Tech Mono',monospace;padding:8px 12px;font-size:12px;">#{rank:02d}</td>
          <td style="color:#e0eef5;font-family:'Rajdhani',sans-serif;font-weight:600;padding:8px 12px;">{row['country']}</td>
          <td style="color:#4a7a8a;font-family:'Share Tech Mono',monospace;padding:8px 12px;font-size:11px;">{row['region']}</td>
          <td style="padding:8px 12px;">
            <div style="background:#0a1a22;border-radius:2px;height:10px;width:120px;display:inline-block;vertical-align:middle;">
              <div style="background:{color};height:10px;width:{w}px;border-radius:2px;box-shadow:0 0 6px {color};"></div>
            </div>
            <span style="font-family:'Share Tech Mono',monospace;font-size:11px;color:{color};margin-left:6px;">{sc:.0f}</span>
          </td>
          <td style="padding:8px 12px;"><span class="risk-badge risk-{lvl}">{row['risk_level']}</span></td>
          <td style="color:#6a9ab0;font-family:'Share Tech Mono',monospace;padding:8px 12px;font-size:11px;">{row.get('active_conflicts','—')}</td>
          <td style="color:#6a9ab0;font-family:'Share Tech Mono',monospace;padding:8px 12px;font-size:11px;">{float(row.get('military_spending',0)):.1f}%</td>
        </tr>"""

    st.markdown(f"""
    <div class="intel-panel" style="overflow-x:auto;">
    <table style="width:100%;border-collapse:collapse;">
      <thead>
        <tr style="border-bottom:2px solid #cc0000;">
          <th style="color:#cc4400;font-family:'Share Tech Mono',monospace;font-size:10px;letter-spacing:2px;padding:10px 12px;text-align:left;">RANK</th>
          <th style="color:#cc4400;font-family:'Share Tech Mono',monospace;font-size:10px;letter-spacing:2px;padding:10px 12px;text-align:left;">NATION</th>
          <th style="color:#cc4400;font-family:'Share Tech Mono',monospace;font-size:10px;letter-spacing:2px;padding:10px 12px;text-align:left;">REGION</th>
          <th style="color:#cc4400;font-family:'Share Tech Mono',monospace;font-size:10px;letter-spacing:2px;padding:10px 12px;text-align:left;">RISK INDEX</th>
          <th style="color:#cc4400;font-family:'Share Tech Mono',monospace;font-size:10px;letter-spacing:2px;padding:10px 12px;text-align:left;">LEVEL</th>
          <th style="color:#cc4400;font-family:'Share Tech Mono',monospace;font-size:10px;letter-spacing:2px;padding:10px 12px;text-align:left;">CONFLICTS</th>
          <th style="color:#cc4400;font-family:'Share Tech Mono',monospace;font-size:10px;letter-spacing:2px;padding:10px 12px;text-align:left;">MIL. SPEND</th>
        </tr>
      </thead>
      <tbody>{rows_html}</tbody>
    </table></div>""", unsafe_allow_html=True)


# ─────────────────────────────────────────────────────────────────────────────
#  TAB 4 · ANALYTICS
# ─────────────────────────────────────────────────────────────────────────────

with tab4:
    st.markdown('<div class="section-title">◈ Geopolitical Analytics Intelligence</div>', unsafe_allow_html=True)

    PL = dict(
        paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="#070f14",
        font=dict(family="Share Tech Mono", color="#6a9ab0", size=11),
        margin=dict(l=40, r=20, t=40, b=40),
        xaxis=dict(gridcolor="#0a1822", linecolor="#0f2733", tickfont=dict(color="#4a7a8a")),
        yaxis=dict(gridcolor="#0a1822", linecolor="#0f2733", tickfont=dict(color="#4a7a8a")),
    )

    ca, cb = st.columns(2)
    with ca:
        bins_b = [0,25,45,65,80,100]; labs_b = ["LOW","MODERATE","ELEVATED","HIGH","CRITICAL"]
        cols_b = ["#00a03c","#b4b400","#cca000","#cc6400","#cc1414"]
        fig = go.Figure()
        for i in range(len(bins_b)-1):
            sub = fdf[(fdf["risk_score"] >= bins_b[i]) & (fdf["risk_score"] < bins_b[i+1])]
            fig.add_trace(go.Bar(x=[labs_b[i]], y=[len(sub)], marker_color=cols_b[i], showlegend=False))
        fig.update_layout(title=dict(text="THREAT LEVEL DISTRIBUTION", font=dict(color="#cc4400",size=12,family="Orbitron")), **PL)
        st.plotly_chart(fig, use_container_width=True)

    with cb:
        reg = fdf.groupby("region")["risk_score"].mean().sort_values(ascending=True).reset_index()
        fig2 = go.Figure(go.Bar(x=reg["risk_score"], y=reg["region"], orientation="h",
            marker=dict(color=reg["risk_score"],
                colorscale=[[0,"#004020"],[0.4,"#6a6a00"],[0.7,"#aa4400"],[1.0,"#cc0000"]]),
            text=reg["risk_score"].round(1), textposition="outside",
            textfont=dict(color="#cc8800",size=10,family="Share Tech Mono")))
        fig2.update_layout(title=dict(text="AVERAGE RISK BY REGION", font=dict(color="#cc4400",size=12,family="Orbitron")), **PL)
        st.plotly_chart(fig2, use_container_width=True)

    cc, cd = st.columns(2)
    with cc:
        fig3 = go.Figure()
        for lvl, col in [("CRITICAL","#cc1414"),("HIGH","#cc6400"),("ELEVATED","#cca000"),("MODERATE","#b4b400"),("LOW","#00a03c")]:
            sub = fdf[fdf["risk_level"] == lvl]
            if len(sub):
                fig3.add_trace(go.Scatter(x=sub["military_spending"], y=sub["risk_score"],
                    mode="markers+text", text=sub["country"], textposition="top center",
                    textfont=dict(size=9,color=col),
                    marker=dict(color=col,size=9), name=lvl, showlegend=True))
        fig3.update_layout(title=dict(text="MILITARY SPEND vs RISK", font=dict(color="#cc4400",size=12,family="Orbitron")),
            xaxis_title="Military Spending (% GDP)", yaxis_title="Risk Score",
            legend=dict(font=dict(color="#4a7a8a",size=10),bgcolor="rgba(0,0,0,0)"), **PL)
        st.plotly_chart(fig3, use_container_width=True)

    with cd:
        fi = model.feature_importances
        fig4 = go.Figure(go.Pie(
            labels=[k.replace("_"," ").title() for k in fi], values=list(fi.values()), hole=0.55,
            marker=dict(colors=["#cc0000","#cc6400","#0066aa","#008855"],line=dict(color="#030a0e",width=2)),
            textfont=dict(family="Share Tech Mono",size=10,color="#ffffff"), textinfo="label+percent"))
        fig4.update_layout(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
            font=dict(family="Share Tech Mono",color="#6a9ab0"), margin=dict(l=10,r=10,t=40,b=10),
            title=dict(text="MODEL FEATURE IMPORTANCE", font=dict(color="#cc4400",size=12,family="Orbitron")),
            legend=dict(font=dict(color="#4a7a8a",size=10),bgcolor="rgba(0,0,0,0)"),
            annotations=[dict(text=f"MAE<br>{model.metrics.get('mae','—')}",x=0.5,y=0.5,
                font_size=16,font_color="#cc4400",font_family="Orbitron",showarrow=False)])
        st.plotly_chart(fig4, use_container_width=True)

    st.markdown('<div class="section-title">◈ Threat Landscape Treemap</div>', unsafe_allow_html=True)
    fig5 = px.treemap(fdf.nlargest(20,"risk_score"), path=["region","country"],
        values="risk_score", color="risk_score",
        color_continuous_scale=[[0,"#003020"],[0.3,"#505000"],[0.6,"#a03000"],[1.0,"#cc0000"]])
    fig5.update_layout(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
        font=dict(family="Share Tech Mono",color="#c0d0d8"), margin=dict(l=0,r=0,t=10,b=0),
        coloraxis_showscale=False)
    fig5.update_traces(textfont=dict(family="Rajdhani",size=13,color="#ffffff"),
        marker_line_color="#030a0e", marker_line_width=2)
    st.plotly_chart(fig5, use_container_width=True, height=340)


# ─────────────────────────────────────────────────────────────────────────────
#  TAB 5 · SCENARIO SIMULATOR
# ─────────────────────────────────────────────────────────────────────────────

with tab5:
    st.markdown('<div class="section-title">◈ Conflict Risk Scenario Simulator</div>', unsafe_allow_html=True)
    col_sim, col_out = st.columns([1,1], gap="large")

    with col_sim:
        st.markdown("""
        <div style="font-family:'Share Tech Mono',monospace;font-size:11px;color:#4a7a8a;
                    margin-bottom:16px;padding:10px;background:#050d12;
                    border-left:3px solid #cc4400;border-radius:2px;">
          Adjust parameters to simulate conflict risk. ML ensemble outputs
          a calibrated score with 95% confidence interval.
        </div>""", unsafe_allow_html=True)

        for label, key, lo, hi, default in [
            ("MILITARY SPENDING (% GDP)",                          "mil",   0.0, 25.0, 4.0),
            ("SANCTIONS INTENSITY  (0 = None · 10 = Total)",       "sanc",  0.0, 10.0, 3.0),
            ("TRADE DEPENDENCY  (0 = Isolated · 10 = Integrated)", "trade", 0.0, 10.0, 5.5),
            ("DIPLOMATIC STABILITY  (0 = Hostile · 10 = Stable)",  "dip",   0.0, 10.0, 4.5),
        ]:
            st.markdown(f'<div style="font-family:\'Share Tech Mono\',monospace;font-size:10px;color:#cc4400;letter-spacing:2px;margin:12px 0 4px 0;">{label}</div>', unsafe_allow_html=True)
            st.slider(label, lo, hi, default, 0.1, label_visibility="collapsed", key=key)

        st.button("⚡  RUN THREAT ASSESSMENT")

    with col_out:
        result = model.predict(st.session_state.mil, st.session_state.sanc,
                               st.session_state.trade, st.session_state.dip)
        score  = result["risk_score"]
        level  = result["risk_level"]
        color  = result["risk_level_color"]
        ci_lo, ci_hi = result["confidence_band"]

        st.markdown(f"""
        <div class="prediction-result">
          <div style="font-family:'Share Tech Mono',monospace;font-size:10px;color:#4a7a8a;letter-spacing:2px;margin-bottom:12px;">THREAT ASSESSMENT OUTPUT</div>
          <div class="prediction-score" style="color:{color};">{score}</div>
          <div class="prediction-label" style="color:{color};">{level}</div>
          <div style="font-family:'Share Tech Mono',monospace;font-size:11px;color:#4a7a8a;text-align:center;margin-top:8px;">95% CI: [{ci_lo} – {ci_hi}]</div>
          <hr style="border-color:#1a2a32;margin:16px 0;">
          <div style="font-family:'Share Tech Mono',monospace;font-size:10px;color:#4a7a8a;letter-spacing:2px;margin-bottom:10px;">CONTRIBUTING FACTORS</div>
        """, unsafe_allow_html=True)

        for factor, pct in result["contributing_factors"].items():
            fc = "#cc0000" if pct > 35 else "#cc6400" if pct > 25 else "#cca000" if pct > 15 else "#4a7a8a"
            st.markdown(f"""
            <div style="margin-bottom:8px;">
              <div style="display:flex;justify-content:space-between;margin-bottom:3px;">
                <span style="font-family:'Share Tech Mono',monospace;font-size:10px;color:#6a9ab0;">{factor.upper()}</span>
                <span style="font-family:'Share Tech Mono',monospace;font-size:10px;color:{fc};">{pct}%</span>
              </div>
              <div style="background:#0a1822;border-radius:2px;height:6px;">
                <div style="background:{fc};height:6px;width:{min(int(pct*2),200)}px;border-radius:2px;box-shadow:0 0 6px {fc};"></div>
              </div>
            </div>""", unsafe_allow_html=True)

        st.markdown("</div>", unsafe_allow_html=True)

        # Sensitivity chart
        sv = np.linspace(0, 10, 25)
        fig_s = go.Figure()
        PL_s = dict(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="#070f14",
            font=dict(family="Share Tech Mono",color="#6a9ab0",size=11),
            margin=dict(l=40,r=20,t=30,b=40),
            xaxis=dict(gridcolor="#0a1822",linecolor="#0f2733",tickfont=dict(color="#4a7a8a")),
            yaxis=dict(gridcolor="#0a1822",linecolor="#0f2733",tickfont=dict(color="#4a7a8a")))
        fig_s.add_trace(go.Scatter(x=sv,
            y=[model.predict(st.session_state.mil,s,st.session_state.trade,st.session_state.dip)["risk_score"] for s in sv],
            name="Sanctions ↑", line=dict(color="#cc0000",width=2)))
        fig_s.add_trace(go.Scatter(x=sv,
            y=[model.predict(st.session_state.mil,st.session_state.sanc,t,st.session_state.dip)["risk_score"] for t in sv],
            name="Trade Dep ↑", line=dict(color="#0066cc",width=2,dash="dash")))
        fig_s.add_trace(go.Scatter(x=sv,
            y=[model.predict(st.session_state.mil,st.session_state.sanc,st.session_state.trade,d)["risk_score"] for d in sv],
            name="Dip. Stability ↑", line=dict(color="#00aa44",width=2,dash="dot")))
        fig_s.add_hline(y=80,line_color="#cc0000",line_dash="dot",line_width=1,
            annotation_text="CRITICAL",annotation_font_color="#cc0000",annotation_font_size=9)
        fig_s.add_hline(y=65,line_color="#cc6400",line_dash="dot",line_width=1,
            annotation_text="HIGH",annotation_font_color="#cc6400",annotation_font_size=9)
        fig_s.update_layout(xaxis_title="Parameter Value",yaxis_title="Predicted Risk",yaxis_range=[0,100],
            legend=dict(font=dict(color="#4a7a8a",size=10,family="Share Tech Mono"),bgcolor="rgba(0,0,0,0)"),
            **PL_s)
        st.markdown('<div class="section-title" style="margin-top:20px;">◈ Parameter Sensitivity</div>', unsafe_allow_html=True)
        st.plotly_chart(fig_s, use_container_width=True)


# ─────────────────────────────────────────────────────────────────────────────
#  TAB 6 · LIVE INTEL FEED
# ─────────────────────────────────────────────────────────────────────────────

with tab6:
    st.markdown('<div class="section-title">📰 Live Geopolitical Intelligence Feed</div>', unsafe_allow_html=True)

    col_feed, col_meta = st.columns([3, 1])

    with col_meta:
        st.markdown("""<div class="intel-panel">
          <div style="font-family:'Share Tech Mono',monospace;font-size:10px;color:#cc4400;letter-spacing:2px;margin-bottom:10px;">FEED SOURCES</div>
        """, unsafe_allow_html=True)
        for src, url in RSS_FEEDS.items():
            st.markdown(f"""
          <div style="margin-bottom:8px;padding:6px 8px;background:#0a1822;border-radius:2px;border-left:2px solid #cc4400;">
            <div style="font-family:'Orbitron',monospace;font-size:11px;color:#ff6644;">{src}</div>
            <div style="font-family:'Share Tech Mono',monospace;font-size:9px;color:#2a4a5a;margin-top:2px;">{url[:38]}…</div>
          </div>""", unsafe_allow_html=True)
        st.markdown("""
          <div style="font-family:'Share Tech Mono',monospace;font-size:10px;color:#2a4a5a;margin-top:8px;">
            CACHE: 15 min<br>KEYWORDS: conflict / war / military…
          </div></div>""", unsafe_allow_html=True)
        if st.button("🔄  REFRESH FEED"):
            st.cache_data.clear()
            st.rerun()

    with col_feed:
        with st.spinner("Fetching live intelligence feeds…"):
            articles = fetch_news(max_per_feed=8)

        if not articles:
            st.markdown("""
            <div style="background:#070f14;border:1px solid #0f2733;border-left:3px solid #cc4400;
                        border-radius:4px;padding:20px;font-family:'Share Tech Mono',monospace;
                        font-size:12px;color:#4a7a8a;">
              ⚠ Unable to reach RSS feeds in current environment.<br><br>
              Live news will display automatically when deployed on Streamlit Cloud.
              The app fetches from BBC World, Reuters, and Al Jazeera every 15 minutes.
            </div>""", unsafe_allow_html=True)
        else:
            relevant = [a for a in articles if a["relevant"]]
            if relevant:
                st.markdown(f"""
                <div style="font-family:'Share Tech Mono',monospace;font-size:10px;color:#cc4400;
                            letter-spacing:2px;margin-bottom:8px;">
                  ⚠ {len(relevant)} CONFLICT-RELEVANT ARTICLES DETECTED
                </div>""", unsafe_allow_html=True)

            items_html = ""
            for a in articles:
                hl = "border-left:3px solid #cc0000;" if a["relevant"] else ""
                items_html += f"""
                <div class="news-item" style="{hl}">
                  <div class="news-source">{a['source']}</div>
                  <div class="news-title"><a href="{a['link']}" target="_blank">{a['title']}</a></div>
                  <div class="news-time">{a['pub']}</div>
                </div>"""

            st.markdown(f'<div class="news-ticker-wrap">{items_html}</div>', unsafe_allow_html=True)
            st.caption(f"{len(articles)} articles retrieved  ·  cached 15 min  ·  {now}")


# ═══════════════════════════════════════════════════════════════════════════════
#  FOOTER
# ═══════════════════════════════════════════════════════════════════════════════

st.markdown(f"""
<div style="margin-top:32px;border-top:1px solid #0a1822;padding:14px 0 4px 0;
            font-family:'Share Tech Mono',monospace;font-size:10px;color:#1a3a4a;
            text-align:center;letter-spacing:2px;">
  GLOBAL CONFLICT INTELLIGENCE DASHBOARD v2.0  ·  SYNTHETIC DEMO DATA  ·
  MODEL R²={model.metrics.get('r2','—')}  MAE={model.metrics.get('mae','—')}  ·  NOT FOR OPERATIONAL USE
</div>""", unsafe_allow_html=True)
