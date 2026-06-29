"""
AIRoute v1.1 - Real Road Routing with OpenRouteService
=======================================================
Upgrades from v1:
  - Real road-based routes via OpenRouteService API
  - Actual travel time and distance from live routing engine
  - Route lines follow real roads on the map (not straight lines)

Run:
  streamlit run app.py
"""

import requests
import folium
import streamlit as st
from streamlit.components.v1 import html as st_html
import openrouteservice

# ─────────────────────────────────────────────
# CONFIG
# ─────────────────────────────────────────────
AQICN_TOKEN = "cdf4c16ae293758ae972a69c3604402f38490461"
ORS_TOKEN   = "eyJvcmciOiI1YjNjZTM1OTc4NTExMTAwMDFjZjYyNDgiLCJpZCI6IjQxOTQwNjU0OGEzMjQxMTNhMGM5ZDhkZTI2MWNkZDFlIiwiaCI6Im11cm11cjY0In0="

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
# ROUTE DEFINITIONS
# ORS uses (longitude, latitude) order
# ─────────────────────────────────────────────
CYBERJAYA  = (101.6559, 2.9213)
KL_SENTRAL = (101.6841, 3.1319)

ROUTE_CONFIGS = [
    {
        "name":      "Route A — Via Putrajaya (Highway)",
        "stations":  ["Putrajaya", "KL Sentral"],
        "waypoints": [CYBERJAYA, (101.6964, 2.9264), KL_SENTRAL],
    },
    {
        "name":      "Route B — Via Petaling Jaya (Federal Highway)",
        "stations":  ["Putrajaya", "Petaling Jaya", "KL Sentral"],
        "waypoints": [CYBERJAYA, (101.6964, 2.9264), (101.6067, 3.1073), KL_SENTRAL],
    },
    {
        "name":      "Route C — Direct Highway (ELITE + KL)",
        "stations":  ["Putrajaya", "KL Sentral"],
        "waypoints": [CYBERJAYA, (101.6700, 3.0200), KL_SENTRAL],
    },
]


# ─────────────────────────────────────────────
# HELPER FUNCTIONS
# ─────────────────────────────────────────────
@st.cache_data(ttl=1800)
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


@st.cache_data(ttl=3600)
def fetch_real_routes():
    client = openrouteservice.Client(key=ORS_TOKEN)
    routes = []

    for config in ROUTE_CONFIGS:
        try:
            result = client.directions(
                coordinates=config["waypoints"],
                profile="driving-car",
                format="geojson",
            )
            feature  = result["features"][0]
            props    = feature["properties"]["segments"]
            geometry = feature["geometry"]["coordinates"]

            total_time_min = sum(s["duration"] for s in props) / 60
            total_dist_km  = sum(s["distance"] for s in props) / 1000
            folium_coords  = [(pt[1], pt[0]) for pt in geometry]

            routes.append({
                "name":     config["name"],
                "stations": config["stations"],
                "time_min": round(total_time_min, 1),
                "dist_km":  round(total_dist_km, 1),
                "geometry": folium_coords,
            })

        except Exception as e:
            st.warning(f"ORS failed for {config['name']}: {e}. Using fallback.")
            routes.append({
                "name":     config["name"],
                "stations": config["stations"],
                "time_min": 35.0,
                "dist_km":  30.0,
                "geometry": [(pt[1], pt[0]) for pt in config["waypoints"]],
            })

    return routes


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
            locations=route["geometry"],
            color=route_color(rank),
            weight=5,
            opacity=0.85,
            tooltip=f"{rank_labels[rank]} | {route['name']} | {route['time_min']} min | {route['dist_km']} km"
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

    legend_html = """
    <div style="position:fixed;bottom:30px;left:30px;z-index:1000;
    background:white;padding:15px 20px;border-radius:10px;
    box-shadow:0 2px 10px rgba(0,0,0,0.2);font-family:Arial,sans-serif;
    font-size:13px;min-width:200px;">
        <b style="font-size:14px;">AIRoute v1.1</b><br>
        <small style="color:#666;">Real road routing via ORS</small>
        <hr style="margin:8px 0;">
        <b>Routes</b><br>
        <span style="color:#00c853;">━━</span> 🥇 Healthiest<br>
        <span style="color:#ff9800;">━━</span> 🥈 2nd Best<br>
        <span style="color:#f44336;">━━</span> 🥉 3rd Best<br>
        <hr style="margin:8px 0;">
        <b>AQI Levels</b><br>
        <span style="color:#00e400;">●</span> Good (0–50)<br>
        <span style="color:#cccc00;">●</span> Moderate (51–100)<br>
        <span style="color:#ff7e00;">●</span> Unhealthy (101–150)<br>
        <span style="color:#ff0000;">●</span> Very Unhealthy (151–200)<br>
        <hr style="margin:8px 0;">
        <small style="color:#999;">Data: Malaysia DOE via AQICN</small>
    </div>
    """
    m.get_root().html.add_child(folium.Element(legend_html))
    return m._repr_html_()


