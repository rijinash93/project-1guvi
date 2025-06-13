import streamlit as st
import pandas as pd
import datetime
from sqlalchemy import create_engine, text

# Streamlit App Config
st.set_page_config(page_title="Police Log Prediction", page_icon="🚔")
# Set custom background color (light blue as example)
st.markdown("""
    <style>
        .stApp {
            background-color: #e6f2ff;
        }
    </style>
    """, unsafe_allow_html=True)

# DB Connection
db_url = "postgresql+pg8000://rijina3030:sOg4cFE5Nguj0kiXk0h86gQjVNPcbJy4@dpg-d0krorbe5dus73c1qhsg-a.singapore-postgres.render.com/project1"
engine = create_engine(db_url)

# Load data
@st.cache_data
def load_data():
    query = "SELECT * FROM traffic_stops"
    return pd.read_sql(query, engine)

df = load_data()

# Title with styled heading
st.markdown("<h2 style='color: navy;'>🚔 Add New Police Log & Predict Outcome and Violation</h2>", unsafe_allow_html=True)

   


# Form
with st.form("my_form"):
   
    stop_date = st.date_input("Stop Date", value=datetime.date(2020, 1, 1))

# Display it in DD-MM-YYYY format
    formatted_date = stop_date.strftime("%d/%m/%Y")
    st.write("Selected Stop Date:", formatted_date)
    
    driver_gender = st.selectbox("Driver Gender", df['driver_gender'].dropna().unique())
    driver_age = st.text_input("Driver Age")
    driver_race = st.text_input("Driver Race")
    
  






# Create time options as strings (e.g., "00:00:00" to "25:00:00")
    time_options = [
    f"{h}:{m:02}:00"
    for h in range(0, 26)
    for m in range(0, 60, 1)
    if not (h == 25 and m > 0)  # Only include 25:00:00, not 25:02:00, etc.
     ]

# Dropdown that behaves like a text box (searchable)
    stop_time = st.selectbox("⏱️ Select Stop Time ", time_options)

# Output selected time
    


# Display the formatted time
    



# Define readable time ranges
    duration_options = [
      "0-15 Min",
      "16-30 Min",
      "31-45 Min",
      "46-60 Min",
      "More than 1 Hour"
      ]

# Dropdown menu
 

# Display selection
    stop_duration = st.selectbox("Stop Duration", duration_options)

   

    search_conducted = st.text_input("Was Search Conducted")
    search_type = st.text_input("Search Type")
    drugs_related_stop = st.text_input("Was it Drug Related")
    
    country_name = st.text_input("Country Name")
    
    vehicle_number = st.text_input("Vehicle Number")

    submit_button = st.form_submit_button("Predict Stop Outcome and Violation")
from sqlalchemy import text

if submit_button:
    # Validate required fields
    required_fields = [vehicle_number]
    if any(field.strip() == "" for field in required_fields):
        st.error("🚫 Please fill in all required fields before submitting.")
    else:
        # Prepare the values dictionary
        values = {
            'driver_race': driver_race,
            'search_conducted': search_conducted,
            'search_type': search_type,
            'drugs_related_stop': drugs_related_stop,
            'driver_gender': driver_gender,
            'driver_age': driver_age,
            'country_name': country_name,
            'vehicle_number': vehicle_number,
            'stop_date': formatted_date,
            'stop_time': stop_time,
            'stop_duration': stop_duration
        }

        # 🟢 Define both queries up front
        select_query = text("""
            SELECT stop_outcome, violation
            FROM traffic_stops
            WHERE 
              country_name = :country_name 
              AND stop_duration = :stop_duration
              AND stop_time = :stop_time
              AND stop_date = :stop_date
              AND driver_gender = :driver_gender 
              AND driver_age = :driver_age 
              AND vehicle_number = :vehicle_number
              AND driver_race = :driver_race 
              AND search_conducted = :search_conducted 
              AND search_type = :search_type 
              AND drugs_related_stop = :drugs_related_stop
        """)

        insert_query = text("""
            INSERT INTO traffic_stops (
                country_name, stop_duration, stop_time, stop_date,
                driver_gender, driver_age, vehicle_number,
                driver_race, search_conducted, search_type, drugs_related_stop
            ) VALUES (
                :country_name, :stop_duration, :stop_time, :stop_date,
                :driver_gender, :driver_age, :vehicle_number,
                :driver_race, :search_conducted, :search_type, :drugs_related_stop
            )
        """)

        # 🔄 Run logic inside transaction block
        try:
            with engine.begin() as connection:
                result = connection.execute(select_query, values).fetchone()

                if result is None:
                    connection.execute(insert_query, values)
                    st.success("✅ New police log inserted into the database.")
                else:
                    stop_outcome, violation = result
                    st.success(f"✅ Predicted Stop Outcome: {stop_outcome}")
                    st.info(f"📋 Violation: {violation}")
        except Exception as e:
            st.error(f"❌ Error while accessing the database:\n{e}")

