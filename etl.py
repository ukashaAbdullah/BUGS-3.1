import math
import sqlite3
import pandas as pd
import requests
from models import AstrosResponse, ISSResponse

DB_NAME = "iss_data.db"
ISS_URL = "http://api.open-notify.org/iss-now.json"
ASTROS_URL = "http://api.open-notify.org/astros.json"


def get_conn():
    return sqlite3.connect(DB_NAME, check_same_thread=False)


def init_db():
    with get_conn() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS positions (
                timestamp INTEGER UNIQUE,
                utc_time TEXT,
                lat REAL,
                lon REAL
            )
        """)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS crew (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT,
                craft TEXT,
                total_in_space INTEGER
            )
        """)


def fetch_and_store(include_crew: bool = True):
    init_db()

    # 1. Fast ISS Position fetch
    r_iss = requests.get(ISS_URL, timeout=5).json()
    iss = ISSResponse.model_validate(r_iss)

    df_pos = pd.DataFrame([{
        "timestamp": iss.timestamp,
        "utc_time": pd.to_datetime(iss.timestamp, unit="s", utc=True).strftime("%Y-%m-%d %H:%M:%S"),
        "lat": iss.iss_position.latitude,
        "lon": iss.iss_position.longitude,
    }])

    with get_conn() as conn:
        existing = pd.read_sql("SELECT timestamp FROM positions WHERE timestamp = ?", conn, params=(iss.timestamp,))
        if existing.empty:
            df_pos.to_sql("positions", conn, if_exists="append", index=False)

    # 2. Crew Manifest (optional during fast live-tracking ticks)
    if include_crew:
        r_crew = requests.get(ASTROS_URL, timeout=5).json()
        crew = AstrosResponse.model_validate(r_crew)

        df_crew = pd.DataFrame([{
            "name": p.name,
            "craft": p.craft,
            "total_in_space": crew.number,
        } for p in crew.people])

        with get_conn() as conn:
            conn.execute("DELETE FROM crew")
            df_crew.to_sql("crew", conn, if_exists="append", index=False)


def haversine_km(lat1, lon1, lat2, lon2):
    radius_km = 6779.0  # Earth radius (6371 km) + ISS altitude (~408 km)
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dp = math.radians(lat2 - lat1)
    dl = math.radians(lon2 - lon1)
    a = math.sin(dp / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dl / 2) ** 2
    return 2 * radius_km * math.asin(math.sqrt(min(1.0, a)))


def get_eda_data():
    init_db()
    with get_conn() as conn:
        df = pd.read_sql("SELECT * FROM positions ORDER BY timestamp ASC", conn)
        crew_df = pd.read_sql("SELECT * FROM crew", conn)

    speeds = [None]
    for i in range(1, len(df)):
        dt = df.loc[i, "timestamp"] - df.loc[i - 1, "timestamp"]
        if 0 < dt <= 600:
            dist = haversine_km(
                df.loc[i - 1, "lat"],
                df.loc[i - 1, "lon"],
                df.loc[i, "lat"],
                df.loc[i, "lon"],
            )
            speeds.append(round((dist / dt) * 3600, 1))
        else:
            speeds.append(None)

    if not df.empty:
        df["speed_kmh"] = speeds

    return df, crew_df
