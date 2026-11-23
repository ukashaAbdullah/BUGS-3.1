import streamlit as st
import plotly.express as px
from etl import fetch_and_store, get_eda_data

st.set_page_config(page_title="ISS Orbital Tracker", layout="wide")

# Render basic HTML/CSS header card
with open("index.html", "r", encoding="utf-8") as f:
    st.components.v1.html(f.read(), height=190)

if st.button("Fetch Live ISS & Crew Data"):
    try:
        fetch_and_store()
        st.success("Data fetched, validated & saved to SQLite!")
    except Exception as e:
        st.error(f"Error: {e}")

df, crew_df = get_eda_data()

if not df.empty:
    latest = df.iloc[-1]
    latest_speed = df["speed_kmh"].dropna().iloc[-1] if not df["speed_kmh"].dropna().empty else "N/A"
    crew_count = int(crew_df["total_in_space"].iloc[0]) if not crew_df.empty else 0

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Latitude", f"{latest['lat']:.2f}")
    c2.metric("Longitude", f"{latest['lon']:.2f}")
    c3.metric("Orbital Speed (km/h)", latest_speed)
    c4.metric("Humans in Space", crew_count)

    st.subheader("ISS Orbital Trajectory")
    fig_map = px.line_geo(df, lat="lat", lon="lon", hover_data=["utc_time", "speed_kmh"])
    fig_map.add_scattergeo(lat=[latest["lat"]], lon=[latest["lon"]], name="Current ISS")
    st.plotly_chart(fig_map, use_container_width=True)

    st.subheader("Orbital Speed Over Time")
    speed_data = df.dropna(subset=["speed_kmh"])
    if not speed_data.empty:
        fig_spd = px.line(speed_data, x="utc_time", y="speed_kmh", markers=True)
        st.plotly_chart(fig_spd, use_container_width=True)

    st.subheader("Active Crew Manifest")
    if not crew_df.empty:
        st.dataframe(crew_df[["name", "craft"]], use_container_width=True, hide_index=True)
else:
    st.info("Click **Fetch Live ISS & Crew Data** above to record your first points.")
