import sqlite3
import math
import time

DB_PATH = "/home/jeongyooon/teddy/hazard_zones.db"
CONFIRM_THRESHOLD = 3
WARN_RADIUS_M = 15


def init_db():
    conn = sqlite3.connect(DB_PATH)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS hazard_zones (
            grid_lat REAL,
            grid_lon REAL,
            count INTEGER DEFAULT 1,
            last_seen REAL,
            confirmed INTEGER DEFAULT 0,
            PRIMARY KEY (grid_lat, grid_lon)
        )
    """)
    conn.commit()
    conn.close()


def to_grid(lat, lon, precision=4):
    return round(lat, precision), round(lon, precision)


def record_obstacle(lat, lon):
    if lat is None or lon is None:
        return

    g_lat, g_lon = to_grid(lat, lon)
    conn = sqlite3.connect(DB_PATH)

    cur = conn.execute(
        "SELECT count FROM hazard_zones WHERE grid_lat=? AND grid_lon=?",
        (g_lat, g_lon)
    )
    row = cur.fetchone()

    if row:
        new_count = row[0] + 1
        confirmed = 1 if new_count >= CONFIRM_THRESHOLD else 0

        conn.execute(
            "UPDATE hazard_zones SET count=?, last_seen=?, confirmed=? "
            "WHERE grid_lat=? AND grid_lon=?",
            (new_count, time.time(), confirmed, g_lat, g_lon)
        )
    else:
        conn.execute(
            "INSERT INTO hazard_zones (grid_lat, grid_lon, count, last_seen) "
            "VALUES (?, ?, 1, ?)",
            (g_lat, g_lon, time.time())
        )

    conn.commit()
    conn.close()


def haversine(lat1, lon1, lat2, lon2):
    R = 6371000

    p1, p2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlambda = math.radians(lon2 - lon1)

    a = (
        math.sin(dphi / 2) ** 2 +
        math.cos(p1) * math.cos(p2) * math.sin(dlambda / 2) ** 2
    )

    return 2 * R * math.asin(math.sqrt(a))


def check_nearby_hazard(lat, lon):
    if lat is None or lon is None:
        return False

    conn = sqlite3.connect(DB_PATH)
    cur = conn.execute(
        "SELECT grid_lat, grid_lon FROM hazard_zones WHERE confirmed=1"
    )
    zones = cur.fetchall()
    conn.close()

    for g_lat, g_lon in zones:
        if haversine(lat, lon, g_lat, g_lon) <= WARN_RADIUS_M:
            return True

    return False

def get_confirmed_zones():
    conn = sqlite3.connect(DB_PATH)
    cur = conn.execute(
        "SELECT grid_lat, grid_lon, count, last_seen "
        "FROM hazard_zones WHERE confirmed=1"
    )
    rows = cur.fetchall()
    conn.close()

    return [
        {
            "lat": row[0],
            "lon": row[1],
            "count": row[2],
            "last_seen": row[3]
        }
        for row in rows
    ]
