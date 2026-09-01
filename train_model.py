import os
import joblib
import json
import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
from sklearn.tree import DecisionTreeClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.preprocessing import LabelEncoder
from sklearn.metrics import accuracy_score, precision_recall_fscore_support

import database

# Ensure models directory exists
MODELS_DIR = "models"
os.makedirs(MODELS_DIR, exist_ok=True)

from encoder_helper import RobustLabelEncoder

def train_all_models():
    print("Fetching dataset for model training...")
    df = database.get_all_crimes_df()
    
    if len(df) == 0:
        print("No crime data found in the database. Cannot train models.")
        return
        
    print(f"Loaded {len(df)} records. Starting data preprocessing...")
    
    # Feature Engineering
    df['Date'] = pd.to_datetime(df['Date'])
    df['Month'] = df['Date'].dt.month
    df['DayOfWeek'] = df['Date'].dt.dayofweek # Monday=0, Sunday=6
    
    # Parse hour from Time (format HH:MM)
    df['Hour'] = df['Time'].apply(lambda x: int(x.split(':')[0]) if isinstance(x, str) and ':' in x else 12)
    
    # Fit Encoders
    le_location = RobustLabelEncoder().fit(df['Location'])
    le_area = RobustLabelEncoder().fit(df['Area'])
    le_crime_type = RobustLabelEncoder().fit(df['Crime_Type'])
    le_severity = RobustLabelEncoder().fit(df['Severity'])
    
    # Save encoders
    joblib.dump(le_location, os.path.join(MODELS_DIR, "le_location.pkl"))
    joblib.dump(le_area, os.path.join(MODELS_DIR, "le_area.pkl"))
    joblib.dump(le_crime_type, os.path.join(MODELS_DIR, "le_crime_type.pkl"))
    joblib.dump(le_severity, os.path.join(MODELS_DIR, "le_severity.pkl"))
    
    # Transform features
    X = pd.DataFrame({
        'Location': le_location.transform(df['Location']),
        'Area': le_area.transform(df['Area']),
        'Hour': df['Hour'],
        'Month': df['Month'],
        'DayOfWeek': df['DayOfWeek']
    })
    
    # Target variables
    y_severity = le_severity.transform(df['Severity'])
    y_crime_type = le_crime_type.transform(df['Crime_Type'])
    y_arrest = df['Arrest_Made'].astype(int)
    
    targets = {
        'severity': (y_severity, 'severity'),
        'crime_type': (y_crime_type, 'crime_type'),
        'arrest': (y_arrest, 'arrest')
    }
    
    algorithms = {
        'rf': RandomForestClassifier(n_estimators=100, random_state=42),
        'dt': DecisionTreeClassifier(max_depth=10, random_state=42),
        'lr': LogisticRegression(max_iter=1000, random_state=42)
    }
    
    metrics_report = {}
    
    for target_name, (y, label) in targets.items():
        metrics_report[target_name] = {}
        
        # Train-test split
        X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
        
        for alg_name, clf in algorithms.items():
            print(f"Training {alg_name.upper()} model for predicting {target_name.upper()}...")
            
            # Fit model
            clf.fit(X_train, y_train)
            
            # Predict
            y_pred = clf.predict(X_test)
            
            # Calculate metrics
            acc = accuracy_score(y_test, y_pred)
            precision, recall, f1, _ = precision_recall_fscore_support(y_test, y_pred, average='weighted', zero_division=0)
            
            # Store metrics
            metrics_report[target_name][alg_name] = {
                'accuracy': round(float(acc), 4),
                'precision': round(float(precision), 4),
                'recall': round(float(recall), 4),
                'f1_score': round(float(f1), 4)
            }
            
            # Save trained model file
            model_filename = f"{target_name}_{alg_name}.pkl"
            joblib.dump(clf, os.path.join(MODELS_DIR, model_filename))
            
    # Save metrics JSON
    with open(os.path.join(MODELS_DIR, "metrics.json"), "w") as f:
        json.dump(metrics_report, f, indent=4)
        
    print("All models and encoders trained and saved successfully!")
    return metrics_report

if __name__ == "__main__":
    train_all_models()