import streamlit as st
import pandas as pd
from sqlalchemy import create_engine

# DB connection
engine = create_engine("postgresql+pg8000://rijina3030:sOg4cFE5Nguj0kiXk0h86gQjVNPcbJy4@dpg-d0krorbe5dus73c1qhsg-a.singapore-postgres.render.com/project1")

# Dictionary of queries
medium_level_queries = {
    "🚗 Vehicle-Based: Top 10 vehicles in drug-related stops": """
        SELECT vehicle_number, COUNT(*) AS count
        FROM traffic_stops
        WHERE drugs_related_stop = 'true'
        GROUP BY vehicle_number
        ORDER BY count DESC
        LIMIT 10;
    """,

    "🚗 Vehicle-Based: Most frequently searched vehicles": """
        SELECT vehicle_number, COUNT(*) AS search_count
        FROM traffic_stops
        WHERE search_conducted = 'true'
        GROUP BY vehicle_number
        ORDER BY search_count DESC
        LIMIT 10;
    """,

    "🧍 Demographic-Based: Age group with highest arrest rate": """
        SELECT 
            CASE 
                WHEN CAST(driver_age AS INTEGER) < 18 THEN 'Under 18'
                WHEN CAST(driver_age AS INTEGER) BETWEEN 18 AND 25 THEN '18-25'
                WHEN CAST(driver_age AS INTEGER) BETWEEN 26 AND 40 THEN '26-40'
                WHEN CAST(driver_age AS INTEGER) BETWEEN 41 AND 60 THEN '41-60'
                ELSE '60+' 
            END AS age_group,
            COUNT(*) FILTER (WHERE stop_outcome = 'Arrest') * 100.0 / COUNT(*) AS arrest_rate
        FROM traffic_stops
        WHERE driver_age ~ '^\d+$'
        GROUP BY age_group
        ORDER BY arrest_rate DESC;
    """,

    "🧍 Demographic-Based: Gender distribution by country": """
        SELECT country_name, driver_gender, COUNT(*) AS count
        FROM traffic_stops
        GROUP BY country_name, driver_gender
        ORDER BY country_name;
    """,

    "🧍 Demographic-Based: Highest search rate by race & gender": """
        SELECT driver_race, driver_gender,
               COUNT(*) FILTER (WHERE search_conducted = 'true') * 100.0 / COUNT(*) AS search_rate
        FROM traffic_stops
        GROUP BY driver_race, driver_gender
        ORDER BY search_rate DESC;
    """,

    "🕒 Time-Based: Time of day with most traffic stops": """
        SELECT 
            CASE 
                WHEN stop_time BETWEEN '00:00:00' AND '06:00:00' THEN 'Night (12AM-6AM)'
                WHEN stop_time BETWEEN '06:00:01' AND '12:00:00' THEN 'Morning (6AM-12PM)'
                WHEN stop_time BETWEEN '12:00:01' AND '18:00:00' THEN 'Afternoon (12PM-6PM)'
                ELSE 'Evening (6PM-12AM)'
            END AS time_period,
            COUNT(*) AS total_stops
        FROM traffic_stops
        GROUP BY time_period
        ORDER BY total_stops DESC;
    """,

    "🕒 Time-Based: Avg stop duration by violation": """
        SELECT violation, AVG(CAST(SPLIT_PART(stop_duration, '-', 1) AS INTEGER)) AS avg_duration_min
        FROM traffic_stops
        GROUP BY violation
        ORDER BY avg_duration_min DESC;
    """,

    "🕒 Time-Based: Are night stops more likely to lead to arrests?": """
        SELECT 
            CASE 
                WHEN stop_time BETWEEN '00:00:00' AND '06:00:00' THEN 'Night'
                ELSE 'Day'
            END AS time_of_day,
            COUNT(*) FILTER (WHERE stop_outcome = 'Arrest') * 100.0 / COUNT(*) AS arrest_rate
        FROM traffic_stops
        GROUP BY time_of_day;
    """,

    "⚖️ Violation-Based: Violations linked to searches/arrests": """
        SELECT violation,
               COUNT(*) FILTER (WHERE search_conducted = 'true') AS search_count,
               COUNT(*) FILTER (WHERE stop_outcome = 'Arrest') AS arrest_count
        FROM traffic_stops
        GROUP BY violation
        ORDER BY arrest_count DESC;
    """,

    "⚖️ Violation-Based: Common violations in drivers <25": """
        SELECT violation, COUNT(*) AS count
        FROM traffic_stops
        WHERE CAST(driver_age AS INTEGER) < 25
        GROUP BY violation
        ORDER BY count DESC;
    """,

    "⚖️ Violation-Based: Violations rarely searched or arrested": """
        SELECT violation,
               COUNT(*) FILTER (WHERE search_conducted = 'true') AS search_count,
               COUNT(*) FILTER (WHERE stop_outcome = 'Arrest') AS arrest_count
        FROM traffic_stops
        GROUP BY violation
        HAVING COUNT(*) FILTER (WHERE search_conducted = 'true') = 0 
            AND COUNT(*) FILTER (WHERE stop_outcome = 'Arrest') = 0;
    """,

    "🌍 Location-Based: Countries with most drug stops": """
        SELECT country_name, COUNT(*) AS drug_stops
        FROM traffic_stops
        WHERE drugs_related_stop = 'true'
        GROUP BY country_name
        ORDER BY drug_stops DESC;
    """,

    "🌍 Location-Based: Arrest rate by country and violation": """
        SELECT country_name, violation,
               COUNT(*) FILTER (WHERE stop_outcome = 'Arrest') * 100.0 / COUNT(*) AS arrest_rate
        FROM traffic_stops
        GROUP BY country_name, violation
        ORDER BY arrest_rate DESC;
    """,

    "🌍 Location-Based: Country with most searches": """
        SELECT country_name, COUNT(*) AS search_count
        FROM traffic_stops
        WHERE search_conducted = 'true'
        GROUP BY country_name
        ORDER BY search_count DESC;
    """
}


