# uav_deconfliction
This repository contains all the content of UAV Strategic Deconfliction in Shared Airspace
# UAV Strategic Deconfliction System

A modular, scalable system for detecting and resolving spatial and temporal conflicts in UAV (drone) flight paths. Built using Streamlit for an interactive frontend and Python-based logic for backend calculations, the system is designed to ensure safety in shared airspace.

## Features

- **Interactive Streamlit Interface** for mission entry and visualization
- **3D Path Visualization** using Plotly
- **Spatial Conflict Detection** based on 3D Euclidean distance
- **Temporal Conflict Checks** using mission time windows
- **Edge Case Handling** (e.g., single-waypoint missions, vertical stacking)
- **Modular Architecture** with separated logic for UI, computation, and data
- **Tested Algorithms** using pytest
- **Designed for Scalability** to handle 10,000+ drone missions

---

## Architecture

The system follows a three-layer architecture:

### 1. Presentation Layer (Streamlit UI)
- Rapid prototyping with interactive forms and visualizations
- Uses dropdowns and sidebar navigation for multi-page layout

### 2. Business Logic Layer (Path Calculations)
- Stateless functions for:
  - Linear path interpolation
  - 3D distance-based collision detection
  - Time-window comparisons for temporal checks

### 3. Data Layer (Session State)
- Streamlit's session state is used to manage user inputs and mission persistence across pages

---

## How It Works

1. Users define UAV missions by selecting waypoints and entry time (in `HHMM` format)
2. The system maps waypoint names to coordinates
3. Linear paths are generated and interpolated between points
4. All path segments are checked for spatial overlap (within a safety margin)
5. Overlapping missions are flagged if their time windows intersect

---

## Getting Started

### Prerequisites

- Python 3.9+
- pip

### Installation


cd UAV-Deconfliction-System
pip install -r requirements.txt


Run the App

streamlit run app.py


