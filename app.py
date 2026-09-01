import os
import sqlite3
import pandas as pd
import numpy as np
import joblib
import json
import datetime
from flask import Flask, render_template, request, jsonify, send_file

import database
import chatbot
import routing
from train_model import train_all_models
from encoder_helper import RobustLabelEncoder
from db_setup import init_db

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = os.path.join('static', 'uploads')
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

# Initialize Database and Models on startup
def init_application():
    print("Checking database and models status...")
    db_exists = os.path.exists(database.DB_PATH)
    
    # Initialize DB (which also generates sample data if missing)
    init_db()
    
    # Check if models exist, if not, train them
    models_to_check = [
        "severity_rf.pkl", "crime_type_rf.pkl", "arrest_rf.pkl",
        "le_location.pkl", "le_area.pkl", "le_crime_type.pkl", "le_severity.pkl"
    ]
    models_missing = any(not os.path.exists(os.path.join("models", m)) for m in models_to_check)
    
    if models_missing or not db_exists:
        print("Models or database missing. Training machine learning models...")
        train_all_models()
    else:
        print("Database and models are ready.")

# Run initialization
init_application()

@app.route('/')
@app.route('/dashboard')
def dashboard():
    summary = database.get_dashboard_summary()
    
    # Load model metrics if they exist
    metrics = {}
    metrics_path = os.path.join("models", "metrics.json")
    if os.path.exists(metrics_path):
        with open(metrics_path, "r") as f:
            metrics = json.load(f)
            
    return render_template('dashboard.html', summary=summary, metrics=metrics)

@app.route('/predict')
def predict_page():
    # Fetch locations and areas to populate select forms
    conn = database.get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT DISTINCT Location FROM crimes ORDER BY Location")
    locations = [row[0] for row in cursor.fetchall()]
    cursor.execute("SELECT DISTINCT Area FROM crimes ORDER BY Area")
    areas = [row[0] for row in cursor.fetchall()]
    conn.close()
    
    return render_template('prediction.html', locations=locations, areas=areas)

@app.route('/map')
def map_page():
    return render_template('map.html')

@app.route('/map-raw')
def map_raw():
    import folium
    from folium.plugins import MarkerCluster, HeatMap
    
    # Fetch crimes from DB
    crimes = database.run_query("SELECT * FROM crimes LIMIT 1000") # Limit to 1000 for map performance
    
    if not crimes:
        # Fallback empty map
        m = folium.Map(location=[34.0522, -118.2437], zoom_start=12)
        return m._repr_html_()
        
    # Calculate map center
    lats = [c['Latitude'] for c in crimes if c['Latitude'] is not None]
    lons = [c['Longitude'] for c in crimes if c['Longitude'] is not None]
    
    avg_lat = sum(lats) / len(lats) if lats else 34.0522
    avg_lon = sum(lons) / len(lons) if lons else -118.2437
    
    # Create map with dark or standard theme
    # Cartodb dark_matter is highly professional and stunning for dashboards!
    m = folium.Map(location=[avg_lat, avg_lon], zoom_start=12, tiles="CartoDB dark_matter")
    
    # Marker cluster
    marker_cluster = MarkerCluster(name="Crime Markers").add_to(m)
    
    # Heatmap data
    heat_data = []
    
    for c in crimes:
        lat, lon = c['Latitude'], c['Longitude']
        if lat is None or lon is None:
            continue
            
        heat_data.append([lat, lon])
        
        # Color coding for Severity
        color = "red" if c['Severity'] == "High" else "orange" if c['Severity'] == "Medium" else "green"
        arrest_status = "Yes" if c['Arrest_Made'] == 1 else "No"
        
        popup_html = f"""
        <div style="font-family: 'Inter', sans-serif; font-size: 12px; color: #333; width: 200px;">
            <h4 style="margin: 0 0 5px 0; color: {color}; border-bottom: 1px solid #ddd; padding-bottom: 3px;">
                {c['Crime_Type']} ({c['Severity']} Risk)
            </h4>
            <b>ID:</b> {c['Crime_ID']}<br/>
            <b>Location:</b> {c['Location']} ({c['Area']})<br/>
            <b>Date:</b> {c['Date']} {c['Time']}<br/>
            <b>Arrest Made:</b> {arrest_status}
        </div>
        """
        
        folium.Marker(
            location=[lat, lon],
            popup=folium.Popup(popup_html, max_width=250),
            icon=folium.Icon(color="red" if c['Severity'] == "High" else "orange" if c['Severity'] == "Medium" else "blue", icon="info-sign")
        ).add_to(marker_cluster)
        
    # Add HeatMap
    HeatMap(heat_data, name="Crime Heatmap", radius=15, max_zoom=13).add_to(m)
    
    # Add layer control
    folium.LayerControl().add_to(m)
    
    return m._repr_html_()

