# 🚨 CrimeMap – Crime Analysis & Prediction System

**CrimeMap** is a web-based crime analysis and prediction system designed to visualize crime data, analyze historical crime patterns, predict crime-related outcomes using machine learning, assess location-based safety risks, and recommend safer routes.

The application is built using **Python, Flask, SQLite, Pandas, Scikit-learn, Joblib, and Folium**.

---

## ✨ Features

### 📊 Crime Analytics Dashboard

* Displays total recorded crimes.
* Shows arrest clearance rate.
* Displays high-severity crime percentage.
* Provides crime-type distribution.
* Provides location-wise crime statistics.
* Displays monthly crime trends.
* Tracks route predictions and safety checks.

### 🗺️ Interactive Crime Map

* Visualizes crime locations on an interactive map.
* Displays individual crime markers.
* Groups nearby markers using marker clustering.
* Provides a crime heatmap.
* Displays crime type and severity information.
* Shows whether an arrest was made for a recorded incident.

The map is generated using **Folium** with an interactive layer control.

### 🤖 Machine Learning Crime Prediction

The system uses machine-learning models to predict:

* Crime Type
* Crime Severity / Risk Level
* Arrest Probability

Three machine-learning algorithms are trained:

* **Random Forest**
* **Decision Tree**
* **Logistic Regression**

The system evaluates models using:

* Accuracy
* Precision
* Recall
* F1 Score

The trained models and encoders are stored using **Joblib**.

### 🛡️ Location Safety Assessment

Users can check the predicted risk level of a monitored location based on:

* Location
* Area
* Date
* Time

The system calculates:

* Risk Score
* Risk Level
* Safety Score

Risk levels are classified as:

* 🟢 Low
* 🟡 Medium
* 🔴 High

### 🧭 Safest Route Recommendation

CrimeMap provides multiple route options between supported locations:

* **Safest Route**
* **Shortest Route**
* **Balanced Route**

The routing system uses **Dijkstra's algorithm** and incorporates predicted crime risk into route costs.

Routes provide information such as:

* Path
* Distance
* Estimated travel time
* Safety score
* Safety classification

### 💬 Crime Safety Chatbot

The built-in chatbot can answer questions about:

* Crime statistics
* Crime hotspots
* Safest areas
* Crime trends
* Arrest statistics
* Location-specific crime information
* Safety recommendations
* Crime-specific safety tips
* Route recommendations
* Machine-learning predictions

The chatbot retrieves information from the SQLite crime database and provides contextual safety recommendations.

### 📁 CSV Dataset Upload

Users can upload a crime dataset in CSV format.

The application:

1. Validates the uploaded CSV.
2. Checks required columns.
3. Converts required data types.
4. Stores the data in SQLite.
5. Retrains the machine-learning models.

Required CSV columns:

```text
Crime_ID
Crime_Type
Location
Latitude
Longitude
Date
Time
Area
Severity
Arrest_Made
```

---

## 🧠 Machine Learning Workflow

The machine-learning pipeline performs feature engineering using:

```text
Location
Area
Hour
Month
DayOfWeek
```

The date is converted into:

* Month
* Day of week

The time is converted into:

* Hour

Categorical values such as location, area, crime type, and severity are encoded before model training.

A custom `RobustLabelEncoder` is used so that previously unseen categories can be handled through an `<unknown>` class.

## The project trains Random Forest, Decision Tree, and Logistic Regression classifiers and stores their evaluation metrics in `metrics.json`.

## 🛣️ Route Safety Algorithm

The route engine represents the supported locations as a graph.

Dijkstra's algorithm is used to calculate different route types.

### Shortest Route

Uses physical distance as the primary cost.

### Safest Route

Gives greater importance to predicted crime risk.

### Balanced Route

Combines distance and crime risk to produce a compromise between safety and travel distance.

## The route system calculates safety statistics for the selected path and returns a safety classification.

## 🗄️ Database

CrimeMap uses **SQLite** for local data storage.

The database contains tables for:

### `crimes`

Stores crime records including:

* Crime ID
* Crime type
* Location
* Latitude
* Longitude
* Date
* Time
* Area
* Severity
* Arrest status

### `route_logs`

Stores calculated route predictions.

### `risk_checks`

Stores location safety assessments.

## The database initialization script automatically creates the required tables and can seed the database with generated sample crime data when the database is empty.

## 📂 Project Structure

A typical project structure is:

