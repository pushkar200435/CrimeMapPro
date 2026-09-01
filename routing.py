import os
import joblib
import datetime
import pandas as pd
import numpy as np
import heapq

from encoder_helper import RobustLabelEncoder

# Primary Area Zone type for each Location/District
LOCATION_AREAS = {
    "Downtown": "Commercial",
    "Uptown": "Residential",
    "Suburbs": "Residential",
    "Westside": "Commercial",
    "Eastside": "Residential",
    "Industrial District": "Industrial",
    "Harbor Area": "Industrial",
    "Parkside": "Park"
}

# Coordinate map for city districts
COORDINATES = {
    "Downtown": (34.0522, -118.2437),
    "Uptown": (34.0822, -118.2837),
    "Suburbs": (34.1222, -118.1837),
    "Westside": (34.0422, -118.3437),
    "Eastside": (34.0322, -118.1937),
    "Industrial District": (34.0122, -118.2237),
    "Harbor Area": (33.7422, -118.2637),
    "Parkside": (34.0922, -118.2037)
}

# Connection network (symmetric undirected graph)
# Format: Node -> list of (Neighbor, Distance_km, BaseTime_mins)
GRAPH = {
    "Downtown": [("Uptown", 3.5, 8), ("Westside", 5.2, 12), ("Eastside", 4.1, 10), ("Industrial District", 3.2, 7)],
    "Uptown": [("Downtown", 3.5, 8), ("Parkside", 2.1, 5), ("Suburbs", 6.4, 15)],
    "Suburbs": [("Uptown", 6.4, 15), ("Parkside", 4.3, 9), ("Eastside", 8.5, 18)],
    "Westside": [("Downtown", 5.2, 12), ("Harbor Area", 7.6, 16)],
    "Eastside": [("Downtown", 4.1, 10), ("Industrial District", 2.2, 6), ("Suburbs", 8.5, 18)],
    "Industrial District": [("Downtown", 3.2, 7), ("Eastside", 2.2, 6), ("Harbor Area", 5.4, 11)],
    "Harbor Area": [("Industrial District", 5.4, 11), ("Westside", 7.6, 16)],
    "Parkside": [("Uptown", 2.1, 5), ("Suburbs", 4.3, 9)]
}

def get_location_risk_score(location, date_str, time_str, model_type="rf"):
    """
    Computes a risk score (0-100) and safety score (0-100) for a location.
    Uses ML predicted severity probabilities.
    """
    if location not in LOCATION_AREAS:
        return 20.0, "Low", 80.0
        
    area = LOCATION_AREAS[location]
    
    # Default fallbacks if models aren't loaded
    default_risk = 20.0
    default_level = "Low"
    default_safety = 80.0
    
    try:
        models_dir = "models"
        le_location_path = os.path.join(models_dir, "le_location.pkl")
        le_area_path = os.path.join(models_dir, "le_area.pkl")
        le_severity_path = os.path.join(models_dir, "le_severity.pkl")
        model_path = os.path.join(models_dir, f"severity_{model_type}.pkl")
        
        if not all(os.path.exists(p) for p in [le_location_path, le_area_path, le_severity_path, model_path]):
            return default_risk, default_level, default_safety
            
        le_location = joblib.load(le_location_path)
        le_area = joblib.load(le_area_path)
        le_severity = joblib.load(le_severity_path)
        model = joblib.load(model_path)
        
        # Parse datetime features
        date_obj = datetime.datetime.strptime(date_str, "%Y-%m-%d")
        month = date_obj.month
        day_of_week = date_obj.weekday()
        hour = int(time_str.split(':')[0]) if ':' in time_str else 12
        
        # Encode inputs safely
        loc_enc = le_location.transform(pd.Series([location]))[0]
        area_enc = le_area.transform(pd.Series([area]))[0]
        
        X = pd.DataFrame([[loc_enc, area_enc, hour, month, day_of_week]], columns=['Location', 'Area', 'Hour', 'Month', 'DayOfWeek'])
        
        # Predict severity probabilities
        probs = model.predict_proba(X)[0]
        classes = le_severity.classes_
        prob_map = dict(zip(classes, probs))
        
        high_prob = float(prob_map.get('High', 0.0))
        med_prob = float(prob_map.get('Medium', 0.0))
        low_prob = float(prob_map.get('Low', 0.0))
        
        # Calculate Risk Score: weights High (100), Med (50), Low (10)
        risk_score = (high_prob * 100.0) + (med_prob * 50.0) + (low_prob * 10.0)
        risk_score = round(min(max(risk_score, 0.0), 100.0), 2)
        
        # Risk level determination
        if risk_score > 55:
            level = "High"
        elif risk_score > 25:
            level = "Medium"
        else:
            level = "Low"
            
        safety_score = round(100.0 - risk_score, 2)
        return risk_score, level, safety_score
        
    except Exception as e:
        print(f"Error computing location risk score: {e}")
        return default_risk, default_level, default_safety

