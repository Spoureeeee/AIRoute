"""
AIRoute v1 - Week 2 Map Visualisation
=======================================
What this does:
  1. Fetches real-time AQI from Malaysia DOE stations (same as Week 1)
  2. Scores all 3 routes using your formula
  3. Draws an interactive HTML map showing:
     - AQI station markers (colour-coded by pollution level)
     - 3 route lines (colour-coded by rank)
     - Clickable popups with AQI details on each marker
     - A legend explaining the colours

Output:
  airoute_map.html — open this in any browser (Chrome, Edge, Firefox)

Before running:
  - Make sure your AQICN token is correct (same as Week 1)
  - pip install folium (already done)

Run:
  python airoute_week2.py
"""

import requests
import folium
from folium import plugins

# ─────────────────────────────────────────────
# CONFIG — paste your token here
# ─────────────────────────────────────────────
AQICN_TOKEN = "cdf4c16ae293758ae972a69c3604402f38490461"

# ─────────────────────────────────────────────
# STATIONS — name, AQICN query, lat/lng for map
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
# ROUTES — waypoints as lat/lng coordinates
# These trace approximate road paths on the map
# ─────────────────────────────────────────────
ROUTES = [
    {
        "name":     "Route A — Via Putrajaya (Highway)",
        "time_min": 35,
        "dist_km":  30,
        "stations": ["Putrajaya", "KL Sentral"],
        "waypoints": [
            (2.9213, 101.6559),   # Cyberjaya start
            (2.9264, 101.6964),   # Putrajaya
            (3.0500, 101.7000),   # Mid highway
            (3.1319, 101.6841),   # KL Sentral
        ],
    },
    {
        "name":     "Route B — Via Petaling Jaya (Federal Highway)",
        "time_min": 50,
        "dist_km":  28,
        "stations": ["Putrajaya", "Petaling Jaya", "KL Sentral"],
        "waypoints": [
            (2.9213, 101.6559),   # Cyberjaya start
            (2.9264, 101.6964),   # Putrajaya area
            (3.1073, 101.6067),   # Petaling Jaya
            (3.1319, 101.6841),   # KL Sentral
        ],
    },
    {
        "name":     "Route C — Direct Highway (ELITE + KL)",
        "time_min": 40,
        "dist_km":  35,
        "stations": ["Putrajaya", "KL Sentral"],
        "waypoints": [
            (2.9213, 101.6559),   # Cyberjaya start
            (3.0200, 101.6700),   # ELITE highway mid
            (3.1000, 101.6750),   # Approaching KL
            (3.1319, 101.6841),   # KL Sentral
        ],
    },
]

# ─────────────────────────────────────────────
# WEIGHTS — same as Week 1
# ─────────────────────────────────────────────
WEIGHT_TIME = 0.33
WEIGHT_DIST = 0.33
WEIGHT_AQI  = 0.34


# ─────────────────────────────────────────────
# HELPER FUNCTIONS
# ─────────────────────────────────────────────
def fetch_aqi(query: str) -> float:
    url = f"https://api.waqi.info/feed/{query}/?token={AQICN_TOKEN}"
    try:
        response = requests.get(url, timeout=10)
        data = response.json()
        if data["status"] == "ok":
            return float(data["data"]["aqi"])
        return -1
    except:
        return -1


def aqi_color(aqi: float) -> str:
    """Returns a hex color based on AQI level."""
    if aqi <= 50:   return "#00e400"   # Green — Good
    if aqi <= 100:  return "#ffff00"   # Yellow — Moderate
    if aqi <= 150:  return "#ff7e00"   # Orange — Unhealthy
    if aqi <= 200:  return "#ff0000"   # Red — Very Unhealthy
    return "#7e0023"                   # Maroon — Hazardous


def aqi_label(aqi: float) -> str:
    if aqi <= 50:   return "Good"
    if aqi <= 100:  return "Moderate"
    if aqi <= 150:  return "Unhealthy"
    if aqi <= 200:  return "Very Unhealthy"
    return "Hazardous"


def route_color(rank: int) -> str:
    """Color for each route line by rank."""
    return ["#00c853", "#ff9800", "#f44336"][rank]  # Green, Orange, Red


def calculate_route_aqi(station_names, station_aqi_map):
    values = [station_aqi_map[s] for s in station_names if station_aqi_map.get(s, -1) != -1]
    return sum(values) / len(values) if values else 0


def score_route(time_min, dist_km, avg_aqi, T_max, D_max, AQI_max):
    return (
        WEIGHT_TIME * (time_min / T_max) +
        WEIGHT_DIST * (dist_km  / D_max) +
        WEIGHT_AQI  * (avg_aqi  / AQI_max)
    )


