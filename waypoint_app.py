# waypoint_gen.py

from shapely.geometry import Polygon, LineString
from shapely.affinity import rotate
import math

def generate_guidance_lines(
    field_polygon: Polygon,
    tool_width: float,
    num_headland: int = 2,
    driving_angle_deg: float = 90
):
    """
    Generate guidance lines (waypoints) for automatic grass cutting / marking.

    Args:
        field_polygon (Polygon): Shapely Polygon of the field boundary.
        tool_width (float): Width of the cutting or marking tool.
        num_headland (int): Number of passes around edge (headland).
        driving_angle_deg (float): Driving direction angle in degrees (0-180).

    Returns:
        List[LineString]: List of clipped, rotated guidance LineStrings.
    """

    # Rotate polygon to align driving direction horizontally
    rotated_poly = rotate(field_polygon, -driving_angle_deg, origin='centroid', use_radians=False)
    minx, miny, maxx, maxy = rotated_poly.bounds

    # Offset polygon outward for headland passes
    headland_offset = num_headland * tool_width
    outer_poly = rotated_poly.buffer(headland_offset)

    # Generate parallel horizontal lines spaced by tool_width
    lines = []
    y = miny - headland_offset
    max_y_extended = maxy + headland_offset

    while y <= max_y_extended:
        line = LineString([(minx - headland_offset*2, y), (maxx + headland_offset*2, y)])
        lines.append(line)
        y += tool_width

    # Clip lines by the outer polygon (field + headland)
    clipped_lines = []
    for line in lines:
        clipped = line.intersection(outer_poly)
        if clipped.is_empty:
            continue
        if clipped.geom_type == 'MultiLineString':
            for seg in clipped.geoms:
                clipped_lines.append(seg)
        elif clipped.geom_type == 'LineString':
            clipped_lines.append(clipped)

    # Rotate lines back to original orientation
    final_lines = [rotate(line, driving_angle_deg, origin=field_polygon.centroid, use_radians=False)
                   for line in clipped_lines]

    # Sort lines by centroid Y to ensure traversal order
    final_lines.sort(key=lambda l: l.centroid.y)

    return final_lines


def generate_waypoints_from_lines(lines):
    """
    Convert guidance lines into an ordered list of waypoints,
    alternating direction to minimize travel time.

    Args:
        lines (List[LineString]): List of guidance lines.

    Returns:
        List[Tuple[float, float]]: Ordered waypoint coordinates.
    """
    waypoints = []
    reverse = False
    for line in lines:
        coords = list(line.coords)
        if reverse:
            coords.reverse()
        waypoints.extend(coords)
        reverse = not reverse
    return waypoints


if __name__ == "__main__":
    import matplotlib.pyplot as plt
    from shapely.geometry import Polygon

    # Example polygon (100m x 50m rectangle)
    field = Polygon([(0,0), (100,0), (100,50), (0,50)])

    tool_width = 5.0
    num_headland = 2
    driving_angle = 90  # Vertical passes

    guidance_lines = generate_guidance_lines(field, tool_width, num_headland, driving_angle)
    waypoints = generate_waypoints_from_lines(guidance_lines)

    # Plotting
    fig, ax = plt.subplots()
    x, y = field.exterior.xy
    ax.plot(x, y, color='green', linewidth=2, label='Field Boundary')

    for line in guidance_lines:
        x, y = line.xy
        ax.plot(x, y, color='red')

    wp_x, wp_y = zip(*waypoints)
    ax.scatter(wp_x, wp_y, color='blue', s=15, label='Waypoints')

    ax.set_aspect('equal')
    ax.legend()
    ax.set_title('Generated Guidance Lines and Waypoints')
    plt.show()
