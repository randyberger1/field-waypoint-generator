import streamlit as st
import geopandas as gpd
from shapely.geometry import Polygon, LineString
import matplotlib.pyplot as plt
import folium
from streamlit_folium import st_folium

st.set_page_config(page_title="Field Robotics Waypoint Generator", layout="wide")
st.title("⚽ Field Robotics Waypoint Generator")

# Sidebar inputs
st.sidebar.header("🛠 Parameters")
tool_width = st.sidebar.number_input("Tool Width (m)", min_value=0.1, value=1.0)
num_headland = st.sidebar.slider("Number of Headland Passes", 1, 10, 2)
angle = st.sidebar.slider("Driving Direction (degrees)", 0, 180, 90)

# Choose input mode
mode = st.radio("Choose field input mode:", ["📍 Manual Coordinate Entry", "🗺️ Draw on Map"])

def generate_dummy_waypoints(polygon, width, n_headland, direction):
    minx, miny, maxx, maxy = polygon.bounds
    lines = []
    y = miny + width
    while y < maxy - width:
        lines.append(LineString([(minx, y), (maxx, y)]))
        y += width
    return gpd.GeoDataFrame(geometry=lines, crs="EPSG:4326")

if mode == "📍 Manual Coordinate Entry":
    st.markdown("Enter coordinates in format: `lat, lon` per line")
    input_text = st.text_area("Coordinates:", height=200, value="""
40.7128, -74.0060
40.7128, -74.0000
40.7160, -74.0000
40.7160, -74.0060
""")

    if input_text.strip():
        try:
            coords = []
            for line in input_text.strip().splitlines():
                lat, lon = map(float, line.split(","))
                coords.append((lon, lat))  # Geo uses (lon, lat)

            if coords[0] != coords[-1]:
                coords.append(coords[0])

            polygon = Polygon(coords)
            field_gdf = gpd.GeoDataFrame(geometry=[polygon], crs="EPSG:4326")

            st.success("✅ Polygon created successfully!")

            fig, ax = plt.subplots()
            field_gdf.plot(ax=ax, color='lightgreen', edgecolor='black')
            st.pyplot(fig)

            # Waypoint generation
            waypoints_gdf = generate_dummy_waypoints(polygon, tool_width, num_headland, angle)
            fig2, ax2 = plt.subplots()
            field_gdf.plot(ax=ax2, color='none', edgecolor='black')
            waypoints_gdf.plot(ax=ax2, color='red')
            st.subheader("Generated Waypoints")
            st.pyplot(fig2)

        except Exception as e:
            st.error(f"Error parsing coordinates: {e}")

elif mode == "🗺️ Draw on Map":
    st.markdown("🧭 Use the map below to draw a polygon field boundary.")
    m = folium.Map(location=[40.713, -74.005], zoom_start=15)
    folium.TileLayer("OpenStreetMap").add_to(m)
    draw_options = {
        "polyline": False,
        "rectangle": False,
        "circle": False,
        "circlemarker": False,
        "marker": False,
    }
    draw = st_folium(m, width=700, height=500, returned_objects=["last_drawn"], draw_options=draw_options)

    if draw and draw.get("last_drawn"):
        try:
            coords = draw["last_drawn"]["geometry"]["coordinates"][0]
            coords = [(pt[0], pt[1]) for pt in coords]
            polygon = Polygon(coords)
            field_gdf = gpd.GeoDataFrame(geometry=[polygon], crs="EPSG:4326")

            fig, ax = plt.subplots()
            field_gdf.plot(ax=ax, color='lightblue', edgecolor='black')
            st.pyplot(fig)

            # Generate waypoints
            waypoints_gdf = generate_dummy_waypoints(polygon, tool_width, num_headland, angle)
            fig2, ax2 = plt.subplots()
            field_gdf.plot(ax=ax2, color='none', edgecolor='black')
            waypoints_gdf.plot(ax=ax2, color='red')
            st.subheader("Generated Waypoints")
            st.pyplot(fig2)

        except Exception as e:
            st.error(f"Error generating polygon from map: {e}")