@app.route('/chatbot')
def chatbot_page():
    return render_template('chatbot.html')

@app.route('/api/chat', methods=['POST'])
def api_chat():
    data = request.get_json() or {}
    message = data.get('message', '').strip()
    
    if not message:
        return jsonify({'response': "Please type a question, and I'll analyze the crime records for you!"})
        
    try:
        response = chatbot.get_chatbot_response(message)
        return jsonify({'response': response})
    except Exception as e:
        return jsonify({'response': f"An error occurred while compiling your insights: {str(e)}"})

@app.route('/api/predict', methods=['POST'])
def api_predict():
    data = request.get_json() or {}
    
    loc = data.get('location')
    area = data.get('area')
    date_str = data.get('date')
    time_str = data.get('time')
    model_type = data.get('model_type', 'rf') # Default to Random Forest
    
    if not all([loc, area, date_str, time_str]):
        return jsonify({'error': 'Missing parameters. Please provide location, area, date, and time.'}), 400
        
    try:
        # Load encoders
        le_location = joblib.load(os.path.join("models", "le_location.pkl"))
        le_area = joblib.load(os.path.join("models", "le_area.pkl"))
        le_crime_type = joblib.load(os.path.join("models", "le_crime_type.pkl"))
        le_severity = joblib.load(os.path.join("models", "le_severity.pkl"))
        
        # Load models
        model_ct = joblib.load(os.path.join("models", f"crime_type_{model_type}.pkl"))
        model_sev = joblib.load(os.path.join("models", f"severity_{model_type}.pkl"))
        model_arr = joblib.load(os.path.join("models", f"arrest_{model_type}.pkl"))
        
        # Parse inputs
        date_obj = datetime.datetime.strptime(date_str, "%Y-%m-%d")
        month = date_obj.month
        day_of_week = date_obj.weekday()
        
        hour = int(time_str.split(':')[0]) if ':' in time_str else 12
        
        # Transform inputs using encoders
        # RobustLabelEncoder transforms unknown categories to '<unknown>' class
        loc_enc = le_location.transform(pd.Series([loc]))[0]
        area_enc = le_area.transform(pd.Series([area]))[0]
        
        # Create input array
        # X order: ['Location', 'Area', 'Hour', 'Month', 'DayOfWeek']
        X = pd.DataFrame([[loc_enc, area_enc, hour, month, day_of_week]], columns=['Location', 'Area', 'Hour', 'Month', 'DayOfWeek'])
        
        # 1. Predict Crime Type
        pred_ct_class = model_ct.predict(X)[0]
        pred_ct = le_crime_type.inverse_transform([pred_ct_class])[0]
        
        # 2. Predict Severity (Risk Level)
        pred_sev_class = model_sev.predict(X)[0]
        pred_sev = le_severity.inverse_transform([pred_sev_class])[0]
        
        # 3. Predict Arrest Made probability
        pred_arr_prob = model_arr.predict_proba(X)[0]
        # class 1 index is usually 1 in binary classification, check shape
        arrest_prob = float(pred_arr_prob[1]) if len(pred_arr_prob) > 1 else float(pred_arr_prob[0])
        arrest_prob_pct = round(arrest_prob * 100, 2)
        
        # Get distributions/probabilities for outputs to visualize
        ct_probs = model_ct.predict_proba(X)[0]
        ct_classes = le_crime_type.inverse_transform(range(len(ct_probs)))
        ct_distribution = {c: round(float(p) * 100, 2) for c, p in zip(ct_classes, ct_probs) if c != '<unknown>'}
        
        sev_probs = model_sev.predict_proba(X)[0]
        sev_classes = le_severity.inverse_transform(range(len(sev_probs)))
        sev_distribution = {s: round(float(p) * 100, 2) for s, p in zip(sev_classes, sev_probs) if s != '<unknown>'}
        
        return jsonify({
            'success': True,
            'prediction': {
                'crime_type': pred_ct,
                'severity': pred_sev,
                'arrest_probability': arrest_prob_pct,
                'crime_type_distribution': ct_distribution,
                'severity_distribution': sev_distribution
            }
        })
        
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({'error': f"Prediction failed: {str(e)}"}), 500

