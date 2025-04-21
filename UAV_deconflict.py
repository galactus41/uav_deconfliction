import streamlit as st
import pandas as pd
import numpy as np
import math
import plotly.graph_objects as go

# ---------- Initialize session state ----------
if 'drone_data' not in st.session_state:
    st.session_state.drone_data = []

if 'waypoint_coordinates' not in st.session_state:
    st.session_state.waypoint_coordinates = {
        'A': (4, 9, 5),   # Shop
        'B': (8, 5, 2),   # Mall
        'C': (1, 9, 4)    # AB Society
    }

if 'location_descriptions' not in st.session_state:
    st.session_state.location_descriptions = {
        'A': 'Shop',
        'B': 'Mall',
        'C': 'AB Society'
    }

# ---------- Sidebar Navigation ----------
st.sidebar.title("UAV Deconfliction App")
current_page = st.sidebar.radio("Navigation", [
    "Add Drone Mission", 
    "Edit Drone Mission", 
    "Drone Mission Table", 
    "Add New Destination", 
    "3D Path Visualization"
])

# ---------- Helper Functions ----------
def calculate_distance(point1, point2):
    """Calculate Euclidean distance between two 3D points"""
    return math.sqrt(sum((coord1 - coord2) ** 2 for coord1, coord2 in zip(point1, point2)))

def generate_interpolated_path(waypoints, interpolation_points=10):
    """Create a smooth path between waypoints with interpolated points"""
    interpolated_path = []
    for i in range(len(waypoints) - 1):
        for t in range(interpolation_points + 1):
            interpolated_path.append((
                waypoints[i][0] + (waypoints[i+1][0] - waypoints[i][0]) * t / interpolation_points,
                waypoints[i][1] + (waypoints[i+1][1] - waypoints[i][1]) * t / interpolation_points,
                waypoints[i][2] + (waypoints[i+1][2] - waypoints[i][2]) * t / interpolation_points
            ))
    return interpolated_path

def detect_collisions(new_drone, existing_drones, waypoint_coordinates, min_safe_distance=1.5):
    """Check for potential collisions between drone paths"""
    collision_reports = []
    resolution_suggestions = []
    collision_path_segments = []
    
    new_path = generate_interpolated_path([waypoint_coordinates[wp] for wp in new_drone['waypoints']])
    
    for drone in existing_drones:
        other_path = generate_interpolated_path([waypoint_coordinates[wp] for wp in drone['waypoints']])
        
        for i, point1 in enumerate(new_path):
            for j, point2 in enumerate(other_path):
                if calculate_distance(point1, point2) < min_safe_distance:
                    collision_reports.append({
                        'Drone': drone['name'],
                        'Time Window': f"{drone['start_time']} - {drone['end_time']}",
                        'Distance': f"{calculate_distance(point1, point2):.2f} meters"
                    })
                    collision_path_segments.append((point1, point2))
                    resolution_suggestions.append({
                        'Recommendation': f"Adjust time or reroute {new_drone['name']}",
                        'Conflicting Drone': drone['name']
                    })
                    break
                    
    return collision_reports[:3], resolution_suggestions[:3], collision_path_segments

# ---------- Page: Add Drone Mission ----------
if current_page == "Add Drone Mission":
    st.header("Add New Drone Mission")
    
    # Get available drone names that aren't already in use
    available_drone_names = [
        f"Drone {i+1}" for i in range(10) 
        if f"Drone {i+1}" not in [d.get('name') for d in st.session_state.drone_data]
    ]
    
    if available_drone_names:
        selected_drone_name = st.selectbox("Select Drone Name", available_drone_names)
    else:
        st.warning("All default drone names are in use. Please enter a custom name.")
        selected_drone_name = st.text_input("Custom Drone Name", key="custom_drone_name")
    
    mission_start_time = st.text_input("Start Time (HHMM)")
    mission_end_time = st.text_input("End Time (HHMM)")
    
    # Waypoint selection
    location_map = st.session_state.location_descriptions
    waypoint_mapping = {v: k for k, v in location_map.items()}
    selected_waypoints = st.multiselect(
        "Select Waypoints (in order)", 
        list(location_map.values())
    )
    
    if st.button("Submit Mission Plan"):
        if not selected_waypoints or not mission_start_time or not mission_end_time:
            st.warning("Please complete all required fields.")
        else:
            waypoint_codes = [waypoint_mapping[wp] for wp in selected_waypoints]
            new_mission = {
                'name': selected_drone_name,
                'start_time': mission_start_time,
                'end_time': mission_end_time,
                'waypoints': waypoint_codes
            }
            
            # Check for potential conflicts
            conflicts, suggestions, _ = detect_collisions(
                new_mission, 
                st.session_state.drone_data, 
                st.session_state.waypoint_coordinates
            )
            
            st.session_state.drone_data.append(new_mission)
            st.success("Drone mission successfully added.")
            
            if conflicts:
                st.subheader("Potential Collision Detected")
                st.table(conflicts)
                st.subheader("Recommended Actions")
                st.table(suggestions)

