import streamlit as st
import pandas as pd
import pymysql
import plotly.express as px
import matplotlib.pyplot as plt

# --- Page Setup ---
st.set_page_config(page_title="SecureCheck Dashboard", layout="wide")
st.title("🚨 SecureCheck: Police Post Digital Ledger")

# --- Database Connection ---
def create_connection():
    try:
        return pymysql.connect(
            host="localhost",
            user="root",
            password="1994",
            database="Secure_check",
            cursorclass=pymysql.cursors.DictCursor
        )
    except Exception as e:
        st.error(f"Database connection failed: {e}")
        return None

# --- Data Fetching ---
def fetch_data(query, params=None):
    conn = create_connection()
    if conn:
        with conn.cursor() as cursor:
            cursor.execute(query, params or ())
            result = cursor.fetchall()
        conn.close()
        return pd.DataFrame(result)
    return pd.DataFrame()

# --- Tabs Layout ---
tab1, tab2, tab3 = st.tabs(["📋 Log a Stop", "📊 View Insights", "🧩 Advanced Queries"])

# --- Tab 1: Form ---
with tab1:
    st.subheader("📋 Traffic Stop Form")
    with st.form("stop_form"):
        col1, col2 = st.columns(2)
        with col1:
            stop_date = st.date_input("Stop Date")
            stop_time = st.time_input("Stop Time")
            country_name = st.text_input("Country", placeholder="e.g., Canada")
            driver_gender = st.selectbox("Gender", ["Male", "Female"])
            driver_age = st.number_input("Age", 16, 100, 30)
            driver_race = st.text_input("Race", placeholder="e.g., Asian")
        with col2:
            search_conducted = st.selectbox("Search Conducted?", ["No", "Yes"])
            search_type = st.text_input("Search Type", placeholder="e.g., Frisk")
            drugs_related = st.selectbox("Drug Related?", ["No", "Yes"])
            stop_duration = st.selectbox("Duration", ["0-15 Min", "16-30 Min", "30+ Min"])
            vehicle_number = st.text_input("Vehicle Number", placeholder="e.g., AB1234")
            #violation = st.text_input("Violation", placeholder="e.g., Speeding")
            #stop_outcome = st.selectbox("Outcome", ["Warning", "Ticket", "Arrest"])

        submitted = st.form_submit_button("Submit")

    if submitted:
        errors = []
        if not country_name.strip(): errors.append("Country is required.")
        if not driver_race.strip(): errors.append("Race is required.")
        if search_conducted == "Yes" and not search_type.strip(): errors.append("Search type is required.")
        if not vehicle_number.strip(): errors.append("Vehicle number is required.")
        #if not violation.strip(): errors.append("Violation is required.")

        if errors:
          for e in errors:
            st.error(f" {e}")
        else:
           st.success("✅ Stop logged successfully!")

    # --- Rule-based prediction logic using valid categories ---
    if driver_age < 25 and drugs_related == "Yes":
        predict_violation = "DUI"
        predict_outcome = "Arrest"
    elif search_conducted == "Yes" and stop_duration == "30+ Min":
        predict_violation = "DUI"
        predict_outcome = "Citation"
    elif stop_duration == "0-15 Min":
        predict_violation = "Speeding"
        predict_outcome = "Warning"
    elif driver_race.lower() in ["asian", "black"] and search_conducted == "Yes":
        predict_violation = "Seatbelt"
        predict_outcome = "Citation"
    elif stop_duration == "16-30 Min" and drugs_related == "No":
        predict_violation = "Signal"
        predict_outcome = "Warning"
    else:
        predict_violation = "Other"
        predict_outcome = "Warning"
        st.info("No matching rule found — using default prediction.")

    # --- Summary generation ---
    outcome_text = {
        "Warning": "received a warning",
        "Ticket": "received a citation",
        "Arrest": "was arrested",
        "Citation": "received a citation"
    }[predict_outcome]

    search_text = "No search was conducted" if search_conducted == "No" else "A search was conducted"
    drug_text = "was not drug-related" if drugs_related == "No" else "was drug-related"
    formatted_time = stop_time.strftime("%I:%M %p")

    summary = f"""
🚗 A {driver_age}-year-old {driver_gender.lower()} driver was predicted to be stopped for **{predict_violation}** at {formatted_time}.  
{search_text}, and they {outcome_text}.  
The stop lasted {stop_duration} and {drug_text}.  
Vehicle number: **{vehicle_number}**
"""

    st.markdown("### **Stop Summary**")
    st.markdown(summary)