@app.route('/api/upload', methods=['POST'])
def api_upload():
    if 'file' not in request.files:
        return jsonify({'error': 'No file uploaded'}), 400
        
    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'Empty filename'}), 400
        
    if not file.filename.endswith('.csv'):
        return jsonify({'error': 'Invalid file format. Please upload a CSV file.'}), 400
        
    try:
        # Save temporary
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], 'uploaded_crimes.csv')
        file.save(filepath)
        
        # Read and Validate CSV
        df = pd.read_csv(filepath)
        required_cols = ["Crime_ID", "Crime_Type", "Location", "Latitude", "Longitude", "Date", "Time", "Area", "Severity", "Arrest_Made"]
        missing_cols = [col for col in required_cols if col not in df.columns]
        
        if missing_cols:
            return jsonify({'error': f"Uploaded CSV is missing columns: {', '.join(missing_cols)}"}), 400
            
        # Clean data types
        df['Latitude'] = pd.to_numeric(df['Latitude'], errors='coerce')
        df['Longitude'] = pd.to_numeric(df['Longitude'], errors='coerce')
        df['Arrest_Made'] = pd.to_numeric(df['Arrest_Made'], errors='coerce').fillna(0).astype(int)
        df = df.dropna(subset=['Crime_ID', 'Crime_Type', 'Location', 'Date', 'Time'])
        
        # Save to SQLite database (replaces old)
        database.save_dataframe_to_db(df, replace=True)
        
        # Retrain models
        print("Uploaded data saved to SQLite. Retraining machine learning models...")
        train_all_models()
        
        return jsonify({
            'success': True,
            'message': f"CSV file uploaded and processed successfully. Loaded {len(df)} records into the database. ML models have been retrained!"
        })
        
    except Exception as e:
        return jsonify({'error': f"Failed to parse CSV: {str(e)}"}), 500

@app.route('/download-project')
def download_project():
    try:
        import subprocess
        # Call zip generator script to bundle the latest changes
        subprocess.run(['python', 'zip_project.py'], check=True)
        
        zip_path = "crime_prediction_system.zip"
        if os.path.exists(zip_path):
            return send_file(zip_path, as_attachment=True, download_name="crime_prediction_system.zip")
        else:
            return "ZIP file creation failed.", 500
    except Exception as e:
        return f"Error creating download bundle: {str(e)}", 500

@app.route('/routes')
def routes_page():
    conn = database.get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT DISTINCT Location FROM crimes ORDER BY Location")
    locations = [row[0] for row in cursor.fetchall()]
    conn.close()
    return render_template('routes.html', locations=locations)

@app.route('/api/route/predict', methods=['POST'])
def api_route_predict():
    data = request.get_json() or {}
    source = data.get('source')
    destination = data.get('destination')
    date_str = data.get('date')
    time_str = data.get('time')
    model_type = data.get('model_type', 'rf')
    
    if not all([source, destination, date_str, time_str]):
        return jsonify({'error': 'Missing parameters. Please provide source, destination, date, and time.'}), 400
        
    try:
        routes_data = routing.get_route_options(source, destination, date_str, time_str, model_type)
        if not routes_data or not routes_data.get('safest'):
            return jsonify({'error': 'Unable to calculate paths between the selected locations.'}), 404
            
        # Log the safest route prediction
        safest = routes_data['safest']
        dt_str = f"{date_str} {time_str}"
        database.log_route_prediction(source, destination, dt_str, safest['safety_score'], safest['distance'], safest['time'])
        
        return jsonify({
            'success': True,
            'routes': routes_data
        })
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({'error': f"Route calculation failed: {str(e)}"}), 500

@app.route('/api/safety-check', methods=['POST'])
def api_safety_check():
    data = request.get_json() or {}
    location = data.get('location')
    date_str = data.get('date')
    time_str = data.get('time')
    model_type = data.get('model_type', 'rf')
    
    if not all([location, date_str, time_str]):
        return jsonify({'error': 'Missing parameters. Please provide location, date, and time.'}), 400
        
    try:
        risk_score, level, safety_score = routing.get_location_risk_score(location, date_str, time_str, model_type)
        dt_str = f"{date_str} {time_str}"
        
        # Log the risk check
        database.log_risk_check(location, dt_str, level, safety_score)
        
        # Specific tip
        tips = chatbot.SAFETY_TIPS.get(location.lower(), chatbot.GENERAL_SAFETY)
        
        return jsonify({
            'success': True,
            'safety_score': safety_score,
            'risk_level': level,
            'risk_score': risk_score,
            'tips': tips[:3]
        })
    except Exception as e:
        return jsonify({'error': f"Safety check failed: {str(e)}"}), 500

