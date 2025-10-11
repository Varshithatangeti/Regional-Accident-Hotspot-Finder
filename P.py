import streamlit as st
import pandas as pd
import numpy as np
import folium
from streamlit_folium import st_folium
from geopy.geocoders import Nominatim
import os
import time

# -------------------------------
# 🎨 PAGE CONFIG
# -------------------------------
st.set_page_config(page_title="Regional Accident Hotspot Finder", layout="wide")
st.title("🚦 Regional Accident Hotspot Finder in India 🇮🇳")
st.markdown("Enter any region name and see accident hotspots and road conditions nearby.")

# -------------------------------
# 📂 LOAD DATA
# -------------------------------
accident_csv = "accident_prediction_india.csv"
coords_csv = "city_coordinates.csv"

if os.path.exists(accident_csv):
    df = pd.read_csv(accident_csv)
else:
    uploaded_file = st.file_uploader("📤 Upload your CSV file", type=["csv"])
    if uploaded_file:
        df = pd.read_csv(uploaded_file)
    else:
        st.warning("⚠️ Please provide accident CSV.")
        st.stop()

# Fill missing values
fill_values = {
    "Driver License Status": "Unknown",
    "Alcohol Involvement": "Unknown",
    "Road Type": "Unknown",
    "Road Condition": "Unknown",
    "Lighting Conditions": "Unknown",
    "Traffic Control Presence": "Unknown",
    "Weather Conditions": "Unknown",
    "Driver Gender": "Unknown",
    "Accident Severity": "Unknown",
    "City Name": "Unknown",
    "Accident Location Details": "Unknown",
    "State Name": "Unknown"
}
df.fillna(value=fill_values, inplace=True)

# Load city coordinates
if os.path.exists(coords_csv):
    coords_df = pd.read_csv(coords_csv)
else:
    st.error("⚠️ city_coordinates.csv not found.")
    st.stop()

# -------------------------------
# 🗂️ USER INPUT
# -------------------------------
st.subheader("🔍 Enter Region Name (City / Town / Village / District / State)")
region_name = st.text_input("Type region name here:", "")

if region_name:
    # -------------------------------
    # 🔎 FIND USER LOCATION
    # -------------------------------
    geolocator = Nominatim(user_agent="regional_accident_app")
    try:
        user_loc = geolocator.geocode(f"{region_name}, India")
        if not user_loc:
            st.warning(f"Cannot find coordinates for: {region_name}")
            st.stop()
        user_lat, user_lon = user_loc.latitude, user_loc.longitude
    except:
        st.error("Error fetching location coordinates.")
        st.stop()

    # -------------------------------
    # 🧠 MERGE COORDINATES AND FILTER NEARBY
    # -------------------------------
    df_coords = df.merge(coords_df, on="City Name", how="left")

    def haversine(lat1, lon1, lat2, lon2):
        R = 6371
        phi1 = np.radians(lat1)
        phi2 = np.radians(lat2)
        dphi = np.radians(lat2 - lat1)
        dlambda = np.radians(lon2 - lon1)
        a = np.sin(dphi/2.0)**2 + np.cos(phi1)*np.cos(phi2)*np.sin(dlambda/2.0)**2
        return R * 2 * np.arcsin(np.sqrt(a))

    df_coords["Distance_km"] = df_coords.apply(lambda row: haversine(user_lat, user_lon, row["Latitude"], row["Longitude"]), axis=1)
    nearby_df = df_coords[df_coords["Distance_km"] <= 50].copy()

    if nearby_df.empty:
        st.info("No accident-prone areas found nearby. Showing your location only.")
        nearby_df = pd.DataFrame([{
            "City Name": region_name,
            "State Name": "Unknown",
            "Accident Location Details": "N/A",
            "Accident Severity": "N/A",
            "Road Type": "N/A",
            "Road Condition": "N/A",
            "Lighting Conditions": "N/A",
            "Traffic Control Presence": "N/A",
            "Latitude": user_lat,
            "Longitude": user_lon,
            "Distance_km": 0
        }])

    # -------------------------------
    # 📊 SHOW TABLE
    # -------------------------------
    st.subheader("📊 Nearby Accident Data")
    display_cols = ["City Name","State Name","Accident Location Details","Accident Severity",
                    "Road Type","Road Condition","Lighting Conditions","Traffic Control Presence","Distance_km"]
    st.dataframe(nearby_df[display_cols].sort_values("Distance_km"))

    # -------------------------------
    # 🗺️ GENERATE ENHANCED MAP
    # -------------------------------
    st.subheader("🗺️ Nearby Accident Hotspots Map")
    m = folium.Map(location=[user_lat, user_lon], zoom_start=12)

    for _, row in nearby_df.iterrows():
        if row["Accident Severity"] not in ["N/A", "Unknown"]:
            color = "red"
            radius = 6 + np.log1p(1)  # can be replaced with #accidents if available
        else:
            color = "green"
            radius = 6

        folium.CircleMarker(
            location=[row["Latitude"], row["Longitude"]],
            radius=radius,
            color=color,
            fill=True,
            fill_opacity=0.6,
            popup=(f"<b>City:</b> {row['City Name']}<br>"
                   f"<b>State:</b> {row['State Name']}<br>"
                   f"<b>Accident Severity:</b> {row['Accident Severity']}<br>"
                   f"<b>Road Type:</b> {row['Road Type']}<br>"
                   f"<b>Road Condition:</b> {row['Road Condition']}<br>"
                   f"<b>Lighting:</b> {row['Lighting Conditions']}<br>"
                   f"<b>Traffic Control:</b> {row['Traffic Control Presence']}<br>"
                   f"<b>Distance:</b> {row['Distance_km']:.2f} km")
        ).add_to(m)

    # Draw 50 km radius around user
    folium.Circle(
        location=[user_lat, user_lon],
        radius=50000,
        color="blue",
        fill=False,
        popup="50 km Radius"
    ).add_to(m)

    # Highlight user location
    folium.Marker(
        location=[user_lat, user_lon],
        popup=f"<b>Your Location:</b> {region_name}",
        icon=folium.Icon(color="blue", icon="star")
    ).add_to(m)

    st_folium(m, width=1200, height=600)
    st.success("✅ Map generated successfully!")



















