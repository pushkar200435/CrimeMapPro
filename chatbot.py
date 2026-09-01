import sqlite3
import re
import database

# Safety tips mapping for different crime types
SAFETY_TIPS = {
    "assault": [
        "Stay in well-lit, populated areas, especially at night.",
        "Be aware of your surroundings and avoid walking alone with headphones on.",
        "If you feel threatened, head toward a public place with people or call emergency services immediately.",
        "Keep your phone accessible but not in a distracting manner."
    ],
    "theft": [
        "Never leave valuables unattended in public places.",
        "Secure your personal belongings, lock zippers on backpacks, and hold purses close to your body.",
        "Secure digital devices and avoid flashing expensive items in public.",
        "Report lost or stolen bank cards immediately to prevent unauthorized use."
    ],
    "burglary": [
        "Ensure all doors, windows, and gates are locked securely before leaving home.",
        "Install motion-sensor lighting around your home's exterior and entry points.",
        "Do not advertise when you are away from home on social media.",
        "Consider installing a security system or smart video doorbell."
    ],
    "robbery": [
        "Avoid carrying large amounts of cash or wearing expensive jewelry in public.",
        "Be alert when using ATMs, especially after dark; choose well-lit, high-traffic locations.",
        "If confronted, prioritize your personal safety over physical possessions. Co-operate and call the police as soon as it is safe.",
        "Walk confidently and purposefully to avoid looking like an easy target."
    ],
    "vandalism": [
        "Report graffiti, broken windows, and property damage immediately to local authorities.",
        "Improve property security with fencing, security cameras, and good lighting.",
        "Install secure gates and barriers to discourage unauthorized access to private property.",
        "Keep vehicles in secure garages or well-lit, visible parking spaces."
    ],
    "drug offense": [
        "Avoid areas known for illegal drug activity or loitering.",
        "If you suspect illegal drug sales or usage in your neighborhood, report it anonymously to local police.",
        "Support local youth and community programs aimed at drug awareness and prevention."
    ],
    "fraud": [
        "Never share sensitive personal information, passwords, or PINs via email, phone, or text.",
        "Review bank statements regularly for unauthorized charges or suspicious transactions.",
        "Be skeptical of unsolicited calls or emails claiming you won a prize or owe urgent taxes.",
        "Use secure, verified payment methods when shopping online."
    ],
    "shoplifting": [
        "Train retail staff to identify suspicious behavior and greet all customers.",
        "Utilize mirrors, cameras, and security tags on high-value merchandise.",
        "Keep shelves organized and ensure there are no blind spots in store layouts."
    ]
}

GENERAL_SAFETY = [
    "Always plan your route in advance, especially when visiting unfamiliar areas.",
    "Keep emergency contact numbers saved on speed dial.",
    "Trust your instincts: if a situation or location feels unsafe, leave immediately.",
    "Keep friends or family informed about your location and expected arrival times."
]

def clean_input(text):
    return re.sub(r'[^\w\s]', '', text.lower().strip())