# ─────────────────────────────────────────────
# MAIN
# ─────────────────────────────────────────────
def main():
    print("\n╔══════════════════════════════════╗")
    print("║       AIRoute v1 — Week 2        ║")
    print("║   Building interactive map...    ║")
    print("╚══════════════════════════════════╝\n")

    # 1. Fetch AQI
    print("Fetching live AQI data...\n")
    station_aqi_map = {}
    for name, info in STATIONS.items():
        aqi = fetch_aqi(info["query"])
        station_aqi_map[name] = aqi
        status = f"AQI = {aqi} ({aqi_label(aqi)})" if aqi != -1 else "FAILED"
        print(f"  {name}: {status}")

    # 2. Score routes
    for route in ROUTES:
        route["avg_aqi"] = calculate_route_aqi(route["stations"], station_aqi_map)

    T_max   = max(r["time_min"] for r in ROUTES)
    D_max   = max(r["dist_km"]  for r in ROUTES)
    AQI_max = max(r["avg_aqi"]  for r in ROUTES) or 1

    for route in ROUTES:
        route["score"] = score_route(
            route["time_min"], route["dist_km"], route["avg_aqi"],
            T_max, D_max, AQI_max
        )

    ranked = sorted(ROUTES, key=lambda r: r["score"])
    rank_labels = ["🥇 HEALTHIEST", "🥈 2nd", "🥉 3rd"]

    print("\nRoute Rankings:")
    for i, r in enumerate(ranked):
        print(f"  {rank_labels[i]} — {r['name']} | AQI: {r['avg_aqi']:.0f} | Score: {r['score']:.4f}")

    # 3. Build Folium map
    # Centre on midpoint between Cyberjaya and KL
    m = folium.Map(
        location=[3.03, 101.67],
        zoom_start=12,
        tiles="CartoDB positron"   # Clean, minimal map style
    )

    # 4. Draw route lines (worst first so best renders on top)
    for i, route in enumerate(reversed(ranked)):
        rank = len(ranked) - 1 - i
        color = route_color(rank)
        label = rank_labels[rank]

        folium.PolyLine(
            locations=route["waypoints"],
            color=color,
            weight=5,
            opacity=0.8,
            tooltip=f"{label} | {route['name']} | Score: {route['score']:.4f}"
        ).add_to(m)

    # 5. Add AQI station markers
    for name, info in STATIONS.items():
        aqi = station_aqi_map.get(name, -1)
        color = aqi_color(aqi) if aqi != -1 else "#999999"
        label = aqi_label(aqi) if aqi != -1 else "No data"

        folium.CircleMarker(
            location=[info["lat"], info["lng"]],
            radius=18,
            color="#333333",
            weight=1.5,
            fill=True,
            fill_color=color,
            fill_opacity=0.9,
            tooltip=f"{name}",
            popup=folium.Popup(
                f"""
                <b>{name}</b><br>
                AQI: <b>{aqi:.0f}</b><br>
                Level: <b>{label}</b><br>
                <small>Source: Malaysia DOE via AQICN</small>
                """,
                max_width=200
            )
        ).add_to(m)

        # Station name label
        folium.Marker(
            location=[info["lat"] + 0.005, info["lng"]],
            icon=folium.DivIcon(
                html=f'<div style="font-size:11px;font-weight:bold;color:#333;white-space:nowrap;">{name}<br>AQI: {aqi:.0f}</div>',
                icon_size=(120, 30),
                icon_anchor=(0, 0)
            )
        ).add_to(m)

    # 6. Add start/end markers
    folium.Marker(
        location=[2.9213, 101.6559],
        popup="Start: Cyberjaya (MMU)",
        tooltip="📍 Start: Cyberjaya",
        icon=folium.Icon(color="blue", icon="home", prefix="fa")
    ).add_to(m)

    folium.Marker(
        location=[3.1319, 101.6841],
        popup="Destination: KL Sentral",
        tooltip="🏁 Destination: KL Sentral",
        icon=folium.Icon(color="red", icon="flag", prefix="fa")
    ).add_to(m)

    # 7. Add legend
    legend_html = """
    <div style="
        position: fixed; bottom: 30px; left: 30px; z-index: 1000;
        background: white; padding: 15px 20px; border-radius: 10px;
        box-shadow: 0 2px 10px rgba(0,0,0,0.2); font-family: Arial, sans-serif;
        font-size: 13px; min-width: 200px;">
        <b style="font-size:14px;">AIRoute v1</b><br>
        <small style="color:#666;">Cyberjaya → KL Sentral</small>
        <hr style="margin:8px 0;">
        <b>Routes</b><br>
        <span style="color:#00c853;">━━</span> 🥇 Healthiest Route<br>
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

    # 8. Save map
    output_file = "airoute_map.html"
    m.save(output_file)

    print(f"\n  ✅ Map saved as '{output_file}'")
    print("  Open it in your browser (double-click the file)\n")


if __name__ == "__main__":
    main()
