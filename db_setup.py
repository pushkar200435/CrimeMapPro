import os
import sqlite3
import pandas as pd
from generate_sample_data import generate_sample_data

DB_PATH = "crime_analysis.db"
CSV_PATH = "datasets/sample_crimes.csv"

def init_db():
    print("Initializing SQLite Database...")
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Create crimes table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS crimes (
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
    
    # Create route_logs table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS route_logs (
        Route_ID INTEGER PRIMARY KEY AUTOINCREMENT,
        Source TEXT,
        Destination TEXT,
        DateTime TEXT,
        Safety_Score REAL,
        Distance REAL,
        Travel_Time INTEGER
    )
    """)

    # Create risk_checks table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS risk_checks (
        Check_ID INTEGER PRIMARY KEY AUTOINCREMENT,
        Location TEXT,
        DateTime TEXT,
        Risk_Level TEXT,
        Safety_Score REAL
    )
    """)
    
    conn.commit()
    print("Tables 'crimes', 'route_logs', and 'risk_checks' initialized successfully.")
    
    # Check if table is empty, seed if empty
    cursor.execute("SELECT COUNT(*) FROM crimes")
    count = cursor.fetchone()[0]
    
    if count == 0:
        print("Database is empty. Seeding with sample data...")
        if not os.path.exists(CSV_PATH):
            generate_sample_data(CSV_PATH)
            
        # Load CSV using pandas and write to sqlite
        try:
            df = pd.read_csv(CSV_PATH)
            df.to_sql("crimes", conn, if_exists="append", index=False)
            conn.commit()
            print(f"Database seeded successfully with {len(df)} records.")
        except Exception as e:
            print(f"Error seeding database: {e}")
    else:
        print(f"Database already contains {count} records. Seeding skipped.")
        
    conn.close()

if __name__ == "__main__":
    init_db()
