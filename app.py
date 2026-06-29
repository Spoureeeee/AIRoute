"""
AIRoute v1 - Week 3 Streamlit Dashboard
=========================================
What this does:
  - Full web app: user selects origin + destination
  - Fetches live AQI from Malaysia DOE stations
  - Scores and ranks routes using your formula
  - Displays ranked results + interactive Folium map
  - User can adjust weights via sliders

Run:
  streamlit run app.py

Then open http://localhost:8501 in your browser.
"""

import requests
import folium
import streamlit as st
from streamlit.components.v1 import html as st_html

# ─────────────────────────────────────────────
# CONFIG
# ─────────────────────────────────────────────
AQICN_TOKEN = "cdf4c16ae293758ae972a69c3604402f38490461"

# ─────────────────────────────────────────────
# STATIONS
# ─────────────────────────────────────────────
STATIONS = {
    "Putrajaya": {
        "query": "putrajaya",
        "lat": 2.9264,
        "lng": 101.6964,
    },
    "Petaling Jaya": {
        "query": "petaling-jaya",
        "lat": 3.1073,
        "lng": 101.6067,
    },
    "KL Sentral": {
        "query": "kuala-lumpur",
        "lat": 3.1319,
        "lng": 101.6841,
    },
}

# ─────────────────────────────────────────────
# ROUTES
# ─────────────────────────────────────────────
ROUTES = [
    {
        "name":      "Route A — Via Putrajaya (Highway)",
        "time_min":  35,
        "dist_km":   30,
        "stations":  ["Putrajaya", "KL Sentral"],
        "waypoints": [
            (2.9213, 101.6559),
            (2.9264, 101.6964),
            (3.0500, 101.7000),
            (3.1319, 101.6841),
        ],
    },
    {
        "name":      "Route B — Via Petaling Jaya (Federal Highway)",
        "time_min":  50,
        "dist_km":   28,
        "stations":  ["Putrajaya", "Petaling Jaya", "KL Sentral"],
        "waypoints": [
            (2.9213, 101.6559),
            (2.9264, 101.6964),
            (3.1073, 101.6067),
            (3.1319, 101.6841),
        ],
    },
    {
        "name":      "Route C — Direct Highway (ELITE + KL)",
        "time_min":  40,
        "dist_km":   35,
        "stations":  ["Putrajaya", "KL Sentral"],
        "waypoints": [
            (2.9213, 101.6559),
            (3.0200, 101.6700),
            (3.1000, 101.6750),
            (3.1319, 101.6841),
        ],
    },
]

# ─────────────────────────────────────────────
# HELPER FUNCTIONS
# ─────────────────────────────────────────────
@st.cache_data(ttl=1800)   # Cache AQI for 30 minutes
def fetch_all_aqi():
    result = {}
    for name, info in STATIONS.items():
        url = f"https://api.waqi.info/feed/{info['query']}/?token={AQICN_TOKEN}"
        try:
            resp = requests.get(url, timeout=10)
            data = resp.json()
            result[name] = float(data["data"]["aqi"]) if data["status"] == "ok" else -1
        except:
            result[name] = -1
    return result


def aqi_color(aqi):
    if aqi <= 50:  return "#00e400"
    if aqi <= 100: return "#ffff00"
    if aqi <= 150: return "#ff7e00"
    if aqi <= 200: return "#ff0000"
    return "#7e0023"


def aqi_label(aqi):
    if aqi <= 50:  return "Good 🟢"
    if aqi <= 100: return "Moderate 🟡"
    if aqi <= 150: return "Unhealthy 🟠"
    if aqi <= 200: return "Very Unhealthy 🔴"
    return "Hazardous ☠️"


def route_color(rank):
    return ["#00c853", "#ff9800", "#f44336"][rank]


def calculate_route_aqi(station_names, station_aqi_map):
    values = [station_aqi_map[s] for s in station_names if station_aqi_map.get(s, -1) != -1]
    return sum(values) / len(values) if values else 0


def score_route(time_min, dist_km, avg_aqi, T_max, D_max, AQI_max, wT, wD, wA):
    return (
        wT * (time_min / T_max) +
        wD * (dist_km  / D_max) +
        wA * (avg_aqi  / AQI_max)
    )


def build_map(ranked, station_aqi_map):
    m = folium.Map(location=[3.03, 101.67], zoom_start=12, tiles="CartoDB positron")
    rank_labels = ["🥇 Healthiest", "🥈 2nd Best", "🥉 3rd Best"]

    for i, route in enumerate(reversed(ranked)):
        rank = len(ranked) - 1 - i
        folium.PolyLine(
            locations=route["waypoints"],
            color=route_color(rank),
            weight=5,
            opacity=0.85,
            tooltip=f"{rank_labels[rank]} | {route['name']}"
        ).add_to(m)

    for name, info in STATIONS.items():
        aqi = station_aqi_map.get(name, -1)
        folium.CircleMarker(
            location=[info["lat"], info["lng"]],
            radius=18,
            color="#333",
            weight=1.5,
            fill=True,
            fill_color=aqi_color(aqi) if aqi != -1 else "#999",
            fill_opacity=0.9,
            tooltip=f"{name}: AQI {aqi:.0f}",
            popup=folium.Popup(
                f"<b>{name}</b><br>AQI: <b>{aqi:.0f}</b><br>{aqi_label(aqi)}<br><small>Malaysia DOE via AQICN</small>",
                max_width=200
            )
        ).add_to(m)

        folium.Marker(
            location=[info["lat"] + 0.005, info["lng"]],
            icon=folium.DivIcon(
                html=f'<div style="font-size:11px;font-weight:bold;color:#333;white-space:nowrap;">{name}<br>AQI: {aqi:.0f}</div>',
                icon_size=(120, 30), icon_anchor=(0, 0)
            )
        ).add_to(m)

    folium.Marker(
        location=[2.9213, 101.6559],
        tooltip="📍 Start: Cyberjaya (MMU)",
        icon=folium.Icon(color="blue", icon="home", prefix="fa")
    ).add_to(m)

    folium.Marker(
        location=[3.1319, 101.6841],
        tooltip="🏁 Destination: KL Sentral",
        icon=folium.Icon(color="red", icon="flag", prefix="fa")
    ).add_to(m)

    return m._repr_html_()


