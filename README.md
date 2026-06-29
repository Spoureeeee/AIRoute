# 🛣️ AIRoute v1
### Health-Aware Route Optimization Using Real-Time Air Quality Data

> *Why navigate around traffic when you can navigate around pollution?*

AIRoute scores road routes using a weighted formula that balances **travel time**, **distance**, and **real-time air quality index (AQI)** — giving you the healthiest route, not just the fastest one.

---

## 🎯 The Problem

Existing navigation apps (Waze, Google Maps) optimize for time and distance. None of them account for air quality exposure along the route — a real public health concern in Malaysia's urban corridors, where PM2.5 and NO2 levels regularly spike during haze season and peak traffic hours.

AIRoute fills that gap.

---

## 🔬 How It Works

AIRoute scores each route using this formula (from the original STEM project poster - Air Quality Monitoring System.jpg):

$$Score = w_T \frac{T}{T_{max}} + w_D \frac{D}{D_{max}} + w_A \frac{AQI}{AQI_{max}}$$

| Variable | Meaning |
|---|---|
| T | Travel time (minutes) |
| D | Distance (km) |
| AQI | Average air quality index along the route |
| w_T, w_D, w_A | User-adjustable weights (must sum to 1) |

**Lower score = better route.** The user controls the weights — a person with asthma would weight AQI heavily; someone in a rush would weight time heavily.

AQI data is fetched in real-time from **Malaysia's DOE APIMS network** (65 monitoring stations nationwide) via the AQICN API.

Replace it with this instead:
**Weight Normalisation**

If the weights do not sum to 1, each is rescaled by dividing by the total:

| Weight | Normalised Formula |
|---|---|
| w_T | w_T / (w_T + w_D + w_A) |
| w_D | w_D / (w_T + w_D + w_A) |
| w_A | w_A / (w_T + w_D + w_A) |

This ensures weights always sum to 1 regardless of slider values, keeping the score formula mathematically valid.

---

## 🗺️ Demo — Cyberjaya → KL Sentral

Three routes compared in real-time:

| Route | Via | Time | Distance |
|---|---|---|---|
| Route A | Putrajaya Highway | 35 min | 30 km |
| Route B | Petaling Jaya (Federal Highway) | 50 min | 28 km |
| Route C | ELITE + KL Direct | 40 min | 35 km |

Rankings shift dynamically based on live AQI readings and the user's chosen weights.

---

## 🚀 Quick Start

### 1. Clone the repo
```bash
git clone https://github.com/Spoureeeee/AIRoute.git
cd AIRoute
```

### 2. Install dependencies
```bash
pip install requests tabulate folium streamlit
```

### 3. Get a free AQICN API token
Register at [aqicn.org/data-platform/token](https://aqicn.org/data-platform/token/) — free, just needs an email.

### 4. Add your token
Open `app.py` and replace `YOUR_TOKEN_HERE` with your token.

### 5. Run the dashboard
```bash
streamlit run app.py
```

Opens at `http://localhost:8501`

---

## 📁 Project Structure

```
AIRoute/
├── app.py                ← Streamlit web dashboard (Week 3)
├── airoute_week2.py      ← Folium map generator (Week 2)
├── airoute_week1.py      ← Core AQI fetcher + route scorer (Week 1)
└── README.md
```

---

## 🛠️ Tech Stack

| Tool | Purpose |
|---|---|
| Python | Core language |
| AQICN API | Real-time Malaysia DOE air quality data |
| Folium | Interactive map visualisation |
| Streamlit | Web dashboard |
| Git + GitHub | Version control + portfolio |

---

## 🗺️ Roadmap — v2

- [ ] OpenRouteService API integration — real road-based routing instead of straight lines
- [ ] ML pollution prediction model trained on historical AQICN data
- [ ] User profile system — save preferences (e.g. "I have asthma")
- [ ] More origin/destination pairs across Klang Valley
- [ ] Mobile-responsive UI
- [ ] Crowdsourced hazard reporting (heavy smoke, construction dust)

---

## 📊 Why This Matters

- Malaysia recorded **130+ unhealthy air quality days** in 2023 due to haze
- High-density commuter corridors (Cyberjaya–KL, Shah Alam–KL) have no health-aware routing tools
- Long-term exposure to PM2.5 is linked to respiratory and cardiovascular disease
- AIRoute gives commuters actionable, data-driven health choices — not just faster ETAs

---

## 👤 Author

**Aflin Airil**
Final Semester, Foundation in Engineering — MMU Cyberjaya
Incoming: Bachelor of Engineering (Hons) in Computer Engineering


[GitHub](https://github.com/Spoureeeee) · [LinkedIn](https://www.linkedin.com/in/aflin-airil-35038230a/)

---

## 📄 License

MIT License — open for academic and non-commercial use.

---

*AIRoute v1 — built in 2 hours as a proof of concept. iNVENTX 2027, we're coming.*