# UI: Medium-level dropdown
st.subheader("📊 Medium-Level Queries")

query_choice = st.selectbox(
    "Select a query to run:",
    ["Select..."] + list(medium_level_queries.keys())
)

# Execute the query
if query_choice != "Select...":
    if st.button("Run Query"):
        query = medium_level_queries[query_choice]
        try:
            df_result = pd.read_sql(query, engine)
            st.dataframe(df_result)
        except Exception as e:
            st.error(f"❌ Error executing query:\n{e}")


# --- Dropdown for Query Selection ---
query_options = {
    "Yearly Breakdown of Stops and Arrests by Country": """
        SELECT 
    country_name,
    EXTRACT(HOUR FROM stop_time::time) AS hour,
    COUNT(*) AS total_stops,
    SUM(CASE WHEN stop_outcome = 'Arrest' THEN 1 ELSE 0 END) AS total_arrests,
    ROUND(100.0 * SUM(CASE WHEN stop_outcome = 'Arrest' THEN 1 ELSE 0 END) / COUNT(*), 2) AS arrest_rate,
    RANK() OVER (
        PARTITION BY EXTRACT(HOUR FROM stop_time::time)
        ORDER BY SUM(CASE WHEN stop_outcome = 'Arrest' THEN 1 ELSE 0 END) DESC
    ) AS arrest_rank
FROM traffic_stops
GROUP BY country_name, EXTRACT(HOUR FROM stop_time::time)
ORDER BY hour, arrest_rank;

    """,

    "Driver Violation Trends Based on Age and Race": """
         SELECT 
     driver_age,
    driver_race,
    violation,
    COUNT(*) AS total_violations
FROM traffic_stops
WHERE violation IS NOT NULL
GROUP BY driver_age, driver_race, violation
ORDER BY driver_age, driver_race, total_violations DESC;

    """,

    "Time Period Analysis of Stops (Year, Month, Hour)": """
        SELECT 
    EXTRACT(HOUR FROM stop_time::time) AS hour,
    COUNT(*) AS total_stops
FROM traffic_stops
GROUP BY hour
ORDER BY hour;

    """,

    "Violations with High Search and Arrest Rates": """
        SELECT 
            violation,
            COUNT(*) AS total_stops,
            SUM(CASE WHEN search_conducted = TRUE THEN 1 ELSE 0 END) AS searches,
            SUM(CASE WHEN stop_outcome = 'Arrest' THEN 1 ELSE 0 END) AS arrests,
            ROUND(100.0 * SUM(CASE WHEN search_conducted = TRUE THEN 1 ELSE 0 END) / COUNT(*), 2) AS search_rate,
            ROUND(100.0 * SUM(CASE WHEN stop_outcome = 'Arrest' THEN 1 ELSE 0 END) / COUNT(*), 2) AS arrest_rate,
            RANK() OVER (ORDER BY ROUND(100.0 * SUM(CASE WHEN stop_outcome = 'Arrest' THEN 1 ELSE 0 END) / COUNT(*), 2) DESC) AS arrest_rank
        FROM traffic_stops
        GROUP BY violation
        HAVING COUNT(*) > 100
        ORDER BY arrest_rank;
    """,

    "Driver Demographics by Country (Age, Gender, Race)": """
        SELECT 
            country_name,
            driver_gender,
            driver_race,
            driver_age,
            COUNT(*) AS total_drivers
        FROM traffic_stops
        GROUP BY country_name, driver_gender, driver_race, driver_age
        ORDER BY country_name, total_drivers DESC;
    """,

    "Top 5 Violations with Highest Arrest Rates": """
        SELECT 
            violation,
            COUNT(*) AS total_stops,
            SUM(CASE WHEN stop_outcome = 'Arrest' THEN 1 ELSE 0 END) AS arrests,
            ROUND(100.0 * SUM(CASE WHEN stop_outcome = 'Arrest' THEN 1 ELSE 0 END) / COUNT(*), 2) AS arrest_rate
        FROM traffic_stops
        GROUP BY violation
        HAVING COUNT(*) > 50
        ORDER BY arrest_rate DESC
        LIMIT 5;
    """
}