@app.route('/map-route-raw')
def map_route_raw():
    import folium
    
    source = request.args.get('source')
    destination = request.args.get('destination')
    date_str = request.args.get('date')
    time_str = request.args.get('time')
    model_type = request.args.get('model_type', 'rf')
    
    if not all([source, destination, date_str, time_str]):
        # Default empty map
        m = folium.Map(location=[34.0522, -118.2437], zoom_start=12)
        return m._repr_html_()
        
    try:
        routes_data = routing.get_route_options(source, destination, date_str, time_str, model_type)
        if not routes_data or not routes_data.get('safest'):
            m = folium.Map(location=[34.0522, -118.2437], zoom_start=12)
            return m._repr_html_()
            
        # Draw Map centered at average of coordinates
        lats = [routing.COORDINATES[n][0] for n in [source, destination]]
        lons = [routing.COORDINATES[n][1] for n in [source, destination]]
        
        avg_lat = sum(lats) / len(lats)
        avg_lon = sum(lons) / len(lons)
        
        m = folium.Map(location=[avg_lat, avg_lon], zoom_start=12, tiles="CartoDB dark_matter")
        
        # Color coding configuration for routes
        path_configs = {
            'safest': {'color': '#10b981', 'weight': 7, 'opacity': 0.85, 'dash': None, 'name': 'Safest Route'},
            'balanced': {'color': '#f59e0b', 'weight': 5, 'opacity': 0.75, 'dash': None, 'name': 'Balanced Route'},
            'shortest': {'color': '#ef4444', 'weight': 4, 'opacity': 0.7, 'dash': '6, 6', 'name': 'Shortest Route'}
        }
        
        # Plot route polylines
        for mode, r_info in routes_data.items():
            if not r_info:
                continue
            path_coords = [routing.COORDINATES[node] for node in r_info['path']]
            
            folium.PolyLine(
                locations=path_coords,
                color=path_configs[mode]['color'],
                weight=path_configs[mode]['weight'],
                opacity=path_configs[mode]['opacity'],
                dash_array=path_configs[mode]['dash'],
                popup=f"<b>{path_configs[mode]['name']}</b><br/>Distance: {r_info['distance']} km<br/>Safety: {r_info['safety_score']}%"
            ).add_to(m)
            
        # Add Source and Destination markers
        # Source
        s_coord = routing.COORDINATES[source]
        folium.Marker(
            location=s_coord,
            popup=f"<b>Source: {source}</b>",
            icon=folium.Icon(color="blue", icon="play")
        ).add_to(m)
        
        # Destination
        d_coord = routing.COORDINATES[destination]
        folium.Marker(
            location=d_coord,
            popup=f"<b>Destination: {destination}</b>",
            icon=folium.Icon(color="green", icon="flag")
        ).add_to(m)
        
        # Add intermediate markers and nearby hotspots
        all_path_nodes = set()
        for r_info in routes_data.values():
            if r_info:
                all_path_nodes.update(r_info['path'])
                
        # Fetch crimes that occurred at these path locations to display nearby incidents
        conn = database.get_db_connection()
        cursor = conn.cursor()
        
        for node in all_path_nodes:
            if node in [source, destination]:
                continue
            # Plot intermediate nodes
            n_coord = routing.COORDINATES[node]
            safety_val = r_info['node_safeties'].get(node, 80.0)
            folium.CircleMarker(
                location=n_coord,
                radius=8,
                color="#3b82f6",
                fill=True,
                fill_color="#3b82f6",
                popup=f"<b>District: {node}</b><br/>Safety Level: {safety_val}%"
            ).add_to(m)
            
            # Hotspots near this node (retrieve recent high/medium crimes)
            cursor.execute("""
                SELECT Crime_Type, Severity, Latitude, Longitude FROM crimes 
                WHERE Location = ? AND Severity IN ('High', 'Medium') LIMIT 15
            """, (node,))
            
            for row in cursor.fetchall():
                c_type, sev, lat, lon = row
                if lat is None or lon is None:
                    continue
                color = "red" if sev == "High" else "orange"
                folium.Circle(
                    location=[lat, lon],
                    radius=40,
                    color=color,
                    fill=True,
                    fill_opacity=0.3,
                    popup=f"Incident: {c_type} ({sev} Risk)"
                ).add_to(m)
                
        conn.close()
        folium.LayerControl().add_to(m)
        return m._repr_html_()
        
    except Exception as e:
        print(f"Map rendering error: {e}")
        m = folium.Map(location=[34.0522, -118.2437], zoom_start=12)
        return m._repr_html_()

if __name__ == '__main__':
    app.run(debug=True, host='127.0.0.1', port=5000)