# ---------- Page: Edit Drone Mission ----------
elif current_page == "Edit Drone Mission":
    st.header("Modify Existing Mission")
    
    if st.session_state.drone_data:
        drone_names = [d['name'] for d in st.session_state.drone_data]
        selected_drone = st.selectbox("Select Mission to Edit", drone_names)
        
        drone_to_edit = next(d for d in st.session_state.drone_data if d['name'] == selected_drone)
        
        updated_start = st.text_input("Start Time", drone_to_edit['start_time'])
        updated_end = st.text_input("End Time", drone_to_edit['end_time'])
        
        location_labels = st.session_state.location_descriptions
        updated_waypoints = st.multiselect(
            "Waypoints", 
            list(location_labels.values()),
            [location_labels[w] for w in drone_to_edit['waypoints']]
        )
        
        if st.button("Save Changes"):
            drone_to_edit['start_time'] = updated_start
            drone_to_edit['end_time'] = updated_end
            label_to_code = {v: k for k, v in location_labels.items()}
            drone_to_edit['waypoints'] = [label_to_code[wp] for wp in updated_waypoints]
            st.success("Mission successfully updated!")
    else:
        st.info("No drone missions available to edit.")

# ---------- Page: Drone Mission Table ----------
elif current_page == "Drone Mission Table":
    st.header("Current Mission Overview")
    
    if st.session_state.drone_data:
        location_names = st.session_state.location_descriptions
        mission_data = []
        
        for mission in st.session_state.drone_data:
            mission_data.append({
                "Drone": mission['name'],
                "Start": mission['start_time'],
                "End": mission['end_time'],
                "Waypoints": " → ".join([location_names[w] for w in mission['waypoints']])
            })
            
        st.table(mission_data)
    else:
        st.info("No active drone missions.")

# ---------- Page: Add New Destination ----------
elif current_page == "Add New Destination":
    st.header("Create New Waypoint")
    
    waypoint_code = st.text_input("Waypoint Identifier (e.g., D)").upper()
    location_name = st.text_input("Location Name (e.g., Police Station)")
    x_coord = st.number_input("X Coordinate")
    y_coord = st.number_input("Y Coordinate")
    z_coord = st.number_input("Z Coordinate (Altitude)")
    
    if st.button("Add Waypoint"):
        if waypoint_code and location_name:
            st.session_state.waypoint_coordinates[waypoint_code] = (x_coord, y_coord, z_coord)
            st.session_state.location_descriptions[waypoint_code] = location_name
            st.success(f"Added {location_name} as waypoint {waypoint_code}.")
        else:
            st.warning("Waypoint identifier and location name are required.")