def dijkstra_routing(source, destination, date_str, time_str, model_type="rf", path_mode="shortest"):
    """
    Executes Dijkstra pathfinding.
    path_mode options:
      - 'shortest': Cost is physical distance.
      - 'safest': Cost is risk score of target node * multiplier + distance.
      - 'balanced': Cost is moderate combination of risk and distance.
    """
    # Pre-calculate risk scores for all nodes in the graph
    node_risks = {}
    for node in GRAPH.keys():
        risk, _, _ = get_location_risk_score(node, date_str, time_str, model_type)
        node_risks[node] = risk
        
    # Heap queue: (cost, current_node, path_list, total_dist, total_time)
    queue = [(0, source, [source], 0.0, 0)]
    visited = set()
    
    while queue:
        cost, node, path, dist, time = heapq.heappop(queue)
        
        if node == destination:
            # Calculate safety statistics for path
            path_safeties = [100.0 - node_risks[n] for n in path]
            avg_safety = round(sum(path_safeties) / len(path_safeties), 2)
            min_safety = round(min(path_safeties), 2)
            
            # Label overall safety classification
            if avg_safety < 45:
                safety_class = "High Risk"
            elif avg_safety < 75:
                safety_class = "Moderate Risk"
            else:
                safety_class = "Safest"
                
            return {
                "path": path,
                "distance": round(dist, 2),
                "time": time,
                "safety_score": avg_safety,
                "min_safety": min_safety,
                "safety_class": safety_class,
                "node_safeties": {n: round(100.0 - node_risks[n], 2) for n in path}
            }
            
        if node in visited:
            continue
        visited.add(node)
        
        for neighbor, edge_dist, edge_time in GRAPH[node]:
            if neighbor in visited:
                continue
                
            # Define edge weights based on pathing mode
            if path_mode == "shortest":
                edge_cost = edge_dist
            elif path_mode == "safest":
                # High cost weight on risk
                edge_cost = (node_risks[neighbor] * 8.0) + edge_dist
            else: # Balanced
                # Moderate cost weight on risk
                edge_cost = (node_risks[neighbor] * 2.0) + edge_dist
                
            heapq.heappush(queue, (
                cost + edge_cost,
                neighbor,
                path + [neighbor],
                dist + edge_dist,
                time + edge_time
            ))
            
    return None # Path not found (unconnected)

def get_route_options(source, destination, date_str, time_str, model_type="rf"):
    """
    Returns three route candidates: Safest, Shortest, and Balanced.
    """
    safest = dijkstra_routing(source, destination, date_str, time_str, model_type, "safest")
    shortest = dijkstra_routing(source, destination, date_str, time_str, model_type, "shortest")
    balanced = dijkstra_routing(source, destination, date_str, time_str, model_type, "balanced")
    
    # If paths are identical, remove duplicates or keep them for display
    return {
        "safest": safest,
        "shortest": shortest,
        "balanced": balanced
    }