```text
CrimeMap/
│
├── app.py
├── chatbot.py
├── database.py
├── db_setup.py
├── encoder_helper.py
├── generate_sample_data.py
├── routing.py
├── train_model.py
│
├── crime_analysis.db
│
├── datasets/
│   └── sample_crimes.csv
│
├── models/
│   ├── severity_rf.pkl
│   ├── severity_dt.pkl
│   ├── severity_lr.pkl
│   ├── crime_type_rf.pkl
│   ├── crime_type_dt.pkl
│   ├── crime_type_lr.pkl
│   ├── arrest_rf.pkl
│   ├── arrest_dt.pkl
│   ├── arrest_lr.pkl
│   ├── le_location.pkl
│   ├── le_area.pkl
│   ├── le_crime_type.pkl
│   ├── le_severity.pkl
│   └── metrics.json
│
├── templates/
│   ├── dashboard.html
│   ├── prediction.html
│   ├── map.html
│   ├── chatbot.html
│   └── routes.html
│
└── static/
    └── ...
```

---

## 🛠️ Technologies Used

| Technology           | Purpose                   |
| -------------------- | ------------------------- |
| Python               | Core programming language |
| Flask                | Web application framework |
| SQLite               | Database                  |
| Pandas               | Data processing           |
| NumPy                | Numerical operations      |
| Scikit-learn         | Machine learning          |
| Joblib               | Model serialization       |
| Folium               | Interactive maps          |
| HTML/CSS/JavaScript  | Frontend                  |
| Dijkstra's Algorithm | Route optimization        |

---

## ⚙️ Installation

### 1. Clone the repository

```bash
git clone https://github.com/YOUR_USERNAME/CrimeMap.git
```

Move into the project directory:

```bash
cd CrimeMap
```

### 2. Create a virtual environment

Windows:

```bash
python -m venv venv
```

Activate it:

```bash
venv\Scripts\activate
```

### 3. Install dependencies

If the project contains a `requirements.txt` file:

```bash
pip install -r requirements.txt
```

Otherwise install the main dependencies:

```bash
pip install flask pandas numpy scikit-learn joblib folium
```

### 4. Initialize the database

```bash
python db_setup.py
```

The database initialization process creates the required SQLite tables and generates/loads sample crime data when necessary.

### 5. Train the machine-learning models

```bash
python train_model.py
```

The training script preprocesses the crime data, creates features, trains the three supported algorithms, evaluates them, and saves the resulting models.

### 6. Start the application

```bash
python app.py
```

Open the URL shown in the terminal, usually:

```text
http://127.0.0.1:5000
```

---

## 🔮 Prediction Process

The prediction API accepts:

```text
Location
Area
Date
Time
```

The application converts the date and time into machine-learning features and uses the trained models to predict crime type, severity, and arrest probability.

The prediction response includes:

```text
Crime Type
Severity
Arrest Probability
Crime Type Distribution
Severity Distribution
```

---

## 📤 Dataset Upload

CrimeMap supports uploading a CSV dataset directly through the application.

The uploaded file is validated against the required schema before being saved to SQLite. After successful upload, the machine-learning models are retrained automatically.

Example:

```csv
Crime_ID,Crime_Type,Location,Latitude,Longitude,Date,Time,Area,Severity,Arrest_Made
CRM-00001,Theft,Downtown,34.0522,-118.2437,2026-01-10,14:30,Commercial,Medium,0
```

---

## ⚠️ Important Disclaimer

This project is intended for **educational, research, and demonstration purposes**.

Crime predictions and safety scores are generated from the available dataset and machine-learning models. They should **not be treated as definitive predictions of criminal activity or used as the sole basis for real-world law-enforcement, legal, or personal safety decisions**.

The sample dataset is synthetic/generated data and should not be interpreted as real-world crime statistics.

---

## 🚀 Future Improvements

Possible future improvements include:

* Real-time crime-data integration
* Live geographic APIs
* Real-world navigation integration
* More advanced machine-learning models
* Deep-learning-based prediction
* Real-time notifications
* User authentication
* Admin dashboard
* Larger and more diverse datasets
* Improved geospatial analysis
* Mobile application
* Cloud deployment
* Model explainability using SHAP/LIME

---

## 👨‍💻 Project

**Project Name:** CrimeMap
**Category:** Crime Analysis & Prediction System
**Architecture:** Flask Web Application + SQLite + Machine Learning