# --- Tab 2: Insights ---
with tab2:
    st.subheader("📊 Recent Traffic Stops")
    data = fetch_data("SELECT * FROM traffic_stops LIMIT 20")
    if not data.empty:
        st.dataframe(data)
    else:
        st.info("No traffic stops found.")
 
    # Advanced Queries
with tab3: 
    
 st.header("🧩 Advanced Insights")

 selected_query = st.selectbox("Select a Query to Run", [
    "top 10 vehicle Number involved in drug-related stops",
    "Which vehicles were most frequently searched?",
    "gender distribution of drivers stopped in each country",
    "race and gender combination has the highest search rate",
    "driver age group had the highest arrest rate",
    "time of day sees the most traffic stops",
    "average stop duration for different violations",
    "Are stops during the night more likely to lead to arrests?",
    "Which violations are most associated with searches or arrests?",
    "violations are most common among younger drivers (<25)",
    "Is there a violation that rarely results in search or arrest?",
    "countries report the highest rate of drug-related stops",
    "arrest rate by country and violation",
    "country has the most stops with search conducted",
    "Yearly Breakdown of Stops and Arrests by Country",
    "Driver Violation Trends Based on Age and Race",
    "Number of Stops by Year,Month, Hour of the Day",
    "Violations with High Search and Arrest Rates",
    "Driver Demographics by Country(Age, Gender, and Race)",
    "Top 5 Violations with Highest Arrest Rates"
 ])

 query_map = {
    "top 10 vehicle Number involved in drug-related stops": "SELECT vehicle_number, COUNT(*) AS stop_count FROM traffic_stops WHERE drugs_related_stop = 1 GROUP BY vehicle_number ORDER BY stop_count DESC limit 10",
    "Which vehicles were most frequently searched?": "select vehicle_number,count(*) as search_count from traffic_stops where search_conducted=1 group by vehicle_number order by search_count DESC ;",
    "gender distribution of drivers stopped in each country": "select country_name ,driver_gender,count(*) as stop_count from traffic_stops where driver_gender is not null group by country_name,driver_gender order by country_name,stop_count desc;",
    "driver age group had the highest arrest rate":""" SELECT 
      (driver_age / 10) * 10 AS age_group,
      (SUM(is_arrested) * 100.0 / COUNT(*)) AS arrest_rate
      FROM traffic_stops
      GROUP BY (driver_age / 10) * 10
      ORDER BY arrest_rate DESC
      LIMIT 1;""",
    "race and gender combination has the highest search rate": "select driver_race , driver_gender ,count(*) as race_gender from traffic_stops where search_conducted=true group by driver_race,driver_gender order by race_gender desc;",
    "time of day sees the most traffic stops":""" SELECT HOUR(timestamp) AS hour_of_day, COUNT(*) AS stop_count
        FROM traffic_stops
        GROUP BY hour_of_day
        ORDER BY stop_count DESC;""",
    "average stop duration for different violations": "select violation,round(avg(stop_duration),2) as average_stop_duration from traffic_stops group by violation order by average_stop_duration desc;",
    "Are stops during the night more likely to lead to arrests?": "SELECT CASE WHEN HOUR(stop_time) BETWEEN 6 AND 20 THEN 'Day' ELSE 'Night'  END AS time_of_day,  COUNT(*) AS total_stops,  SUM(is_arrested = 'Yes') AS total_arrests,  ROUND(SUM(is_arrested = 'Yes') * 100.0 / COUNT(*), 2) AS arrest_rate_percent FROM  traffic_stops GROUP BY  time_of_day",

    "Which violations are most associated with searches or arrests?": """
    SELECT 
      violation,
      COUNT(*) AS total_stops,
      ROUND(SUM(search_conducted = 1) * 100.0 / COUNT(*), 2) AS search_rate_percent,
      ROUND(SUM(is_arrested = 1) * 100.0 / COUNT(*), 2) AS arrest_rate_percent
 FROM
   traffic_stops
 GROUP BY 
   violation
 ORDER BY
   arrest_rate_percent DESC;
  """,

    "violations are most common among younger drivers (<25)": """select violation, count(*) as no_of_drivers 
 from traffic_stops 
 where driver_age < 25 
 group by violation 
 order by no_of_drivers desc;""",

 "Is there a violation that rarely results in search or arrest?":"""SELECT   violation,  COUNT(*) AS total_stops,
   ROUND(AVG(CASE WHEN search_conducted = 1 OR is_arrested = 1 THEN 1.0 ELSE 0 END) * 100, 2) AS action_rate_percent
   FROM 
    traffic_stops
   GROUP BY 
     violation
    ORDER BY 
      total_stops ASC;""",


      "countries report the highest rate of drug-related stops":"""select country_name,count(*) as total_stops ,
    round(avg(case when drugs_related_stop = 1 then 1 else 0 end)*100,2) as drugs_stop
    from traffic_stops  
    group by country_name
    order by drugs_stop desc;""",

    "arrest rate by country and violation":"""select country_name,violation,  round(avg(case when is_arrested = 1 then 1 else 0 end)*100,2) as arrest_rate
      from traffic_stops
      group by country_name,violation
      order by 
        country_name ASC,
        arrest_rate DESC;""",

    "country has the most stops with search conducted":""" SELECT country_name , count(*) as most_stops 
       from traffic_stops
       where search_conducted=1
       group by country_name
       order by most_stops desc
       limit 1;""",


    "Yearly Breakdown of Stops and Arrests by Country":""" select country_name,year,total_stops,total_arrest,
    round(total_arrest*100/total_stops,2) as arrest_rate,
    sum(total_arrest)over(partition by country_name) as country_arrest,
    sum(total_stops)over(partition by country_name) as country_stops,
    'country total' AS row_type
 from (  
    select country_name,
    extract(year from timestamp) as year,
    count(*) as total_stops,
    count(case when  is_arrested=1 then 1 end) as total_arrest
 from traffic_stops
    group by country_name,year
  ) as yearly
  order by country_name,year;""",


  "Driver Violation Trends Based on Age and Race":""" SELECT 
  t.driver_age,        -- from traffic_stops
  t.driver_race,
  t.violation,       -- from traffic_stops
  v.total_violations   -- from subquery
 FROM traffic_stops t   -- alias 't' for traffic_stops
 JOIN (
  SELECT driver_age, driver_race, COUNT(*) AS total_violations
  FROM traffic_stops
  GROUP BY driver_age, driver_race
 ) v                   -- alias 'v' for subquery
 ON t.driver_age = v.driver_age AND t.driver_race = v.driver_race;""",



 "Number of Stops by Year,Month, Hour of the Day":"""SELECT d.stop_year,
  d.stop_month,
  d.stop_hour,
  d.total_stops
 FROM (
  SELECT 
    YEAR(timestamp) AS stop_year,
    MONTH(timestamp) AS stop_month,
    HOUR(timestamp) AS stop_hour,
    COUNT(*) AS total_stops
  FROM traffic_stops
  GROUP BY stop_year, stop_month, stop_hour
 ) d
 ORDER BY d.stop_year, d.stop_month, d.stop_hour;""",


 "Violations with High Search and Arrest Rates":"""SELECT violation,total_arrest,
  total_stops,
  total_search_conducted,
  ROUND(total_arrest * 100.0 / total_stops, 2) AS arrest_rate,
  ROUND(total_search_conducted * 100.0 / total_stops, 2) AS search_rate,
  RANK() OVER (ORDER BY total_arrest * 1.0 / total_stops DESC) AS arrest_rank,
  RANK() OVER (ORDER BY total_search_conducted * 1.0 / total_stops DESC) AS search_rank
 FROM (
  SELECT 
    violation,
    COUNT(*) AS total_stops,
    COUNT(CASE WHEN search_conducted = 1 THEN 1 END) AS total_search_conducted,
    COUNT(CASE WHEN is_arrested = 1 THEN 1 END) AS total_arrest
  FROM traffic_stops
  GROUP BY violation
 ) AS v
 WHERE 
  (total_arrest * 100.0 / total_stops) > 10
  and (total_search_conducted * 100.0 / total_stops) > 10
 ORDER BY violation;""",



 "Driver Demographics by Country(Age, Gender, and Race)":"""SELECT 
  country_name,
  driver_age,
  driver_gender,
  driver_race,
  COUNT(*) AS total_drivers
 FROM traffic_stops
 WHERE country_name IS NOT NULL
 GROUP BY country_name, driver_age, driver_gender, driver_race
 ORDER BY country_name,driver_age, total_drivers DESC;  """,


 "Top 5 Violations with Highest Arrest Rates":"""SELECT violation, 
       COUNT(*) AS total, 
       SUM(CASE WHEN is_arrested = 'TRUE' THEN 1 ELSE 0 END) AS arrests,
       round(SUM(CASE WHEN is_arrested = 'TRUE' THEN 1 ELSE 0 END) * 100.0 / COUNT(*),2) AS arrest_rate
FROM traffic_stops
 GROUP BY violation
 ORDER BY arrest_rate DESC
 LIMIT 5;"""

    
 }

 if st.button("Run Query"):
    result = fetch_data(query_map[selected_query].strip())

    if not result.empty:
        # --- Custom Visualizations ---
        st.markdown("###  Visualization")

        if selected_query == "top 10 vehicle Number involved in drug-related stops":
            fig = px.bar(result, x="vehicle_number", y="stop_count", title="Top 10 Vehicles in Drug-Related Stops")
            st.plotly_chart(fig, use_container_width=True)

        elif selected_query == "Which vehicles were most frequently searched?":
            fig = px.bar(result, x="vehicle_number", y="search_count", title="Most Frequently Searched Vehicles")
            st.plotly_chart(fig, use_container_width=True)

        elif selected_query == "gender distribution of drivers stopped in each country":
            fig = px.bar(result, x="country_name", y="stop_count", color="driver_gender", barmode="group",
                         title="Gender Distribution by Country")
            st.plotly_chart(fig, use_container_width=True)

        elif selected_query == "race and gender combination has the highest search rate":
            fig = px.bar(result, x="driver_race", y="race_gender", color="driver_gender", barmode="group",
                         title="Search Rate by Race and Gender")
            st.plotly_chart(fig, use_container_width=True)

        elif selected_query == "average stop duration for different violations":
            fig = px.bar(result, x="violation", y="average_stop_duration", title="Average Stop Duration by Violation")
            st.plotly_chart(fig, use_container_width=True)

        elif selected_query == "countries report the highest rate of drug-related stops":
            fig = px.bar(result, x="country_name", y="drugs_stop", title="Drug-Related Stop Rate by Country")
            st.plotly_chart(fig, use_container_width=True)

        elif selected_query == "arrest rate by country and violation":
            fig = px.bar(result, x="violation", y="arrest_rate", color="country_name", barmode="group",
                         title="Arrest Rate by Country and Violation")
            st.plotly_chart(fig, use_container_width=True)

        elif selected_query == "time of day sees the most traffic stops":
            fig = px.bar(result, x="hour_of_day", y="stop_count", title="Traffic Stops by Hour of Day")
            st.plotly_chart(fig, use_container_width=True)

        elif selected_query == "driver age group had the highest arrest rate":
            fig = px.bar(result,x="age_group",y="arrest_rate",title="🚔 Arrest Rate by Driver Age Group",
              labels={"age_group": "Age Group", "arrest_rate": "Arrest Rate (%)"},
              color="arrest_rate",
               color_continuous_scale="Reds"
            )
            st.plotly_chart(fig, use_container_width=True)


        elif selected_query == "Yearly Breakdown of Stops and Arrests by Country":
            fig = px.line(result, x="year", y="arrest_rate", color="country_name", markers=True,
                          title="Yearly Arrest Rate by Country")
            st.plotly_chart(fig, use_container_width=True)

        elif selected_query == "Number of Stops by Year,Month, Hour of the Day":
            fig = px.line(
    result,
    x="stop_hour",
    y="total_stops",
    color="stop_month",
    facet_col="stop_year",
    title="Hourly Stop Trends by Month (Faceted by Year)"
)

            st.plotly_chart(fig, use_container_width=True)

        elif selected_query == "Violations with High Search and Arrest Rates":
            fig = px.scatter(result, x="search_rate", y="arrest_rate", size="total_stops", color="violation",
                             title="Search vs Arrest Rate by Violation", hover_name="violation")
            st.plotly_chart(fig, use_container_width=True)

        elif selected_query == "Top 5 Violations with Highest Arrest Rates":
            fig = px.bar(result, x="violation", y="arrest_rate", title="Top 5 Violations by Arrest Rate")
            st.plotly_chart(fig, use_container_width=True)

        else:
            st.info("No chart available for this query.")

        # --- Special logic for night/day arrest query ---
        if selected_query == "Are stops during the night more likely to lead to arrests?":
            if 'time_of_day' in result.columns:
                day_row = result[result['time_of_day'] == 'Day']
                night_row = result[result['time_of_day'] == 'Night']

                if not day_row.empty and not night_row.empty:
                    day_rate = day_row['arrest_rate_percent'].values[0]
                    night_rate = night_row['arrest_rate_percent'].values[0]

                    if night_rate > day_rate:
                        st.success("✅ Yes — night stops are more likely to lead to arrests.")
                    else:
                        st.info("🚫 No — night stops are less likely to lead to arrests than day stops.")

                    st.write(f"🌞 Day arrest rate: {day_rate:.2f}%")
                    st.write(f"🌙 Night arrest rate: {night_rate:.2f}%")
                else:
                    st.warning("Missing data for either 'Day' or 'Night'.")
            else:
                st.warning("Expected column 'time_of_day' not found in result.")
        else:
            st.dataframe(result)
    else:
        st.warning("No results found for the selected query.")