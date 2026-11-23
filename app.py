import math
import time
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st
from etl import fetch_and_store, get_eda_data, haversine_km

st.set_page_config(page_title="ISS Orbital Tracker", page_icon="🛰️", layout="wide")

if "custom_points" not in st.session_state:
    st.session_state.custom_points = []

if "manual_mode" not in st.session_state:
    st.session_state.manual_mode = False

st.markdown(
    """
    <style>
      [data-testid="stMetric"] {
        background-color: #f8fafc;
        border: 1px solid #e2e8f0;
        padding: 12px 16px;
        border-radius: 12px;
      }
    </style>
    """,
    unsafe_allow_html=True,
)

with open("index.html", "r", encoding="utf-8") as f:
    st.components.v1.html(f.read(), height=175)

c1, c2, c3, c4 = st.columns([1.3, 1.3, 1.4, 2.0])

with c1:
    fetch_clicked = st.button("🔄 Fetch Live", type="primary", use_container_width=True)

with c2:
    live_track = st.toggle("⚡ Auto-Track (5s)", value=False)

with c3:
    reset_clicked = st.button("↩️ Live API Mode", use_container_width=True)

if reset_clicked:
    st.session_state.manual_mode = False
    st.session_state.custom_points = []
    st.rerun()

if fetch_clicked:
    st.session_state.manual_mode = False
    try:
        fetch_and_store(include_crew=True)
        with c4:
            st.success("Fetched live ISS & crew data!")
    except Exception as e:
        with c4:
            st.error(f"Error: {e}")
elif live_track and not st.session_state.manual_mode:
    try:
        fetch_and_store(include_crew=False)
        with c4:
            st.caption("Auto-tracking active (5s)...")
    except Exception as e:
        with c4:
            st.warning(f"Network issue: {e}")

df, crew_df = get_eda_data()

if df.empty and not st.session_state.custom_points:
    st.info("Click **Fetch Live** or click anywhere on the map below to place the ISS dot.")

# Build working dataframe (either live DB data + any dragged/clicked points, or manual points)
if st.session_state.manual_mode and st.session_state.custom_points:
    work_df = st.session_state.custom_points.copy()
else:
    work_df = []
    for _, r in df.iterrows():
        work_df.append({
            "timestamp": int(r["timestamp"]),
            "utc_time": r["utc_time"],
            "lat": float(r["lat"]),
            "lon": float(r["lon"]),
            "speed_kmh": r["speed_kmh"],
        })
    for pt in st.session_state.custom_points:
        work_df.append(pt)

# Recalculate speed for the last point if custom point was added
if len(work_df) >= 2:
    for i in range(1, len(work_df)):
        dt = abs(work_df[i]["timestamp"] - work_df[i - 1]["timestamp"])
        if dt == 0:
            dt = 5
        dist = haversine_km(
            work_df[i - 1]["lat"],
            work_df[i - 1]["lon"],
            work_df[i]["lat"],
            work_df[i]["lon"],
        )
        work_df[i]["speed_kmh"] = round((dist / dt) * 3600, 1)

crew_count = int(crew_df["total_in_space"].iloc[0]) if not crew_df.empty else 0

if work_df:
    latest = work_df[-1]
    speeds_only = [x["speed_kmh"] for x in work_df if x.get("speed_kmh") is not None]
    latest_speed = f"{speeds_only[-1]:,.1f} km/h" if speeds_only else "Need 2+ points"

    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Latitude", f"{latest['lat']:.2f}°")
    m2.metric("Longitude", f"{latest['lon']:.2f}°")
    m3.metric("Orbital Speed", latest_speed)
    m4.metric("Humans in Space", crew_count)
else:
    latest = {"lat": 0.0, "lon": 0.0, "utc_time": "N/A"}

st.markdown("### 🌍 ISS Orbital Trajectory (Click on map to move ISS & trajectory)")

fig_map = go.Figure()

