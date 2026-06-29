"""
AIRoute v1 - Week 1 Starter Code
=================================
What this does:
  1. Fetches real-time AQI data from AQICN API (Malaysia DOE stations)
  2. Defines 3 hardcoded routes: Cyberjaya -> KL Sentral
  3. Scores each route using YOUR formula from the poster
  4. Prints a ranked result table

Before running:
  - Get your FREE API token at: https://aqicn.org/data-platform/token/
  - Replace YOUR_TOKEN_HERE below with your actual token
  - Install dependencies: pip install requests tabulate

Run:
  python airoute_week1.py
"""

import requests
from tabulate import tabulate

# ─────────────────────────────────────────────
# CONFIG — replace with your real token
# ─────────────────────────────────────────────
AQICN_TOKEN = "cdf4c16ae293758ae972a69c3604402f38490461"

# ─────────────────────────────────────────────
# STEP 1: AQI STATIONS
# These are real DOE monitoring stations near Klang Valley.
# We assign each station to a zone along the route.
# ─────────────────────────────────────────────
STATIONS = {
    "Putrajaya":    "putrajaya",
    "Petaling Jaya":"petaling-jaya",
    "KL Sentral":   "kuala-lumpur",
}

def fetch_aqi(station_name: str) -> float:
    """
    Fetch real-time AQI for a given station name from AQICN.
    Returns AQI as a float, or -1 if the request fails.
    """
    url = f"https://api.waqi.info/feed/{station_name}/?token={AQICN_TOKEN}"
    try:
        response = requests.get(url, timeout=10)
        data = response.json()
        if data["status"] == "ok":
            aqi = data["data"]["aqi"]
            print(f"  [OK] {station_name}: AQI = {aqi}")
            return float(aqi)
        else:
            print(f"  [FAIL] {station_name}: {data['data']}")
            return -1
    except Exception as e:
        print(f"  [ERROR] {station_name}: {e}")
        return -1


# ─────────────────────────────────────────────
# STEP 2: ROUTE DEFINITIONS
# 3 routes from Cyberjaya to KL Sentral.
# Time (minutes) and distance (km) are realistic estimates.
# AQI stations list = stations you pass through on that route.
# ─────────────────────────────────────────────
ROUTES = [
    {
        "name":     "Route A — Via Putrajaya (Highway)",
        "time_min": 35,
        "dist_km":  30,
        "stations": ["Putrajaya", "KL Sentral"],
    },
    {
        "name":     "Route B — Via Petaling Jaya (Federal Highway)",
        "time_min": 50,
        "dist_km":  28,
        "stations": ["Putrajaya", "Petaling Jaya", "KL Sentral"],
    },
    {
        "name":     "Route C — Direct Highway (ELITE + KL)",
        "time_min": 40,
        "dist_km":  35,
        "stations": ["Cyberjaya", "KL Sentral"],
    },
]


# ─────────────────────────────────────────────
# STEP 3: ROUTE SCORE FORMULA
# Score = wT*(T/Tmax) + wD*(D/Dmax) + wA*(AQI/AQImax)
#
# Lower score = better route.
# Default weights: equal (0.33 each).
# AQI for a route = average AQI of all stations along it.
# ─────────────────────────────────────────────
WEIGHT_TIME = 0.33
WEIGHT_DIST = 0.33
WEIGHT_AQI  = 0.34   # slightly heavier — health is the point


def calculate_route_aqi(station_names: list, station_aqi_map: dict) -> float:
    """Average AQI across all stations on this route."""
    values = [station_aqi_map[s] for s in station_names if station_aqi_map.get(s, -1) != -1]
    return sum(values) / len(values) if values else 0


def score_route(time_min, dist_km, avg_aqi, T_max, D_max, AQI_max) -> float:
    """
    Lower = better.
    Normalises each metric against the worst value across all routes.
    """
    return (
        WEIGHT_TIME * (time_min / T_max) +
        WEIGHT_DIST * (dist_km  / D_max) +
        WEIGHT_AQI  * (avg_aqi  / AQI_max)
    )


def aqi_label(aqi: float) -> str:
    """Malaysia API colour bands (DOE standard)."""
    if aqi <= 50:   return "Good 🟢"
    if aqi <= 100:  return "Moderate 🟡"
    if aqi <= 150:  return "Unhealthy 🟠"
    if aqi <= 200:  return "Very Unhealthy 🔴"
    return "Hazardous ☠️"


# ─────────────────────────────────────────────
# STEP 4: MAIN — fetch, score, rank, print
# ─────────────────────────────────────────────
def main():
    print("\n╔══════════════════════════════════╗")
    print("║        AIRoute v1 — Week 1       ║")
    print("║  Cyberjaya → KL Sentral          ║")
    print("╚══════════════════════════════════╝\n")

    # Fetch AQI for all unique stations
    print("Fetching live AQI data from Malaysia DOE stations...\n")
    station_aqi_map = {}
    for label, query in STATIONS.items():
        station_aqi_map[label] = fetch_aqi(query)

    print()

    # Compute per-route AQI
    for route in ROUTES:
        route["avg_aqi"] = calculate_route_aqi(route["stations"], station_aqi_map)

    # Find max values for normalisation
    T_max   = max(r["time_min"] for r in ROUTES)
    D_max   = max(r["dist_km"]  for r in ROUTES)
    AQI_max = max(r["avg_aqi"]  for r in ROUTES) or 1  # avoid div/0

    # Score every route
    for route in ROUTES:
        route["score"] = score_route(
            route["time_min"],
            route["dist_km"],
            route["avg_aqi"],
            T_max, D_max, AQI_max
        )

    # Sort by score (ascending = better)
    ranked = sorted(ROUTES, key=lambda r: r["score"])

    # Build display table
    table = []
    for i, r in enumerate(ranked):
        rank_label = ["🥇 HEALTHIEST", "🥈 2nd", "🥉 3rd"][i] if i < 3 else str(i+1)
        table.append([
            rank_label,
            r["name"],
            f"{r['time_min']} min",
            f"{r['dist_km']} km",
            f"{r['avg_aqi']:.0f}  ({aqi_label(r['avg_aqi'])})",
            f"{r['score']:.4f}",
        ])

    headers = ["Rank", "Route", "Time", "Distance", "Avg AQI", "Score (lower=better)"]
    print(tabulate(table, headers=headers, tablefmt="rounded_outline"))

    print(f"\n  Weights used → Time: {WEIGHT_TIME} | Distance: {WEIGHT_DIST} | AQI: {WEIGHT_AQI}")
    print("  Formula: Score = wT×(T/Tmax) + wD×(D/Dmax) + wA×(AQI/AQImax)\n")
    print("  ✅ Week 1 complete. Next: add map visualisation with Folium.\n")


if __name__ == "__main__":
    main()