# ---------- Page: 3D Path Visualization ----------
elif current_page == "3D Path Visualization":
    st.header("Interactive 3D Mission Visualization")
    
    waypoints = st.session_state.waypoint_coordinates
    location_names = st.session_state.location_descriptions
    missions = st.session_state.drone_data
    
    if not missions:
        st.info("No drone missions available for visualization.")
        st.stop()
    
    # Visualization mode selection
    col1, col2 = st.columns(2)
    with col1:
        visualization_mode = st.radio(
            "Visualization Mode",
            ["All missions", "Select specific drones"],
            index=0
        )
    
    # Drone selection based on mode
    if visualization_mode == "Select specific drones":
        with col2:
            selected_drones = st.multiselect(
                "Select drones to visualize",
                options=[m['name'] for m in missions],
                default=[missions[0]['name']] if missions else []
            )
        missions_to_show = [m for m in missions if m['name'] in selected_drones]
    else:
        missions_to_show = missions
    
    # Color selection for drones
    color_palette = ['#1f77b4', '#ff7f0e', '#2ca02c', '#d62728', '#9467bd', 
                    '#8c564b', '#e377c2', '#7f7f7f', '#bcbd22', '#17becf']
    
    # Initialize 3D visualization
    visualization = go.Figure()
    
    # Plot each selected mission path with unique color
    for idx, mission in enumerate(missions_to_show):
        mission_path = [waypoints[wp] for wp in mission['waypoints']]
        smooth_path = generate_interpolated_path(mission_path)
        
        if smooth_path:
            x_coords, y_coords, z_coords = zip(*smooth_path)
        else:
            x_coords, y_coords, z_coords = [], [], []
            
        hover_text = f"{mission['name']} ({mission['start_time']} - {mission['end_time']})"
        drone_color = color_palette[idx % len(color_palette)]
        
        visualization.add_trace(go.Scatter3d(
            x=x_coords, y=y_coords, z=z_coords,
            mode='lines',
            name=mission['name'],
            line=dict(color=drone_color, width=4),
            hoverinfo='text',
            text=[hover_text] * len(x_coords),
            legendgroup=mission['name'],
            showlegend=True
        ))
        
        # Add markers for the waypoints in this drone's path
        visualization.add_trace(go.Scatter3d(
            x=[waypoints[wp][0] for wp in mission['waypoints']],
            y=[waypoints[wp][1] for wp in mission['waypoints']],
            z=[waypoints[wp][2] for wp in mission['waypoints']],
            mode='markers',
            marker=dict(size=5, color=drone_color),
            name=f"{mission['name']} Waypoints",
            hoverinfo='text',
            text=[f"{mission['name']} - {location_names[wp]}" for wp in mission['waypoints']],
            legendgroup=mission['name'],
            showlegend=False
        ))
    
    # Check for and display collision paths between selected drones
    if len(missions_to_show) > 1:
        collision_detected = False
        for i in range(len(missions_to_show)):
            for j in range(i + 1, len(missions_to_show)):
                collisions, _, collision_segments = detect_collisions(
                    missions_to_show[i], 
                    [missions_to_show[j]], 
                    waypoints
                )
                
                if collisions:
                    collision_detected = True
                    for segment in collision_segments:
                        x_segment, y_segment, z_segment = zip(*segment)
                        visualization.add_trace(go.Scatter3d(
                            x=x_segment, y=y_segment, z=z_segment,
                            mode='lines',
                            line=dict(color='red', width=8),
                            name='Collision Zone',
                            hoverinfo='skip',
                            showlegend=False
                        ))
        
        if collision_detected:
            st.warning("Collision zones detected between selected drones (shown in red)")
    
    # Plot all waypoint markers with labels
    for code, (x, y, z) in waypoints.items():
        visualization.add_trace(go.Scatter3d(
            x=[x], y=[y], z=[z],
            mode='markers+text',
            marker=dict(size=8, color='green', symbol='diamond'),
            text=[location_names[code]],
            textposition="top center",
            hoverinfo='text',
            name=f"Waypoint {code}",
            showlegend=False
        ))
    
    # Configure visualization layout
    visualization.update_layout(
        scene=dict(
            xaxis_title='X Coordinate (m)',
            yaxis_title='Y Coordinate (m)',
            zaxis_title='Altitude (m)',
            aspectmode='data'
        ),
        title="Drone Mission Paths in 3D Space",
        showlegend=True,
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1
        ),
        margin=dict(l=0, r=0, b=0, t=40)
    )
    
    st.plotly_chart(visualization, use_container_width=True)
    
    # Display legend explanation
    st.markdown("""
    **Visualization Legend:**
    - Solid colored lines: Drone flight paths
    - Colored dots: Drone waypoints
    - Diamond markers: Location waypoints
    - Red lines: Collision zones between drones
    """)
