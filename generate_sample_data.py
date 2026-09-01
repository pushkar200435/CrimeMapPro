import os
import csv
import random
import datetime

def generate_sample_data(output_path="datasets/sample_crimes.csv", num_records=2000):
    # Ensure directory exists
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    crime_types = ["Theft", "Assault", "Burglary", "Robbery", "Vandalism", "Drug Offense", "Fraud", "Shoplifting"]
    locations = ["Downtown", "Uptown", "Suburbs", "Westside", "Eastside", "Industrial District", "Harbor Area", "Parkside"]
    
    # Location coordinates centers (lat, lon)
    location_coordinates = {
        "Downtown": (34.0522, -118.2437),
        "Uptown": (34.0822, -118.2837),
        "Suburbs": (34.1222, -118.1837),
        "Westside": (34.0422, -118.3437),
        "Eastside": (34.0322, -118.1937),
        "Industrial District": (34.0122, -118.2237),
        "Harbor Area": (33.7422, -118.2637),
        "Parkside": (34.0922, -118.2037)
    }
    
    areas = {
        "Downtown": ["Commercial", "Transit Station", "Nightclub District"],
        "Uptown": ["Residential", "Commercial", "Park"],
        "Suburbs": ["Residential", "School Zone", "Park"],
        "Westside": ["Residential", "Commercial", "Transit Station"],
        "Eastside": ["Residential", "Industrial", "Commercial"],
        "Industrial District": ["Industrial", "Transit Station"],
        "Harbor Area": ["Industrial", "Commercial", "Transit Station"],
        "Parkside": ["Park", "Residential", "School Zone"]
    }
    
    start_date = datetime.date(2024, 1, 1)
    end_date = datetime.date(2026, 6, 1)
    date_delta = end_date - start_date
    
    with open(output_path, mode="w", newline="") as file:
        writer = csv.writer(file)
        writer.writerow(["Crime_ID", "Crime_Type", "Location", "Latitude", "Longitude", "Date", "Time", "Area", "Severity", "Arrest_Made"])
        
        for idx in range(1, num_records + 1):
            crime_id = f"CRM-{idx:05d}"
            
            # Select Location
            loc = random.choice(locations)
            lat_center, lon_center = location_coordinates[loc]
            # Add small gaussian noise to make markers cluster realistically on map
            lat = lat_center + random.gauss(0, 0.008)
            lon = lon_center + random.gauss(0, 0.008)
            
            # Select Area based on location
            area = random.choice(areas[loc])
            
            # Time of crime (HH:MM)
            hour = random.randint(0, 23)
            minute = random.randint(0, 59)
            time_str = f"{hour:02d}:{minute:02d}"
            
            # Crime type and severity correlations
            # Certain areas/times favor certain crimes
            if area == "Nightclub District" and hour >= 20 or hour <= 3:
                crime_type = random.choices(["Assault", "Robbery", "Theft"], weights=[0.4, 0.2, 0.4])[0]
            elif area == "Industrial" and (hour >= 20 or hour <= 5):
                crime_type = random.choices(["Burglary", "Vandalism", "Theft"], weights=[0.5, 0.3, 0.2])[0]
            elif area == "Park" and (hour >= 18 or hour <= 4):
                crime_type = random.choices(["Vandalism", "Drug Offense", "Assault"], weights=[0.4, 0.4, 0.2])[0]
            elif area == "School Zone":
                crime_type = random.choices(["Vandalism", "Theft", "Shoplifting"], weights=[0.3, 0.4, 0.3])[0]
            elif area == "Commercial" and hour >= 9 and hour <= 18:
                crime_type = random.choices(["Shoplifting", "Theft", "Fraud"], weights=[0.5, 0.3, 0.2])[0]
            else:
                crime_type = random.choice(crime_types)
            
            # Define severity based on crime type
            if crime_type in ["Assault", "Robbery"]:
                severity = random.choices(["High", "Medium"], weights=[0.8, 0.2])[0]
            elif crime_type in ["Burglary", "Theft", "Drug Offense"]:
                severity = random.choices(["Medium", "High", "Low"], weights=[0.7, 0.2, 0.1])[0]
            else: # Vandalism, Shoplifting, Fraud
                severity = random.choices(["Low", "Medium"], weights=[0.8, 0.2])[0]
                
            # Arrest Made probability
            # Higher arrest rates for Drug Offense, Assault
            # Lower for Theft, Burglary
            if crime_type == "Drug Offense":
                arrest_prob = 0.85
            elif crime_type == "Assault":
                arrest_prob = 0.60
            elif crime_type in ["Theft", "Burglary", "Vandalism"]:
                arrest_prob = 0.15
            elif crime_type == "Shoplifting":
                arrest_prob = 0.40
            else: # Robbery, Fraud
                arrest_prob = 0.30
                
            arrest_made = 1 if random.random() < arrest_prob else 0
            
            # Generate date
            random_days = random.randint(0, date_delta.days)
            crime_date = start_date + datetime.timedelta(days=random_days)
            date_str = crime_date.strftime("%Y-%m-%d")
            
            writer.writerow([crime_id, crime_type, loc, f"{lat:.6f}", f"{lon:.6f}", date_str, time_str, area, severity, arrest_made])
            
    print(f"Sample crime dataset generated successfully with {num_records} records at {output_path}!")

if __name__ == "__main__":
    generate_sample_data()
