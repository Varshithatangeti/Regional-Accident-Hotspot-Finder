import streamlit as st
import pandas as pd
import numpy as np
import folium
from streamlit_folium import st_folium
from geopy.geocoders import Nominatim
from folium.plugins import HeatMap
import os

st.set_page_config(page_title="Regional Accident Hotspot Finder", layout="wide")
st.title("🚦 Regional Accident Hotspot Finder in India 🇮🇳")
st.markdown("Enter a region name and view all accident hotspots within a 50 km radius.")

accident_csv = "accident_prediction_india.csv"
coords_csv = "city_coordinates.csv"

if os.path.exists(accident_csv):
    df = pd.read_csv(accident_csv)
else:
    uploaded_file = st.file_uploader("📤 Upload your accident CSV file", type=["csv"])
    if uploaded_file:
        df = pd.read_csv(uploaded_file)
    else:
        st.warning("⚠️ Please upload accident_prediction_india.csv to continue.")
        st.stop()

if os.path.exists(coords_csv):
    coords_df = pd.read_csv(coords_csv)
else:
    st.error("⚠️ city_coordinates.csv not found.")
    st.stop()

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

if "Latitude" not in df.columns or "Longitude" not in df.columns:
    df = df.merge(coords_df, on="City Name", how="left")

st.subheader("🔍 Enter Region Name (City / Town / District / State)")
region_name = st.text_input("Type region name here:", "")

if region_name:
    geolocator = Nominatim(user_agent="regional_accident_app")
    try:
        user_loc = geolocator.geocode(f"{region_name}, India")
        if not user_loc:
            st.warning(f"Cannot find coordinates for: {region_name}")
            st.stop()
        user_lat, user_lon = user_loc.latitude, user_loc.longitude
    except:
        st.error("❌ Error fetching location coordinates.")
        st.stop()

    def haversine(lat1, lon1, lat2, lon2):
        R = 6371
        phi1, phi2 = np.radians(lat1), np.radians(lat2)
        dphi, dlambda = np.radians(lat2 - lat1), np.radians(lon2 - lon1)
        a = np.sin(dphi / 2.0)**2 + np.cos(phi1)*np.cos(phi2)*np.sin(dlambda / 2.0)**2
        return R * 2 * np.arcsin(np.sqrt(a))

    df = df.dropna(subset=["Latitude", "Longitude"])
    df["Distance_km"] = df.apply(
        lambda row: haversine(user_lat, user_lon, row["Latitude"], row["Longitude"]), axis=1
    )

    nearby_df = df[df["Distance_km"] <= 50].copy()

    if nearby_df.empty:
        st.info("No accident spots found within 50 km.")
        nearby_df = pd.DataFrame([{
            "City Name": region_name,
            "State Name": "Unknown",
            "Accident Severity": "N/A",
            "Latitude": user_lat,
            "Longitude": user_lon,
            "Distance_km": 0
        }])

    st.subheader("📊 Accident Data within 50 km Radius")
    show_cols = [
        "City Name", "State Name", "Accident Severity",
        "Road Type", "Road Condition", "Lighting Conditions", "Traffic Control Presence"
    ]
    available_cols = [col for col in show_cols if col in nearby_df.columns]
    st.dataframe(nearby_df[available_cols + ["Distance_km"]].sort_values("Distance_km"))

    st.subheader("🗺️ Accident Hotspots (Red Circles = Accident Spots, Blue Star = You)")
    m = folium.Map(location=[user_lat, user_lon], zoom_start=10, tiles="OpenStreetMap")

    heat_data = [[row["Latitude"], row["Longitude"]] for _, row in nearby_df.iterrows()]
    if heat_data:
        HeatMap(heat_data, radius=18, blur=15, gradient={0.3:'orange',0.5:'red',0.8:'darkred'}).add_to(m)

    for _, row in nearby_df.iterrows():
        folium.Circle(
            location=[row["Latitude"], row["Longitude"]],
            radius=300,
            color="red",
            fill=True,
            fill_color="red",
            fill_opacity=0.4,
            popup=(f"<b>City:</b> {row['City Name']}<br>"
                   f"<b>State:</b> {row['State Name']}<br>"
                   f"<b>Severity:</b> {row['Accident Severity']}<br>"
                   f"<b>Distance:</b> {row['Distance_km']:.2f} km")
        ).add_to(m)

    folium.Circle(
        location=[user_lat, user_lon],
        radius=50000,
        color="blue",
        fill=False,
        popup="50 km Radius"
    ).add_to(m)

    folium.Marker(
        location=[user_lat, user_lon],
        popup=f"<b>Your Location:</b> {region_name}",
        icon=folium.Icon(color="blue", icon="star")
    ).add_to(m)

    st_folium(m, width=1200, height=600)
    st.success("✅ Accident-prone areas are now highlighted with red circles and labeled.")