# --- User Selection ---
st.subheader("📊 complex-Level Queries")

query_choice = st.selectbox(
    "Select a query to run:",
    ["Select..."] + list(query_options.keys())
)

# Execute the query
if query_choice != "Select...":
    if st.button("Run Query",key=query_options[query_choice]):
        query = query_options[query_choice]
        try:
            df_result = pd.read_sql(query, engine)
            st.dataframe(df_result)
        except Exception as e:
            st.error(f"❌ Error executing query:\n{e}")


# Streamlit UI
import streamlit as st
import pandas as pd
from sqlalchemy import create_engine, text

# Streamlit page config


# Title with style
st.markdown("<h2 style='color: navy;'>🚦 Traffic Stop Records by Country</h2>", unsafe_allow_html=True)


# Fetch unique countries for dropdown
with engine.connect() as conn:
    result = conn.execute(text("SELECT DISTINCT country_name FROM traffic_stops"))
    countries = [row[0] for row in result]

# Add selection box
selected_country = st.selectbox("🌍 Choose a country", options=["--Select--"] + countries)

# Submit button
if st.button("🎯 Submit"):
    if selected_country == "--Select--":
        st.warning("⚠️ Please choose a valid country.")
    else:
        with engine.connect() as conn:
            query = text("SELECT * FROM traffic_stops WHERE country_name = :country")
            df = pd.read_sql(query, conn, params={"country": selected_country})

        if df.empty:
            st.info(f"ℹ️ No records found for **{selected_country}**.")
        else:
            st.success(f"✅ {len(df)} records found for **{selected_country}**.")
            # Style dataframe
            styled_df = df.style.set_properties(**{
                'background-color': 'lavender',
                'color': 'black',
                'border-color': 'white'
            }).highlight_null('red')
            st.dataframe(styled_df, use_container_width=True)
