import requests
import sqlite3
import datetime
import time
import os

TOMTOM_API_KEY = "Dg92TyuiXhtZH1t7hJwiRdMgMA7DtGmj"
ZOOM = 10


LAT_START, LAT_END = 48.05, 48.15
LON_START, LON_END = -1.75, -1.55
STEP = 0.01 

def generate_grid():
    points = []
    lat = LAT_START
    while lat <= LAT_END:
        lon = LON_START
        while lon <= LON_END:
            points.append((round(lat, 5), round(lon, 5)))
            lon += STEP
        lat += STEP
    return points

def init_db():
    db_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "urban_mobility.db")
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS tomtom_traffic (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        timestamp TEXT,
        location TEXT,
        current_speed REAL,
        free_flow_speed REAL,
        congestion_level TEXT
    )
    """)
    conn.commit()
    conn.close()

def get_traffic_from_grid(points):
    print(f"🌐 Appel API TomTom pour {len(points)} points...")
    all_data = []
    for lat, lon in points:
        url = f"https://api.tomtom.com/traffic/services/4/flowSegmentData/absolute/{ZOOM}/json"
        params = {
            "point": f"{lat},{lon}",
            "unit": "KMPH",
            "key": TOMTOM_API_KEY
        }
        try:
            response = requests.get(url, params=params)
            if response.status_code == 200:
                data = response.json()
                if "flowSegmentData" in data:
                    all_data.append((lat, lon, data["flowSegmentData"]))
            else:
                print(f"❌ {lat},{lon} HTTP {response.status_code}")
        except Exception as e:
            print(f"❌ Erreur {lat},{lon} : {e}")
    return all_data

def store_traffic_data(all_data):
    conn = sqlite3.connect("urban_mobility.db")
    cursor = conn.cursor()
    ts = datetime.datetime.utcnow().isoformat()

    for lat, lon, segment in all_data:
        location = f"{lat},{lon}"
        current_speed = segment["currentSpeed"]
        free_speed = segment["freeFlowSpeed"]
        ratio = current_speed / free_speed if free_speed > 0 else 0

        if ratio >= 0.85:
            level = "fluide"
        elif ratio >= 0.6:
            level = "dense"
        else:
            level = "bouché"

        cursor.execute("""
            INSERT INTO tomtom_traffic (timestamp, location, current_speed, free_flow_speed, congestion_level)
            VALUES (?, ?, ?, ?, ?)
        """, (ts, location, current_speed, free_speed, level))

    conn.commit()
    conn.close()
    print(f"✅ {len(all_data)} tronçons sauvegardés.")

def main_loop():
    init_db()
    while True:
        try:
            points = generate_grid()
            data = get_traffic_from_grid(points)
            store_traffic_data(data)
        except Exception as e:
            print(f"❌ Erreur globale : {e}")
        print("⏳ Attente 5 minutes...\n")
        time.sleep(770)

if __name__ == "__main__":
    print("🚀 Script multi-tronçons TomTom lancé !")
    main_loop()