# Invisible grid of clickable points over world so clicking anywhere on the map moves the red dot
grid_lats = [lat for lat in range(-60, 61, 6) for _ in range(-180, 181, 6)]
grid_lons = [lon for _ in range(-60, 61, 6) for lon in range(-180, 181, 6)]
fig_map.add_trace(
    go.Scattergeo(
        lat=grid_lats,
        lon=grid_lons,
        mode="markers",
        marker=dict(size=10, color="rgba(0,0,0,0)"),
        hovertemplate="Move ISS here: (%{lat:.1f}°, %{lon:.1f}°)<extra></extra>",
        showlegend=False,
        name="Click Target",
    )
)

if work_df:
    path_lats, path_lons = [], []
    for i, pt in enumerate(work_df):
        if i > 0 and abs(pt["lon"] - work_df[i - 1]["lon"]) > 180:
            path_lats.append(None)
            path_lons.append(None)
        path_lats.append(pt["lat"])
        path_lons.append(pt["lon"])

    fig_map.add_trace(
        go.Scattergeo(
            lat=path_lats,
            lon=path_lons,
            mode="lines+markers",
            line=dict(width=2.5, color="#38bdf8"),
            marker=dict(size=5, color="#7dd3fc"),
            name="Trajectory",
        )
    )

    fig_map.add_trace(
        go.Scattergeo(
            lat=[latest["lat"]],
            lon=[latest["lon"]],
            mode="markers+text",
            text=["ISS"],
            textposition="top center",
            marker=dict(size=14, color="#ef4444"),
            name="Red Dot (ISS)",
        )
    )

fig_map.update_geos(
    projection_type="natural earth",
    showland=True,
    landcolor="#1e293b",
    showocean=True,
    oceancolor="#0f172a",
    showcountries=True,
    countrycolor="#475569",
    bgcolor="#0f172a",
)
fig_map.update_layout(
    height=430,
    uirevision="iss-map-locked",
    clickmode="event+select",
    margin=dict(l=0, r=0, t=10, b=0),
    paper_bgcolor="#0f172a",
    font=dict(color="#f8fafc"),
    legend=dict(orientation="h", y=0.02, x=0.02),
)

event = st.plotly_chart(fig_map, use_container_width=True, on_select="rerun", key="iss_map")

if event and getattr(event, "selection", None) and event.selection.points:
    pt_clicked = event.selection.points[0]
    new_lat = float(pt_clicked["lat"])
    new_lon = float(pt_clicked["lon"])
    last_ts = work_df[-1]["timestamp"] if work_df else int(time.time())
    st.session_state.custom_points.append({
        "timestamp": last_ts + 5,
        "utc_time": time.strftime("%Y-%m-%d %H:%M:%S", time.gmtime()),
        "lat": round(new_lat, 2),
        "lon": round(new_lon, 2),
        "speed_kmh": None,
    })
    st.rerun()

left, right = st.columns([3, 2])

with left:
    st.markdown("### ⚡ Orbital Speed Over Time")
    speed_rows = [
        {"utc_time": x["utc_time"], "speed_kmh": x["speed_kmh"]}
        for x in work_df
        if x.get("speed_kmh") is not None
    ]
    if speed_rows:
        fig_spd = px.line(
            speed_rows,
            x="utc_time",
            y="speed_kmh",
            markers=True,
            labels={"utc_time": "UTC Time", "speed_kmh": "Speed (km/h)"},
        )
        fig_spd.update_layout(height=290, margin=dict(l=10, r=10, t=15, b=10))
        st.plotly_chart(fig_spd, use_container_width=True)
    else:
        st.info("Click on the map or fetch live data to see speed over time.")

with right:
    st.markdown("### 👨‍🚀 Active Crew Manifest")
    if not crew_df.empty:
        st.dataframe(
            crew_df[["name", "craft"]].rename(columns={"name": "Astronaut", "craft": "Spacecraft"}),
            use_container_width=True,
            hide_index=True,
            height=290,
        )
    else:
        st.info("No crew data available yet.")

if live_track and not st.session_state.manual_mode:
    time.sleep(5)
    st.rerun()
