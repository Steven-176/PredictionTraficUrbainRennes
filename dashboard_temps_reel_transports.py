def run_realtime_interface():
    import streamlit as st
    import requests
    import pandas as pd
    import polyline
    import pydeck as pdk
    from datetime import datetime
    import pytz


    # configurations de l'API
    GOOGLE_API_KEY = "AIzaSyDvGHxMr-vEZhOuJ1z1CbypTNU7r4tV0KU"
    GEOCODING_URL = "https://maps.googleapis.com/maps/api/geocode/json"
    DIRECTIONS_URL = "https://maps.googleapis.com/maps/api/directions/json"
    STAR_API_REALTIME = [
        ("bus", "https://data.explore.star.fr/api/records/1.0/search/?dataset=tco-bus-circulation-passages-tr&q=*&rows=1000"),
        ("metro", "https://data.explore.star.fr/api/records/1.0/search/?dataset=tco-metro-circulation-passages-tr&q=*&rows=1000"),
        ("tram", "https://data.explore.star.fr/api/records/1.0/search/?dataset=tco-tram-circulation-passages-tr&q=*&rows=1000")
    ]

    # stylysé la page
    st.markdown("""
    <style>
        /* Import Google Fonts */
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');
        
        /* Global Styles */
        .main {
            font-family: 'Inter', sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
        }
        
        /* Custom container */
        .custom-container {
            background: rgba(255, 255, 255, 0.95);
            backdrop-filter: blur(10px);
            border-radius: 20px;
            padding: 2rem;
            margin: 1rem 0;
            box-shadow: 0 8px 32px rgba(0, 0, 0, 0.1);
            border: 1px solid rgba(255, 255, 255, 0.2);
        }
        
        /* Title styling */
        .main-title {
            text-align: center;
            background: linear-gradient(45deg, #667eea, #764ba2);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            background-clip: text;
            font-size: 3rem;
            font-weight: 700;
            margin-bottom: 2rem;
            text-shadow: 2px 2px 4px rgba(0,0,0,0.1);
        }
        
        /* Sidebar styling */
        .css-1d391kg {
            background: linear-gradient(180deg, #f8f9ff 0%, #e8eeff 100%);
            border-radius: 15px;
            padding: 1rem;
        }
        
        /* Button styling */
        .stButton > button {
            background: linear-gradient(45deg, #667eea, #764ba2);
            color: white;
            border: none;
            border-radius: 25px;
            padding: 0.75rem 2rem;
            font-weight: 600;
            font-size: 1rem;
            transition: all 0.3s ease;
            box-shadow: 0 4px 15px rgba(102, 126, 234, 0.4);
        }
        
        .stButton > button:hover {
            transform: translateY(-2px);
            box-shadow: 0 8px 25px rgba(102, 126, 234, 0.6);
        }
        
        /* Card styling */
        .info-card {
            background: linear-gradient(135deg, #ff9a9e 0%, #fecfef 50%, #fecfef 100%);
            border-radius: 15px;
            padding: 1.5rem;
            margin: 1rem 0;
            box-shadow: 0 6px 20px rgba(0, 0, 0, 0.1);
            border-left: 5px solid #ff6b9d;
        }
        
        .warning-card {
            background: linear-gradient(135deg, #ffeaa7 0%, #fab1a0 100%);
            border-radius: 15px;
            padding: 1.5rem;
            margin: 1rem 0;
            box-shadow: 0 6px 20px rgba(0, 0, 0, 0.1);
            border-left: 5px solid #e17055;
        }
        
        .success-card {
            background: linear-gradient(135deg, #74b9ff 0%, #00cec9 100%);
            border-radius: 15px;
            padding: 1.5rem;
            margin: 1rem 0;
            box-shadow: 0 6px 20px rgba(0, 0, 0, 0.1);
            border-left: 5px solid #00b894;
            color: white;
        }
        
        /* Dataframe styling */
        .stDataFrame {
            border-radius: 10px;
            overflow: hidden;
            box-shadow: 0 4px 15px rgba(0, 0, 0, 0.1);
        }
        
        /* Input styling */
        .stTextInput > div > div > input {
            border-radius: 10px;
            border: 2px solid #e0e6ff;
            transition: all 0.3s ease;
        }
        
        .stTextInput > div > div > input:focus {
            border-color: #667eea;
            box-shadow: 0 0 10px rgba(102, 126, 234, 0.3);
        }
        
        /* Selectbox styling */
        .stSelectbox > div > div {
            border-radius: 10px;
            border: 2px solid #e0e6ff;
        }
        
        /* Header icons */
        .header-icon {
            font-size: 1.2em;
            margin-right: 0.5rem;
        }
        
        /* Metrics styling */
        .metric-container {
            background: rgba(255, 255, 255, 0.8);
            border-radius: 12px;
            padding: 1rem;
            text-align: center;
            box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
            margin: 0.5rem;
        }
        
        /* Animation for loading */
        @keyframes fadeIn {
            from { opacity: 0; transform: translateY(20px); }
            to { opacity: 1; transform: translateY(0); }
        }
        
        .fade-in {
            animation: fadeIn 0.6s ease-out;
        }
    </style>
    """, unsafe_allow_html=True)

    # fonctions pour l'API Google Maps et STAR
    def geocode_address(address):
        params = {"address": address, "key": GOOGLE_API_KEY}
        response = requests.get(GEOCODING_URL, params=params)
        res = response.json()
        if res["status"] == "OK":
            loc = res["results"][0]["geometry"]["location"]
            return loc["lat"], loc["lng"]
        return None, None

    def get_transit_directions(origin, destination):
        params = {
            "origin": origin,
            "destination": destination,
            "mode": "transit",
            "alternatives": "true",
            "departure_time": "now",
            "key": GOOGLE_API_KEY
        }
        response = requests.get(DIRECTIONS_URL, params=params)
        return response.json()

    def extract_route_steps(data):
        routes_info = []
        for route in data.get("routes", []):
            steps = []
            poly_points = []
            try:
                leg = route["legs"][0]
                for step in leg["steps"]:
                    travel_mode = step.get("travel_mode")
                    transit = step.get("transit_details")
                    line = transit["line"]["short_name"] if transit else "Walk"
                    dep_time = transit["departure_time"]["text"] if transit else ""
                    arr_time = transit["arrival_time"]["text"] if transit else ""
                    dep_stop = transit["departure_stop"]["name"] if transit else ""
                    instructions = step["html_instructions"]
                    points = polyline.decode(step["polyline"]["points"])
                    poly_points.extend(points)

                    steps.append({
                        "Mode": travel_mode,
                        "Ligne": line,
                        "Départ": dep_time,
                        "Arrivée": arr_time,
                        "Arrêt": dep_stop,
                        "Instructions": instructions
                    })
                description = " > ".join([s['Ligne'] for s in steps if s['Mode'] == "TRANSIT"])
                duration_value = leg.get("duration", {}).get("value", 999999)
                routes_info.append((steps, poly_points, leg.get("duration", {}).get("text", ""), description, duration_value))
            except:
                continue
        return routes_info

    def extract_transit_stops(data):
        """Extrait tous les arrêts de transport en commun"""
        stops = []
        for route in data.get("routes", []):
            for leg in route.get("legs", []):
                for step in leg.get("steps", []):
                    if step.get("travel_mode") == "TRANSIT":
                        transit = step.get("transit_details", {})
                        
                        # Arrêt de départ
                        dep_stop = transit.get("departure_stop", {})
                        if dep_stop:
                            stops.append({
                                "name": dep_stop.get("name", ""),
                                "lat": dep_stop.get("location", {}).get("lat"),
                                "lng": dep_stop.get("location", {}).get("lng"),
                                "type": "departure",
                                "line": transit.get("line", {}).get("short_name", "")
                            })
                        
                        # Arrêt d'arrivée
                        arr_stop = transit.get("arrival_stop", {})
                        if arr_stop:
                            stops.append({
                                "name": arr_stop.get("name", ""),
                                "lat": arr_stop.get("location", {}).get("lat"),
                                "lng": arr_stop.get("location", {}).get("lng"),
                                "type": "arrival",
                                "line": transit.get("line", {}).get("short_name", "")
                            })
        return stops

    def get_star_passages(stop_name):
        all_passages = []
        for mode, url in STAR_API_REALTIME:
            try:
                r = requests.get(url)
                records = r.json().get("records", [])
                for rec in records:
                    f = rec.get("fields", {})
                    if f.get("nomarret", "").strip().lower() == stop_name.strip().lower():
                        all_passages.append({
                            "line": f.get("nomcourtligne"),
                            "destination": f.get("destination"),
                            "status": f.get("precision"),
                            "scheduled": f.get("arriveetheorique"),
                            "real": f.get("arrivee"),
                            "mode": mode
                        })
            except:
                continue
        
        df = pd.DataFrame(all_passages)
        if not df.empty:
            df["scheduled"] = pd.to_datetime(df["scheduled"], errors='coerce', utc=True)
            df["real"] = pd.to_datetime(df["real"], errors='coerce', utc=True)
            
            # Calculer le retard en minutes seulement si les deux valeurs sont présentes
            def calculate_delay(row):
                if pd.isna(row["scheduled"]) or pd.isna(row["real"]):
                    return 0
                try:
                    # S'assurer que les deux sont dans le même fuseau horaire
                    if row["scheduled"].tz is None:
                        scheduled = row["scheduled"].replace(tzinfo=pytz.UTC)
                    else:
                        scheduled = row["scheduled"]
                        
                    if row["real"].tz is None:
                        real = row["real"].replace(tzinfo=pytz.UTC)
                    else:
                        real = row["real"]
                    
                    return (real - scheduled).total_seconds() / 60
                except:
                    return 0
            
            df["retard (min)"] = df.apply(calculate_delay, axis=1)
            df["perturbation"] = df["status"].apply(lambda x: "Oui" if x != "Temps réel" else "Non")
            df = df.sort_values("scheduled")
        
        return df


    st.markdown('<h1 class="main-title">🚉 Itinéraire optimisé avec Google Maps et STAR</h1>', unsafe_allow_html=True)
    st.markdown("<div style='margin-top: -3rem;'></div>", unsafe_allow_html=True)


    # les inputs
    with st.sidebar:
        st.markdown("### 🧭 Planification de trajet")
        
        depart = st.text_input(
            "📍 Adresse de départ", 
            value="27 Rue Dupont-des-Loges, Rennes",
            help="Saisissez votre point de départ"
        )
        
        arrivee = st.text_input(
            "🎯 Adresse d'arrivée", 
            value="5 All. Marie Berhaut, Rennes",
            help="Saisissez votre destination"
        )
        
        search_button = st.button("🔍 Rechercher les trajets disponibles", use_container_width=True)
        st.markdown('</div>', unsafe_allow_html=True)

    if search_button:
        if depart and arrivee:
            with st.spinner("🔄 Recherche d'itinéraires en cours..."):
                lat_dep, lon_dep = geocode_address(depart)
                lat_arr, lon_arr = geocode_address(arrivee)

                if lat_dep and lat_arr:
                    origin = f"{lat_dep},{lon_dep}"
                    destination = f"{lat_arr},{lon_arr}"
                    data = get_transit_directions(origin, destination)

                    if data.get("routes"):
                        routes_info = extract_route_steps(data)
                        stops_info = extract_transit_stops(data)
                        st.session_state["routes"] = routes_info
                        st.session_state["stops"] = stops_info
                        st.session_state["coords"] = (lat_dep, lon_dep, lat_arr, lon_arr)
                        st.session_state["selected"] = 0
                        st.success("✅ Itinéraires trouvés avec succès!")
                    else:
                        st.error("❌ Aucun itinéraire trouvé via Google Maps.")
                else:
                    st.error("❌ Adresse introuvable. Vérifiez les champs.")

    if "routes" in st.session_state:
        # Sélection d'itinéraire
        with st.sidebar:
            st.markdown("### 🛣️ Choix d'itinéraire")
            options = [f"{r[3]} ({r[2]})" for r in st.session_state["routes"]]
            selected = st.selectbox("Sélectionnez votre itinéraire", options)
            st.session_state["selected"] = options.index(selected)

        col1, col2 = st.columns([2, 1])
        
        with col1:
            index = st.session_state["selected"]
            steps, poly_points, duration, description, _ = st.session_state["routes"][index]

            st.markdown(f"""
            <div class="custom-container fade-in">
                <h3>📋 Détails de l'itinéraire sélectionné</h3>
                <div class="metric-container">
                    <h4>🕒 Durée estimée: {duration}</h4>
                </div>
            </div>
            """, unsafe_allow_html=True)
            
            df_steps = pd.DataFrame(steps)
            st.dataframe(df_steps, use_container_width=True)

            # Informations temps réel STAR
            lignes_affichees = []
            has_perturbation_or_retard = False
            
            for step in steps:
                if step["Mode"] == "TRANSIT":
                    stop = step["Arrêt"]
                    line = step["Ligne"]
                    if (stop, line) in lignes_affichees:
                        continue
                    lignes_affichees.append((stop, line))
                    
                    with st.spinner(f"Récupération des données STAR pour {line}..."):
                        df_star = get_star_passages(stop)
                        
                    if not df_star.empty:
                        df_match = df_star[df_star["line"] == line]
                        if not df_match.empty:
                            if (df_match["retard (min)"].fillna(0) > 0).any() or (df_match["perturbation"] == "Oui").any():
                                has_perturbation_or_retard = True
                            
                            st.markdown(f"""
                            <div class="custom-container">
                                <h4>🚌 STAR - Ligne {line} depuis {stop}</h4>
                            </div>
                            """, unsafe_allow_html=True)
                            
                            # Styling pour les retards
                            def highlight_delays(val):
                                if isinstance(val, (int, float)) and val > 0:
                                    return 'background-color: #ffcccc; font-weight: bold;'
                                return ''
                            
                            styled_df = df_match[['line', 'destination', 'status', 'scheduled', 'real', 'retard (min)', 'mode', 'perturbation']].style.applymap(
                                highlight_delays, subset=['retard (min)']
                            )
                            st.write(styled_df)

        with col2:
            # Recommandation optimale
            optimal_route = None
            for route in st.session_state["routes"]:
                r_steps = route[0]
                perturb = False
                for s in r_steps:
                    if s["Mode"] == "TRANSIT":
                        stop = s["Arrêt"]
                        line = s["Ligne"]
                        df_star = get_star_passages(stop)
                        if not df_star.empty:
                            df_match = df_star[df_star["line"] == line]
                            if not df_match.empty:
                                if (df_match["retard (min)"].fillna(0) > 0).any() or (df_match["perturbation"] == "Oui").any():
                                    perturb = True
                                    break
                if not perturb:
                    if optimal_route is None or route[4] < optimal_route[4]:
                        optimal_route = route

            if optimal_route:
                traj_desc = []
                for s in optimal_route[0]:
                    if s["Mode"] == "TRANSIT":
                        traj_desc.append(f"Ligne {s['Ligne']} depuis {s['Arrêt']}")
                traj_str = " → ".join(traj_desc)
                
                st.markdown(f"""
                <div class="success-card fade-in">
                    <h3>🎯 Trajet optimal recommandé</h3>
                    <p>{traj_str}</p>
                    <h4>🕒 Durée: {optimal_route[2]}</h4>
                </div>
                """, unsafe_allow_html=True)
            else:
                status_class = "success-card" if not has_perturbation_or_retard else "warning-card"
                status_icon = "✅" if not has_perturbation_or_retard else "⚠️"
                status_text = "Itinéraire optimal sans perturbations" if not has_perturbation_or_retard else "Attention: retards ou perturbations détectés"
                
                st.markdown(f"""
                <div class="{status_class} fade-in">
                    <h3>🤖 Recommandation intelligente</h3>
                    <p><strong>Durée totale:</strong> {duration}</p>
                    <p>{status_icon} {status_text}</p>
                </div>
                """, unsafe_allow_html=True)

        # Carte
        st.markdown("""
        <div class="custom-container fade-in">
            <h3>🗺️ Visualisation du trajet</h3>
        </div>
        """, unsafe_allow_html=True)

        lat_dep, lon_dep, lat_arr, lon_arr = st.session_state["coords"]
        df_poly = pd.DataFrame(poly_points, columns=["lat", "lon"])

    # Préparer les arrêts pour l'itinéraire sélectionné uniquement
        selected_stops = []
        steps = st.session_state["routes"][st.session_state["selected"]][0]

        for step in steps:
            if step["Mode"] == "TRANSIT":
                stop_name = step["Arrêt"]
                for stop in st.session_state["stops"]:
                    if stop["name"].strip().lower() == stop_name.strip().lower():
                        if stop["lat"] and stop["lng"]:
                            selected_stops.append({
                                "lat": stop["lat"],
                                "lng": stop["lng"],
                                "name": stop["name"],
                                "line": stop["line"],
                                "type": stop["type"]
                            })


        df_stops = pd.DataFrame(selected_stops)

        layers = [
            # Ligne du trajet
            pdk.Layer(
                'LineLayer',
                data=df_poly,
                get_position='[lon, lat]',
                get_color='[102, 126, 234, 200]',
                get_width=5
            ),
            # Points départ et points d arrivée
            pdk.Layer(
                'ScatterplotLayer',
                data=pd.DataFrame([
                    {"lat": lat_dep, "lng": lon_dep, "name": "Départ", "color": [255, 0, 0, 200]},
                    {"lat": lat_arr, "lng": lon_arr, "name": "Arrivée", "color": [0, 255, 0, 200]}
                ]),
                get_position='[lng, lat]',
                get_color='color',
                get_radius=120,
                pickable=True
            )
        ]

        # Ajouter les arrêts s'ils existent
        if not df_stops.empty:
            layers.append(
                pdk.Layer(
                    'ScatterplotLayer',
                    data=df_stops,
                    get_position='[lng, lat]',
                    get_color='[255, 165, 0, 180]',  # Orange pour les arrêts
                    get_radius=80,
                    pickable=True
                )
            )

        st.pydeck_chart(pdk.Deck(
            map_style='mapbox://styles/mapbox/light-v9',
            initial_view_state=pdk.ViewState(
                latitude=lat_dep,
                longitude=lon_dep,
                zoom=12,
                pitch=0
            ),
            layers=layers,
            tooltip={"text": "{name}\nLigne: {line}"}
        ))