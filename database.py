import sqlite3
import pandas as pd
import os

DB_PATH = "crime_analysis.db"

def get_db_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def get_all_crimes_df():
    """Returns all crimes as a pandas DataFrame for ML model training."""
    conn = get_db_connection()
    df = pd.read_sql_query("SELECT * FROM crimes", conn)
    conn.close()
    return df

def save_dataframe_to_db(df, replace=True):
    """Saves a pandas DataFrame of crimes to the database."""
    conn = get_db_connection()
    if replace:
        cursor = conn.cursor()
        cursor.execute("DROP TABLE IF EXISTS crimes")
        cursor.execute("""
        CREATE TABLE crimes (
            Crime_ID TEXT PRIMARY KEY,
            Crime_Type TEXT,
            Location TEXT,
            Latitude REAL,
            Longitude REAL,
            Date TEXT,
            Time TEXT,
            Area TEXT,
            Severity TEXT,
            Arrest_Made INTEGER
        )
        """)
        conn.commit()
    
    # Save the dataframe
    df.to_sql("crimes", conn, if_exists="append", index=False)
    conn.commit()
    conn.close()

def get_dashboard_summary():
    """Gathers all summary statistics for the dashboard."""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    summary = {}
    
    # Total Crimes
    cursor.execute("SELECT COUNT(*) FROM crimes")
    summary['total_crimes'] = cursor.fetchone()[0]
    
    if summary['total_crimes'] == 0:
        conn.close()
        return {
            'total_crimes': 0, 'arrest_rate': 0, 'high_severity_pct': 0,
            'crime_types': [], 'monthly_trends': [], 'location_stats': [],
            'safe_routes_count': 0, 'live_checks_count': 0, 'high_risk_areas_count': 0
        }
        
    # Arrests and Arrest Rate
    cursor.execute("SELECT COUNT(*) FROM crimes WHERE Arrest_Made = 1")
    arrests = cursor.fetchone()[0]
    summary['arrest_rate'] = round((arrests / summary['total_crimes']) * 100, 2)
    
    # High Severity Crimes Percentage
    cursor.execute("SELECT COUNT(*) FROM crimes WHERE Severity = 'High'")
    high_sev = cursor.fetchone()[0]
    summary['high_severity_pct'] = round((high_sev / summary['total_crimes']) * 100, 2)
    
    # Crime Type Distribution
    cursor.execute("SELECT Crime_Type, COUNT(*) as count FROM crimes GROUP BY Crime_Type ORDER BY count DESC")
    summary['crime_types'] = [{'name': row[0], 'value': row[1]} for row in cursor.fetchall()]
    
    # Area-wise Crime Count
    cursor.execute("SELECT Location, COUNT(*) as count FROM crimes GROUP BY Location ORDER BY count DESC")
    summary['location_stats'] = [{'name': row[0], 'value': row[1]} for row in cursor.fetchall()]
    
    # Monthly Trends (grouped by Year-Month)
    cursor.execute("""
        SELECT substr(Date, 1, 7) as month, COUNT(*) as count 
        FROM crimes 
        GROUP BY month 
        ORDER BY month ASC
    """)
    summary['monthly_trends'] = [{'month': row[0], 'count': row[1]} for row in cursor.fetchall()]
    
    # Safe Routes count from route_logs
    try:
        cursor.execute("SELECT COUNT(*) FROM route_logs")
        summary['safe_routes_count'] = cursor.fetchone()[0]
    except Exception:
        summary['safe_routes_count'] = 0
        
    # Live Risk Assessments count from risk_checks
    try:
        cursor.execute("SELECT COUNT(*) FROM risk_checks")
        summary['live_checks_count'] = cursor.fetchone()[0]
    except Exception:
        summary['live_checks_count'] = 0
        
    # High-Risk Areas Detected (Locations with high count of High severity incidents, e.g. > 20)
    try:
        cursor.execute("SELECT COUNT(*) FROM (SELECT Location FROM crimes WHERE Severity = 'High' GROUP BY Location HAVING COUNT(*) > 20)")
        summary['high_risk_areas_count'] = cursor.fetchone()[0]
    except Exception:
        summary['high_risk_areas_count'] = 0
    
    conn.close()
    return summary

def log_route_prediction(source, destination, datetime_str, safety_score, distance, travel_time):
    """Logs a calculated route path into route_logs table."""
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("""
            INSERT INTO route_logs (Source, Destination, DateTime, Safety_Score, Distance, Travel_Time)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (source, destination, datetime_str, safety_score, distance, travel_time))
        conn.commit()
    except Exception as e:
        print(f"Error logging route prediction: {e}")
    finally:
        conn.close()

def log_risk_check(location, datetime_str, risk_level, safety_score):
    """Logs a location safety check into risk_checks table."""
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("""
            INSERT INTO risk_checks (Location, DateTime, Risk_Level, Safety_Score)
            VALUES (?, ?, ?, ?)
        """, (location, datetime_str, risk_level, safety_score))
        conn.commit()
    except Exception as e:
        print(f"Error logging risk check: {e}")
    finally:
        conn.close()

def run_query(query, params=()):
    """Executes a custom SQL select query and returns list of dictionaries."""
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute(query, params)
        columns = [column[0] for column in cursor.description]
        results = []
        for row in cursor.fetchall():
            results.append(dict(zip(columns, row)))
        return results
    except Exception as e:
        print(f"Database query error: {e}")
        return []
    finally:
        conn.close()
