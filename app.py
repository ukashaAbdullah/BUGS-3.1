import time
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st
from etl import fetch_and_store, get_eda_data

st.set_page_config(page_title="ISS Orbital Tracker", page_icon="🛰️", layout="wide")

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

c_btn, c_toggle, c_status = st.columns([1.4, 1.4, 3.2])

with c_btn:
    fetch_clicked = st.button("🔄 Fetch Now", type="primary", use_container_width=True)

with c_toggle:
    live_track = st.toggle("⚡ Auto-Track (5s)", value=False)

if fetch_clicked:
    try:
        fetch_and_store(include_crew=True)
        with c_status:
            st.success("Updated live ISS & crew data!")
    except Exception as e:
        with c_status:
            st.error(f"Error: {e}")

elif live_track:
    try:
        fetch_and_store(include_crew=False)
        with c_status:
            st.caption("Live tracking active — updating every 5 seconds...")
    except Exception as e:
        with c_status:
            st.warning(f"Temporary network hiccup: {e}")

df, crew_df = get_eda_data()

if df.empty:
    st.info("Click **Fetch Now** or turn on **Auto-Track (5s)** to start.")
    st.stop()

latest = df.iloc[-1]
valid_speeds = df["speed_kmh"].dropna()
latest_speed = f"{valid_speeds.iloc[-1]:,.1f} km/h" if not valid_speeds.empty else "Need 2+ points"
crew_count = int(crew_df["total_in_space"].iloc[0]) if not crew_df.empty else 0

m1, m2, m3, m4 = st.columns(4)
m1.metric("Latitude", f"{latest['lat']:.2f}°")
m2.metric("Longitude", f"{latest['lon']:.2f}°")
m3.metric("Orbital Speed", latest_speed)
m4.metric("Humans in Space", crew_count)

st.markdown("### 🌍 ISS Orbital Trajectory")
fig_map = go.Figure()

path_lats, path_lons = [], []
for i in range(len(df)):
    if i > 0 and abs(df.loc[i, "lon"] - df.loc[i - 1, "lon"]) > 180:
        path_lats.append(None)
        path_lons.append(None)
    path_lats.append(df.loc[i, "lat"])
    path_lons.append(df.loc[i, "lon"])

fig_map.add_trace(
    go.Scattergeo(
        lat=path_lats,
        lon=path_lons,
        mode="lines+markers",
        line=dict(width=2.5, color="#38bdf8"),
        marker=dict(size=4, color="#7dd3fc"),
        name="Flight Path",
    )
)

fig_map.add_trace(
    go.Scattergeo(
        lat=[latest["lat"]],
        lon=[latest["lon"]],
        mode="markers+text",
        text=["ISS"],
        textposition="top center",
        marker=dict(size=13, color="#ef4444"),
        name="Current ISS (Red Dot)",
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
    height=420,
    uirevision="iss-map-locked",
    margin=dict(l=0, r=0, t=10, b=0),
    paper_bgcolor="#0f172a",
    font=dict(color="#f8fafc"),
    legend=dict(orientation="h", y=0.02, x=0.02),
)
st.plotly_chart(fig_map, use_container_width=True)

left, right = st.columns([3, 2])

with left:
    st.markdown("### ⚡ Orbital Speed Over Time")
    speed_df = df.dropna(subset=["speed_kmh"])
    if not speed_df.empty:
        fig_spd = px.line(
            speed_df,
            x="utc_time",
            y="speed_kmh",
            markers=True,
            labels={"utc_time": "UTC Time", "speed_kmh": "Speed (km/h)"},
        )
        fig_spd.update_layout(height=290, margin=dict(l=10, r=10, t=15, b=10))
        st.plotly_chart(fig_spd, use_container_width=True)
    else:
        st.info("Collect at least 2 readings to see speed over time.")

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

if live_track:
    time.sleep(5)
    st.rerun()
