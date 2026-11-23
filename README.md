# 🛰️ ISS Orbital Tracker & Crew Monitor

![Python](https://img.shields.io/badge/Python-3.11-3776AB?style=for-the-badge&logo=python&logoColor=white)
![Streamlit](https://img.shields.io/badge/Streamlit-Dashboard-FF4B4B?style=for-the-badge&logo=streamlit&logoColor=white)
![Pydantic](https://img.shields.io/badge/Pydantic-v2_Validation-E92063?style=for-the-badge&logo=pydantic&logoColor=white)
![SQLite](https://img.shields.io/badge/SQLite-Persistence-003B57?style=for-the-badge&logo=sqlite&logoColor=white)
![Plotly](https://img.shields.io/badge/Plotly-Geospatial-3F4F75?style=for-the-badge&logo=plotly&logoColor=white)
![DevContainer](https://img.shields.io/badge/Codespaces-Ready-181717?style=for-the-badge&logo=github&logoColor=white)

A real-time Extract, Transform, Load (ETL) pipeline and interactive geospatial telemetry dashboard engineered by **Team Bugs**. The application ingests live orbital coordinates and astronaut manifests from the **Open-Notify API**, enforces strict schema validation, persists historical telemetry in **SQLite**, and renders an interactive **Natural Earth** trajectory map with instantaneous orbital velocity analytics.

---

## ✨ Core Capabilities

- **Live Telemetry & Automated Polling:** Supports on-demand synchronization of both station coordinates and crew rosters, alongside an automated **5-second continuous tracking loop** that appends new coordinate fixes without redundant crew queries.
- **Interactive Geospatial Trajectory:** Renders the International Space Station's flight path on a dark-themed Natural Earth projection (`Plotly Graph Objects`) with automatic **anti-meridian ($\pm 180^\circ$ longitude) segmentation** to prevent visual wraparound artifacts.
- **Click-to-Simulate Waypoints:** Embeds a $6^\circ \times 6^\circ$ interactive coordinate matrix across the globe (`-60°` to `60°` latitude), enabling users to click anywhere on the map to plot custom waypoints and dynamically recompute trajectory kinematics.
- **Altitude-Adjusted Orbital Kinematics:** Computes point-to-point orbital ground velocity ($\text{km/h}$) using the Haversine formula calibrated to the ISS orbital radius ($R = 6,779.0\text{ km}$).
- **Schema-Validated SQLite Storage:** Validates incoming JSON payloads through **Pydantic v2** models (coercing stringified coordinates into floats) before deduplicating and committing records to `iss_data.db`.

---

## 🏗️ System Architecture & Module Breakdown

| File | Architectural Layer | Primary Responsibilities |
| :--- | :--- | :--- |
| `app.py` | **Presentation & UI** | Orchestrates the Streamlit layout, session state, metric cards, interactive `Scattergeo` map, velocity time-series chart, and crew manifest table. |
| `etl.py` | **ETL & Kinematics Engine** | Queries Open-Notify endpoints, manages SQLite connection/table initialization, deduplicates timestamps, and executes Haversine speed calculations. |
| `models.py` | **Data Validation** | Defines Pydantic v2 schemas (`Position`, `ISSResponse`, `Astronaut`, `AstrosResponse`) with `mode="before"` type coercion for coordinate strings. |
| `index.html` | **Custom UI Component** | Provides a styled HTML/CSS hero banner rendered via `streamlit.components.v1.html` displaying project metadata and technology tags. |
| `requirements.txt` | **Dependency Manifest** | Pins core runtime libraries (`requests`, `pydantic`, `pandas`, `plotly`, `streamlit`). |
| `.devcontainer/devcontainer.json` | **Cloud Environment** | Configures a Python 3.11 Bookworm container for GitHub Codespaces with automated dependency installation and port `8501` forwarding. |

---

## ⚙️ Tracking & Simulation Modes

| Mode | Trigger | API Network Calls | Database Persistence | Velocity Behavior |
| :--- | :--- | :--- | :--- | :--- |
| **Fetch Live** | `🔄 Fetch Live` button | Fetches `iss-now.json` **and** `astros.json` | Appends unique timestamp to `positions`; refreshes `crew` table | Computes velocity across stored database fixes where $0 < \Delta t \le 600\text{ s}$ |
| **Auto-Track (5s)** | `⚡ Auto-Track (5s)` toggle | Polls `iss-now.json` every 5 seconds (`include_crew=False`) | Appends each new orbital fix to `iss_data.db` | Continuously updates live trajectory and speed curve |
| **Interactive Simulation** | Click any point on the map | None (local session state) | Ephemeral (`st.session_state.custom_points` only) | Recalculates speed assuming a 5-second step ($\Delta t = 5\text{ s}$) between waypoints |
| **Reset to Live** | `↩️ Live API Mode` button | None | Preserves persisted SQLite history | Clears simulated map clicks and restores pure database telemetry |

---

## 📐 Orbital Velocity Methodology

To estimate instantaneous orbital velocity between consecutive coordinate fixes $(\phi_1, \lambda_1)$ and $(\phi_2, \lambda_2)$, `etl.py` applies the **Haversine formula** using an effective orbital radius that combines Earth's mean radius ($6,371\text{ km}$) with the ISS nominal orbital altitude ($\approx 408\text{ km}$):

$$R_{\text{orbit}} = 6,371.0 + 408.0 = 6,779.0\text{ km}$$

$$d = 2 R_{\text{orbit}} \arcsin\left(\sqrt{\sin^2\left(\frac{\Delta\phi}{2}\right) + \cos(\phi_1)\cos(\phi_2)\sin^2\left(\frac{\Delta\lambda}{2}\right)}\right)$$

$$v_{\text{km/h}} = \left(\frac{d}{\Delta t}\right) \times 3600$$

> **Continuity Filter:** For persisted database records, velocity is calculated only when consecutive timestamps satisfy $0 < \Delta t \le 600\text{ seconds}$, preventing stale gaps between separate tracking sessions from skewing speed metrics.

---

## 📂 Repository Structure

```text
BUGS-3.1/
├── .devcontainer/
│   └── devcontainer.json   # GitHub Codespaces & VS Code Dev Container config
├── app.py                  # Main Streamlit dashboard & interactive Plotly visualizations
├── etl.py                  # Open-Notify API ingestion, SQLite storage & Haversine math
├── index.html              # Styled HTML/CSS header component
├── models.py               # Pydantic v2 data validation schemas
└── requirements.txt        # Python package dependencies
## Local Setup

### Requirements
- Python 3.10 or newer
- pip

### Installation

Clone the repository:

```bash
git clone https://github.com/ukashaAbdullah/BUGS-3.1.git
cd BUGS-3.1

### Install dependencies

```bash
pip install -r requirements.txt

### Run the application

```bash
streamlit run app.py.
'''