def get_chatbot_response(user_query):
    query_clean = clean_input(user_query)
    
    # 1. Check for specific locations in the query
    locations = ["downtown", "uptown", "suburbs", "westside", "eastside", "industrial district", "harbor area", "parkside"]
    matched_location = None
    for loc in locations:
        if loc in query_clean:
            matched_location = loc
            break
            
    # 2. Check for specific crime types
    crime_types = ["theft", "assault", "burglary", "robbery", "vandalism", "drug offense", "fraud", "shoplifting"]
    matched_crime = None
    for crime in crime_types:
        if crime in query_clean:
            matched_crime = crime
            break

    # Helper: Fetch general database counts
    conn = database.get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM crimes")
    total_crimes = cursor.fetchone()[0]
    
    if total_crimes == 0:
        conn.close()
        return "The database is currently empty. Please upload a crime dataset to get dynamic insights!"

    # --- ANSWER ROUTING ---
    
    # Route matching list
    matched_locs = []
    for loc in locations:
        if loc in query_clean:
            matched_locs.append(loc)

    # 1. Routing Queries (takes precedence if two locations matched)
    if len(matched_locs) >= 2 and any(k in query_clean for k in ["route", "path", "go from", "travel", "navigate", "safest way"]):
        import routing
        src = matched_locs[0].title()
        dst = matched_locs[1].title()
        now = datetime.datetime.now()
        date_str = now.strftime("%Y-%m-%d")
        time_str = now.strftime("%H:%M")
        
        route_info = routing.dijkstra_routing(src, dst, date_str, time_str, "rf", "safest")
        if route_info:
            path_str = " → ".join(route_info['path'])
            response = f"I've calculated the **Safest Route** from **{src}** to **{dst}** based on current risk matrices:\n\n"
            response += f"- **Path**: `{path_str}`\n"
            response += f"- **Distance**: **{route_info['distance']} km**\n"
            response += f"- **Estimated Time**: **{route_info['time']} mins**\n"
            response += f"- **Safety Score**: **{route_info['safety_score']}%** (Classified: **{route_info['safety_class']}**)\n\n"
            
            high_risk_nodes = [node for node, safety in route_info['node_safeties'].items() if safety < 55]
            if high_risk_nodes:
                response += f"⚠️ **Warning**: This route traverses **{', '.join(high_risk_nodes)}**, which currently carry elevated crime risks. Exercise caution."
            else:
                response += "✅ This path is currently clear of high-risk districts."
        else:
            response = f"I could not compute a routing path between **{src}** and **{dst}**. Please verify if they are connected."

    # 2. Avoid/Dangerous Areas Queries
    elif any(k in query_clean for k in ["avoid", "dangerous area", "unsafe area", "stay away", "places to avoid"]):
        import routing
        now = datetime.datetime.now()
        date_str = now.strftime("%Y-%m-%d")
        time_str = now.strftime("%H:%M")
        
        high_risk = []
        for loc in locations:
            _, level, safety = routing.get_location_risk_score(loc.title(), date_str, time_str, "rf")
            if level == "High" or safety < 50:
                high_risk.append((loc.title(), safety))
                
        high_risk.sort(key=lambda x: x[1])
        
        if high_risk:
            avoid_list = "\n".join([f"- **{loc}** (Safety Index: **{safety}%**)" for loc, safety in high_risk])
            response = f"Based on current hourly safety matrices, you should avoid or exercise caution in these **high-risk areas**:\n\n{avoid_list}"
        else:
            cursor.execute("SELECT Location, COUNT(*) as count FROM crimes GROUP BY Location ORDER BY count DESC LIMIT 2")
            rows = cursor.fetchall()
            avoid_list = "\n".join([f"- **{row[0]}** ({row[1]} historical crimes)" for row in rows])
            response = f"No locations are currently flagged as high risk for this hour. However, historically, you should exercise caution in:\n\n{avoid_list}"

    # 3. Specific Location Risk/Safety Check Queries
    elif any(k in query_clean for k in ["my location", "current location", "risk at", "safety check"]):
        if matched_location:
            loc_title = matched_location.title()
            import routing
            now = datetime.datetime.now()
            date_str = now.strftime("%Y-%m-%d")
            time_str = now.strftime("%H:%M")
            risk_score, level, safety_score = routing.get_location_risk_score(loc_title, date_str, time_str, "rf")
            
            response = f"**Safety Assessment for {loc_title}** (Current Time: {time_str}):\n"
            response += f"- Safety Index: **{safety_score}%**\n"
            response += f"- Risk Level: **{level} Risk**\n\n"
            
            tips = SAFETY_TIPS.get(matched_location.lower(), GENERAL_SAFETY)
            response += "Recommendations:\n" + "\n".join([f"- {tip}" for tip in tips[:3]])
        else:
            response = "To check your location's risk level, please specify one of our monitored districts: **Downtown, Uptown, Suburbs, Westside, Eastside, Industrial District, Harbor Area, or Parkside**."

    # 4. Safety tips or advice query
    elif any(k in query_clean for k in ["safety", "tip", "advice", "recommendation", "protect", "prevent"]):
        if matched_crime:
            tips = SAFETY_TIPS[matched_crime]
            tips_list = "\n".join([f"- {tip}" for tip in tips])
            response = f"Here are safety recommendations to protect against **{matched_crime.capitalize()}**:\n\n{tips_list}"
        elif matched_location:
            # Get stats for this location and give advice
            loc_title = matched_location.title()
            cursor.execute("SELECT Crime_Type, COUNT(*) as c FROM crimes WHERE LOWER(Location) = ? GROUP BY Crime_Type ORDER BY c DESC LIMIT 1", (matched_location,))
            row = cursor.fetchone()
            top_crime = row[0] if row else "crimes"
            response = f"**Safety Advice for {loc_title}**:\n"
            response += f"This area experiences issues with **{top_crime}**. We recommend:\n"
            # Give tips for that crime
            tips = SAFETY_TIPS.get(top_crime.lower(), GENERAL_SAFETY)
            response += "\n".join([f"- {tip}" for tip in tips[:3]])
        else:
            tips_list = "\n".join([f"- {tip}" for tip in GENERAL_SAFETY])
            response = f"Here are general safety guidelines:\n\n{tips_list}\n\nTip: You can ask for safety advice on specific crimes like 'How do I protect against theft?'"
            
    # Safest area query
    elif any(k in query_clean for k in ["safest", "least crime", "minimum crime", "safest location"]):
        cursor.execute("SELECT Location, COUNT(*) as count FROM crimes GROUP BY Location ORDER BY count ASC LIMIT 1")
        row = cursor.fetchone()
        loc, count = row[0], row[1]
        cursor.execute("SELECT COUNT(*) FROM crimes WHERE Location = ? AND Arrest_Made = 1", (loc,))
        arrests = cursor.fetchone()[0]
        arrest_rate = round((arrests / count) * 100, 1) if count > 0 else 0
        response = f"Based on the dataset, the **safest area is {loc}** with only **{count} recorded crimes** and an arrest clearance rate of **{arrest_rate}%**."

    # Most dangerous or high risk area query
    elif any(k in query_clean for k in ["dangerous", "highest crime", "most crime", "hotspot", "high risk area"]):
        cursor.execute("SELECT Location, COUNT(*) as count FROM crimes GROUP BY Location ORDER BY count DESC LIMIT 1")
        row = cursor.fetchone()
        loc, count = row[0], row[1]
        cursor.execute("SELECT Crime_Type, COUNT(*) as c FROM crimes WHERE Location = ? GROUP BY Crime_Type ORDER BY c DESC LIMIT 1", (loc,))
        top_crime = cursor.fetchone()[0]
        response = f"The primary crime hotspot is **{loc}** with a total of **{count} crimes**. The most prevalent crime type in this area is **{top_crime}**."

    # Arrest statistics query
    elif any(k in query_clean for k in ["arrest", "solved", "clearance", "catch"]):
        cursor.execute("SELECT COUNT(*) FROM crimes WHERE Arrest_Made = 1")
        total_arrests = cursor.fetchone()[0]
        rate = round((total_arrests / total_crimes) * 100, 2)
        response = f"Out of **{total_crimes} total crimes**, arrests were successfully made in **{total_arrests} cases**. This represents a system-wide **Arrest Clearance Rate of {rate}%**."

    # Most common crime type query
    elif any(k in query_clean for k in ["common crime", "frequent crime", "prevalent crime", "highest crime type"]):
        cursor.execute("SELECT Crime_Type, COUNT(*) as count FROM crimes GROUP BY Crime_Type ORDER BY count DESC LIMIT 1")
        row = cursor.fetchone()
        crime_name, count = row[0], row[1]
        pct = round((count / total_crimes) * 100, 1)
        response = f"The most common crime category in the dataset is **{crime_name}**, accounting for **{count} incidents** ({pct}% of all recorded crimes)."

    # Location specific query
    elif matched_location:
        loc_title = matched_location.title()
        cursor.execute("SELECT COUNT(*) FROM crimes WHERE LOWER(Location) = ?", (matched_location,))
        loc_total = cursor.fetchone()[0]
        cursor.execute("SELECT Crime_Type, COUNT(*) as count FROM crimes WHERE LOWER(Location) = ? GROUP BY Crime_Type ORDER BY count DESC LIMIT 1", (matched_location,))
        top_crime_row = cursor.fetchone()
        top_crime = top_crime_row[0] if top_crime_row else "None"
        cursor.execute("SELECT COUNT(*) FROM crimes WHERE LOWER(Location) = ? AND Arrest_Made = 1", (matched_location,))
        loc_arrests = cursor.fetchone()[0]
        loc_arrest_rate = round((loc_arrests / loc_total) * 100, 2) if loc_total > 0 else 0
        
        response = f"**Crime Insights for {loc_title}**:\n"
        response += f"- Total Incidents: **{loc_total}**\n"
        response += f"- Prevalent Crime Type: **{top_crime}**\n"
        response += f"- Local Arrest Clearance Rate: **{loc_arrest_rate}%**\n"
        if loc_arrest_rate > 50:
            response += "The police response and arrest rates in this district are relatively high."
        else:
            response += "This location shows a low arrest rate, indicating high levels of unresolved cases."

    # Crime trend over time
    elif any(k in query_clean for k in ["trend", "increase", "decrease", "over time", "monthly", "yearly"]):
        cursor.execute("SELECT substr(Date, 1, 7) as month, COUNT(*) as count FROM crimes GROUP BY month ORDER BY month DESC LIMIT 3")
        rows = cursor.fetchall()
        if len(rows) >= 2:
            recent = rows[0]
            prev = rows[1]
            diff = recent[1] - prev[1]
            trend_dir = "increased" if diff > 0 else "decreased"
            response = f"Comparing the most recent months:\n"
            response += f"- {recent[0]}: **{recent[1]} crimes**\n"
            response += f"- {prev[0]}: **{prev[1]} crimes**\n"
            response += f"Crime volume has **{trend_dir} by {abs(diff)} incidents** from {prev[0]} to {recent[0]}."
        else:
            response = "Not enough monthly historical records are available in the database to compile a trend comparison."

    # Model prediction queries
    elif any(k in query_clean for k in ["model", "prediction", "random forest", "accuracy", "train", "machine learning"]):
        try:
            with open("models/metrics.json", "r") as f:
                metrics = json.load(f)
            response = "Our prediction system uses historical trends trained on three models:\n"
            response += f"- **Random Forest Classifier**: Severity Accuracy is ~{metrics.get('severity', {}).get('rf', {}).get('accuracy', 0)*100:.1f}%\n"
            response += f"- **Decision Tree**: Severity Accuracy is ~{metrics.get('severity', {}).get('dt', {}).get('accuracy', 0)*100:.1f}%\n"
            response += f"- **Logistic Regression**: Severity Accuracy is ~{metrics.get('severity', {}).get('lr', {}).get('accuracy', 0)*100:.1f}%\n"
            response += "You can use the **Prediction Dashboard** tab to run customized risk and severity scenarios!"
        except Exception:
            response = "Our system trains Random Forest, Decision Tree, and Logistic Regression algorithms on features like location, area type, month, day, and time. Ensure the models are fully trained by visiting the Dashboard and running the training script."

    # Fallback response
    else:
        cursor.execute("SELECT COUNT(DISTINCT Location) FROM crimes")
        unique_locs = cursor.fetchone()[0]
        cursor.execute("SELECT COUNT(DISTINCT Crime_Type) FROM crimes")
        unique_crimes = cursor.fetchone()[0]
        
        response = f"Hello! I am your AI Crime Analyst Assistant. Currently, I am monitoring **{total_crimes} total incidents** across **{unique_locs} locations** and **{unique_crimes} crime categories**.\n\n"
        response += "Here are some questions you can ask me:\n"
        response += "- *'What is the safest area?'*\n"
        response += "- *'Which district has the highest crime?'*\n"
        response += "- *'What are safety tips for robbery?'*\n"
        response += "- *'Show me the crime insights for Downtown'* (or any other location)\n"
        response += "- *'What is the overall arrest rate?'*\n"
        response += "- *'Explain the prediction model accuracy'*"

    conn.close()
    return response