# ─────────────────────────────────────────────
# STREAMLIT UI
# ─────────────────────────────────────────────
st.set_page_config(
    page_title="AIRoute — Health-Aware Navigation",
    page_icon="🛣️",
    layout="wide"
)

st.title("🛣️ AIRoute v1.1")
st.caption("Health-aware route optimization · Real-time Malaysia DOE air quality · Real road routing via OpenRouteService")
st.divider()

with st.sidebar:
    st.header("⚙️ Settings")
    st.subheader("Route")
    origin      = st.selectbox("Origin", ["Cyberjaya (MMU)"])
    destination = st.selectbox("Destination", ["KL Sentral"])

    st.subheader("Priority Weights")
    st.caption("Adjust to match your preference. Normalised automatically.")
    wT = st.slider("⏱️ Time", 0.0, 1.0, 0.33, 0.01)
    wD = st.slider("📏 Distance", 0.0, 1.0, 0.33, 0.01)
    wA = st.slider("🫁 Air Quality (AQI)", 0.0, 1.0, 0.34, 0.01)

    total = wT + wD + wA or 1
    wT, wD, wA = wT/total, wD/total, wA/total
    st.caption(f"Normalised → Time: {wT:.2f} | Distance: {wD:.2f} | AQI: {wA:.2f}")

    if st.button("🔄 Refresh AQI Data"):
        st.cache_data.clear()
        st.rerun()

    st.divider()
    st.caption("AQI refreshes every 30 min. Routes cached 1 hour.")
    st.caption("Source: Malaysia DOE APIMS via AQICN")

with st.spinner("Fetching live AQI and real road routes..."):
    station_aqi_map = fetch_all_aqi()
    routes          = fetch_real_routes()

for route in routes:
    route["avg_aqi"] = calculate_route_aqi(route["stations"], station_aqi_map)

T_max   = max(r["time_min"] for r in routes)
D_max   = max(r["dist_km"]  for r in routes)
AQI_max = max(r["avg_aqi"]  for r in routes) or 1

for route in routes:
    route["score"] = score_route(
        route["time_min"], route["dist_km"], route["avg_aqi"],
        T_max, D_max, AQI_max, wT, wD, wA
    )

ranked      = sorted(routes, key=lambda r: r["score"])
rank_labels = ["🥇 Healthiest Route", "🥈 2nd Best", "🥉 3rd Best"]
rank_colors = ["#e8f5e9", "#fff8e1", "#ffebee"]

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
        st.markdown(
            f"""
            <div style="background:{rank_colors[i]};padding:12px 16px;
            border-radius:10px;margin-bottom:10px;color:#111111;">
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
    st.caption("Lower score = better route. Weights normalised to sum to 1.")

with col2:
    st.subheader("🗺️ Interactive Map")
    st.caption("Routes follow real roads. Click markers for AQI details. Hover routes for info.")
    map_html = build_map(ranked, station_aqi_map)
    st_html(map_html, height=520)

st.divider()
st.caption("AIRoute v1.1 — Built by Aflin Airil | MMU Cyberjaya | YTM Future Leaders Scholar | github.com/Spoureeeee/AIRoute")
