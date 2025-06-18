import requests
import sqlite3
import datetime
import time
import os

# CONFIGURATION DE L'API STAR TRANSPORTS EN COMMUN
REALTIME_API_URL = "https://data.explore.star.fr/api/records/1.0/search/?dataset=tco-bus-circulation-passages-tr&q=*&rows=1000"
STOP_API_URL = "https://data.explore.star.fr/api/records/1.0/search/?dataset=tco-bus-topologie-pointsarret-td&q=*&rows=1000"

#INITIALISATION DE LA BASE DE DONNÉES
def init_db():
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    db_path = os.path.join(BASE_DIR, "urban_mobility.db")
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS star_stops (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT,
        latitude REAL,
        longitude REAL
    )
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS star_realtime (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        timestamp TEXT,
        line TEXT,
        destination TEXT,
        stop_name TEXT,
        latitude REAL,
        longitude REAL,
        status TEXT,
        arrival_scheduled TEXT,
        arrival_real TEXT
    )
    """)

    conn.commit()
    conn.close()
    print("✅ Base initialisée.\n")

# COLLECTION DES ARRÊTS
def get_star_stops():
    print("🌐 Collecte des arrêts STAR avec coordonnées...")
    try:
        response = requests.get(STOP_API_URL)
        data = response.json()
        records = data.get("records", [])
        return [
            {
                "name": rec["fields"].get("nom", "").strip(),
                "lat": rec["fields"]["coordonnees"][0],
                "lon": rec["fields"]["coordonnees"][1],
            }
            for rec in records if "coordonnees" in rec["fields"]
        ]
    except Exception as e:
        print(f"❌ Erreur récupération arrêts STAR : {e}")
        return []

def store_star_stops(stops):
    conn = sqlite3.connect("urban_mobility.db")
    cursor = conn.cursor()
    cursor.execute("DELETE FROM star_stops")

    for stop in stops:
        cursor.execute("""
            INSERT INTO star_stops (name, latitude, longitude)
            VALUES (?, ?, ?)
        """, (stop["name"], stop["lat"], stop["lon"]))

    conn.commit()
    conn.close()
    print(f"✅ {len(stops)} arrêts STAR enregistrés.\n")

# COLLECTE DES PASSAGES EN TEMPS RÉEL
def get_star_realtime():
    print("🚌 Collecte brute des passages STAR...")
    try:
        headers = {"User-Agent": "Mozilla/5.0"}
        response = requests.get(REALTIME_API_URL, headers=headers)
        print("🔎 HTTP Status:", response.status_code)
        print("📤 Contenu brut reçu (début):")
        print(response.text[:1000])  # Ajouté pour diagnostic

        data = response.json()
        records = data.get("records", [])
        print(f"📥 {len(records)} passages reçus.")
        return records
    except Exception as e:
        print(f"❌ Erreur récupération STAR : {e}")
        return []



def store_star_realtime(records):
    conn = sqlite3.connect("urban_mobility.db")
    cursor = conn.cursor()
    ts = datetime.datetime.utcnow().isoformat()

    for rec in records:
        fields = rec.get("fields", {})
        stop = fields.get("nomarret", "inconnu").strip()
        line = fields.get("nomcourtligne", "inconnu")
        destination = fields.get("destination", "inconnue")
        status = fields.get("precision", "inconnue")
        sched = fields.get("arriveetheorique", None)
        real = fields.get("arrivee", None)
        coords = fields.get("coordonnees", [None, None])
        lat = coords[0]
        lon = coords[1]

        cursor.execute("""
            INSERT INTO star_realtime (timestamp, line, destination, stop_name, latitude, longitude, status, arrival_scheduled, arrival_real)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (ts, line, destination, stop, lat, lon, status, sched, real))

    conn.commit()
    conn.close()
    print(f"✅ {len(records)} passages STAR enregistrés.\n")

# AFFICHAGE DE LA DERNIÈRE ENTRÉE
def show_last_star():
    conn = sqlite3.connect("urban_mobility.db")
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM star_realtime ORDER BY id DESC LIMIT 1")
    row = cursor.fetchone()
    print("📊 Dernière entrée STAR :", row if row else "Aucune donnée.")
    conn.close()

# BOUCLE PRINCIPALE
def main_loop():
    init_db()
    store_star_stops(get_star_stops())

    while True:
        records = get_star_realtime()
        store_star_realtime(records)
        show_last_star()
        print("⏳ Attente 5 minutes...\n")
        time.sleep(300)

if __name__ == "__main__":
    print("🚀 Script STAR complet lancé !\n")
    main_loop()
