import streamlit as st
import geopandas as gpd
from shapely.geometry import Polygon
import pandas as pd
import matplotlib.pyplot as plt
from waypoint_gen import generate_guidance_lines, generate_waypoints_from_lines

st.title("Field Robotics Waypoint Generator")

# --- Input field polygon ---
input_mode = st.radio("Input polygon by:", ["Draw on Map (GeoJSON)", "Manual Coordinates"])

field_poly = None
if input_mode == "Manual Coordinates":
    coords_text = st.text_area("Enter coordinates (lat, lon) one per line:", 
        value="40.7128, -74.0060\n40.7128, -74.0000\n40.7160, -74.0000\n40.7160, -74.0060")
    try:
        coords = []
        for line in coords_text.strip().splitlines():
            lat, lon = map(float, line.split(","))
            coords.append((lon, lat))  # Shapely expects (lon, lat)
        if coords[0] != coords[-1]:
            coords.append(coords[0])
        field_poly = Polygon(coords)
    except Exception as e:
        st.error(f"Invalid input: {e}")

else:
    geojson_str = st.text_area("Paste GeoJSON Polygon Feature here:")
    if geojson_str:
        import json
        from shapely.geometry import shape
        try:
            gj = json.loads(geojson_str)
            field_poly = shape(gj["geometry"])  # assume valid polygon geometry
        except Exception as e:
            st.error(f"Invalid GeoJSON: {e}")

if field_poly is not None:
    st.success("Polygon loaded successfully!")

    # Parameters
    tool_width = st.number_input("Tool width (meters):", min_value=0.1, value=5.0, step=0.1)
    num_headland = st.slider("Number of headland passes:", 0, 5, 2)
    driving_angle = st.slider("Driving angle (degrees):", 0, 180, 90)

    # Generate guidance lines & waypoints
    lines = generate_guidance_lines(field_poly, tool_width, num_headland, driving_angle)
    waypoints = generate_waypoints_from_lines(lines)

    # Show matplotlib plot
    fig, ax = plt.subplots()
    x, y = field_poly.exterior.xy
    ax.plot(x, y, color="green", linewidth=2, label="Field Boundary")
    for line in lines:
        x, y = line.xy
        ax.plot(x, y, color="red")
    if waypoints:
        wp_x, wp_y = zip(*waypoints)
        ax.scatter(wp_x, wp_y, color="blue", s=15, label="Waypoints")
    ax.set_aspect("equal")
    ax.legend()
    st.pyplot(fig)

    # Export waypoints as CSV
    if st.button("Export waypoints CSV"):
        df = pd.DataFrame(waypoints, columns=["lon", "lat"])
        csv = df.to_csv(index=False)
        st.download_button("Download CSV", data=csv, file_name="waypoints.csv")