# ─────────────────────────────────────────────
# STREAMLIT UI
# ─────────────────────────────────────────────
st.set_page_config(
    page_title="AIRoute — Health-Aware Navigation",
    page_icon="🛣️",
    layout="wide"
)

st.title("🛣️ AIRoute v1")
st.caption("Health-aware route optimization using real-time Malaysia DOE air quality data")
st.divider()

# Sidebar — controls
with st.sidebar:
    st.header("⚙️ Settings")

    st.subheader("Route")
    origin = st.selectbox("Origin", ["Cyberjaya (MMU)"])
    destination = st.selectbox("Destination", ["KL Sentral"])

    st.subheader("Priority Weights")
    st.caption("Adjust to match your preference. Values are normalised automatically.")
    wT = st.slider("⏱️ Time", 0.0, 1.0, 0.33, 0.01)
    wD = st.slider("📏 Distance", 0.0, 1.0, 0.33, 0.01)
    wA = st.slider("🫁 Air Quality (AQI)", 0.0, 1.0, 0.34, 0.01)

    # Normalise weights so they always sum to 1
    total = wT + wD + wA or 1
    wT, wD, wA = wT/total, wD/total, wA/total

    st.caption(f"Normalised → Time: {wT:.2f} | Distance: {wD:.2f} | AQI: {wA:.2f}")

    if st.button("🔄 Refresh AQI Data"):
        st.cache_data.clear()
        st.rerun()

    st.divider()
    st.caption("Data refreshes every 30 minutes automatically.")
    st.caption("Source: Malaysia DOE APIMS via AQICN")

# Fetch AQI
with st.spinner("Fetching live AQI from Malaysia DOE stations..."):
    station_aqi_map = fetch_all_aqi()

# Score routes
for route in ROUTES:
    route["avg_aqi"] = calculate_route_aqi(route["stations"], station_aqi_map)

T_max   = max(r["time_min"] for r in ROUTES)
D_max   = max(r["dist_km"]  for r in ROUTES)
AQI_max = max(r["avg_aqi"]  for r in ROUTES) or 1

for route in ROUTES:
    route["score"] = score_route(
        route["time_min"], route["dist_km"], route["avg_aqi"],
        T_max, D_max, AQI_max, wT, wD, wA
    )

ranked = sorted(ROUTES, key=lambda r: r["score"])
rank_labels = ["🥇 Healthiest Route", "🥈 2nd Best", "🥉 3rd Best"]
rank_colors = ["#e8f5e9", "#fff8e1", "#ffebee"]

# Layout — two columns
col1, col2 = st.columns([1, 1.8])

with col1:
    st.subheader("📊 Live AQI — Stations")
    for name, aqi in station_aqi_map.items():
        if aqi != -1:
            st.metric(label=name, value=f"AQI {aqi:.0f}", delta=aqi_label(aqi), delta_color="off")
        else:
            st.metric(label=name, value="No data")

    st.divider()
    st.subheader("🏆 Route Rankings")

    for i, route in enumerate(ranked):
        with st.container():
            st.markdown(
                f"""
                <div style="background:{rank_colors[i]};padding:12px 16px;
                border-radius:10px;margin-bottom:10px;">
                <b>{rank_labels[i]}</b><br>
                {route['name']}<br>
                <small>
                ⏱️ {route['time_min']} min &nbsp;|&nbsp;
                📏 {route['dist_km']} km &nbsp;|&nbsp;
                🫁 AQI {route['avg_aqi']:.0f} ({aqi_label(route['avg_aqi'])})<br>
                Score: <b>{route['score']:.4f}</b>
                </small>
                </div>
                """,
                unsafe_allow_html=True
            )

    st.divider()
    st.subheader("📐 Formula")
    st.latex(r"Score = w_T \frac{T}{T_{max}} + w_D \frac{D}{D_{max}} + w_A \frac{AQI}{AQI_{max}}")
    st.caption("Lower score = better route. Weights are set in the sidebar.")

with col2:
    st.subheader("🗺️ Interactive Map")
    st.caption("Click station markers for AQI details. Hover routes for rankings.")
    map_html = build_map(ranked, station_aqi_map)
    st_html(map_html, height=520)

st.divider()
st.caption("AIRoute v1 — Built by Aflin Airil | MMU Cyberjaya | YTM Future Leaders Scholar | github.com/Spoureeeee/AIRoute")
