import streamlit as st
import pandas as pd
import plotly.express as px
from db import fetch_data, insert_stop, check_flagged_vehicle

# --- Page Setup ---
st.set_page_config(page_title="SecureCheck Dashboard", layout="wide")
st.title("🚨 SecureCheck: Police Post Digital Ledger")

# --- Role-Based Login (Sidebar) ---
# This controls who can see what on the dashboard
st.sidebar.title("🔐 Officer Login")
role = st.sidebar.selectbox("Login as", ["Officer", "Admin"])
password = st.sidebar.text_input("Password", type="password")

# Show login status in sidebar
if role == "Admin":
    if password == "":
        st.sidebar.info("ℹ️ Enter Admin password to unlock all tabs")
    elif password == "admin123":
        st.sidebar.success("✅ Logged in as Admin — Full Access")
    else:
        st.sidebar.error("❌ Wrong password")
elif role == "Officer":
    st.sidebar.success("✅ Logged in as Officer — Tab 1 & 2 only")

# --- Access flags ---
# officer_access: True for any Officer (no password needed)
# admin_access: True only for Admin with correct password
officer_access = (role == "Officer")
admin_full_access = (role == "Admin" and password == "admin123")

# --- Tabs Layout ---
tab1, tab2, tab3 = st.tabs(["📋 Log a Stop", "📊 View Insights", "🧩 Advanced Queries"])

# --- Tab 1: Form --- (Officers and Admins can access)
with tab1:
    if not officer_access and not admin_full_access:
        st.warning("🔒 Please login using the sidebar to access this tab.")
        st.stop()
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

           # --- Step 1: Save the stop to MySQL ---
           saved = insert_stop(
               stop_date, stop_time, country_name, driver_gender, driver_age,
               driver_race, search_conducted, search_type, drugs_related,
               stop_duration, vehicle_number, predict_violation, predict_outcome
           )

           # --- Step 2: Check if the vehicle is flagged ---
           flagged = check_flagged_vehicle(vehicle_number.strip().upper())
           if flagged:
               st.error(f"🚨 ALERT! Vehicle **{vehicle_number.upper()}** is FLAGGED!")
               st.warning(f"⚠️ Reason: {flagged.get('reason', 'Suspect vehicle')} | Flagged on: {flagged.get('flagged_date', 'N/A')}")
           else:
               if saved:
                   st.success("✅ Stop logged and saved to database successfully!")
               else:
                   st.warning("⚠️ Stop summary generated but could not be saved to database.")

# --- Tab 2: Insights --- (Officers and Admins can access)
with tab2:
    if not officer_access and not admin_full_access:
        st.warning("🔒 Please login using the sidebar to access this tab.")
        st.stop()
    # --- KPI Metrics ---
    total = fetch_data("SELECT COUNT(*) AS total FROM traffic_stops")
    arrests = fetch_data("SELECT COUNT(*) AS arrests FROM traffic_stops WHERE is_arrested = 1")
    searches = fetch_data("SELECT COUNT(*) AS searches FROM traffic_stops WHERE search_conducted = 1")
    drug_stops = fetch_data("SELECT COUNT(*) AS drug_stops FROM traffic_stops WHERE drugs_related_stop = 1")
    # Violation Detection Rate = flagged vehicles caught / total stops × 100
    flagged_caught = fetch_data("SELECT COUNT(*) AS flagged FROM traffic_stops WHERE vehicle_number IN (SELECT vehicle_number FROM flagged_vehicles)")

    col1, col2, col3, col4, col5 = st.columns(5)
    if not total.empty:
        col1.metric("Total Stops", f"{total['total'].iloc[0]:,}")
    if not arrests.empty:
        col2.metric("Total Arrests", f"{arrests['arrests'].iloc[0]:,}")
    if not searches.empty:
        col3.metric("Searches Conducted", f"{searches['searches'].iloc[0]:,}")
    if not drug_stops.empty:
        col4.metric("Drug-Related Stops", f"{drug_stops['drug_stops'].iloc[0]:,}")
    if not flagged_caught.empty and not total.empty and total['total'].iloc[0] > 0:
        rate = round(flagged_caught['flagged'].iloc[0] * 100 / total['total'].iloc[0], 2)
        col5.metric("🚨 Violation Detection Rate", f"{rate}%")

    st.markdown("---")

    # --- Charts Row 1 ---
    col_a, col_b = st.columns(2)

    with col_a:
        st.subheader("Stops by Violation")
        viol_data = fetch_data("SELECT violation, COUNT(*) AS count FROM traffic_stops GROUP BY violation ORDER BY count DESC")
        if not viol_data.empty:
            fig = px.bar(viol_data, x="violation", y="count", title="Stops by Violation Type")
            st.plotly_chart(fig, use_container_width=True)

    with col_b:
        st.subheader("Stop Outcome Distribution")
        outcome_data = fetch_data("SELECT stop_outcome, COUNT(*) AS count FROM traffic_stops GROUP BY stop_outcome ORDER BY count DESC")
        if not outcome_data.empty:
            fig = px.pie(outcome_data, names="stop_outcome", values="count", title="Stop Outcomes")
            st.plotly_chart(fig, use_container_width=True)

    # --- Charts Row 2 ---
    col_c, col_d = st.columns(2)

    with col_c:
        st.subheader("Stops by Gender")
        gender_data = fetch_data("SELECT driver_gender, COUNT(*) AS count FROM traffic_stops GROUP BY driver_gender")
        if not gender_data.empty:
            fig = px.pie(gender_data, names="driver_gender", values="count", title="Gender Distribution")
            st.plotly_chart(fig, use_container_width=True)

    with col_d:
        st.subheader("Stops by Race")
        race_data = fetch_data("SELECT driver_race, COUNT(*) AS count FROM traffic_stops GROUP BY driver_race ORDER BY count DESC")
        if not race_data.empty:
            fig = px.bar(race_data, x="driver_race", y="count", title="Stops by Driver Race")
            st.plotly_chart(fig, use_container_width=True)

    # --- Charts Row 3 ---
    col_e, col_f = st.columns(2)

    with col_e:
        st.subheader("Stops by Hour of Day")
        hour_data = fetch_data("SELECT HOUR(stop_time) AS hour, COUNT(*) AS count FROM traffic_stops GROUP BY hour ORDER BY hour")
        if not hour_data.empty:
            fig = px.line(hour_data, x="hour", y="count", title="Traffic Stops by Hour", markers=True)
            st.plotly_chart(fig, use_container_width=True)

    with col_f:
        st.subheader("Stops by Country")
        country_data = fetch_data("SELECT country_name, COUNT(*) AS count FROM traffic_stops GROUP BY country_name ORDER BY count DESC LIMIT 10")
        if not country_data.empty:
            fig = px.bar(country_data, x="country_name", y="count", title="Top 10 Countries by Stop Count")
            st.plotly_chart(fig, use_container_width=True)

    st.markdown("---")

    # --- Recent Records ---
    st.subheader("📋 Recent Traffic Stops")
    data = fetch_data("SELECT * FROM traffic_stops ORDER BY timestamp DESC LIMIT 50")
    if not data.empty:
        st.dataframe(data, use_container_width=True)
    else:
        st.info("No traffic stops found.")
 
    # Advanced Queries
with tab3:
    # Tab 3 is ADMIN ONLY
    if not admin_full_access:
        st.error("🔒 This section is for Admins only.")
        st.info("👉 Select 'Admin' from the sidebar and enter the correct password.")
        st.stop()

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
      ROUND(SUM(is_arrested) * 100.0 / COUNT(*), 2) AS arrest_rate
      FROM traffic_stops
      GROUP BY (driver_age / 10) * 10
      ORDER BY arrest_rate DESC;""",
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
            st.markdown("### Visualization")

            def show_insights(i1, i2, i3):
                st.markdown("### 🔍 Key Insights")
                c1, c2, c3 = st.columns(3)
                c1.info(i1)
                c2.info(i2)
                c3.info(i3)

        if selected_query == "top 10 vehicle Number involved in drug-related stops":
            fig = px.bar(result, x="vehicle_number", y="stop_count", title="Top 10 Vehicles in Drug-Related Stops")
            st.plotly_chart(fig, use_container_width=True)

            top_vehicle   = result.iloc[0]['vehicle_number']
            top_count     = result.iloc[0]['stop_count']
            second_vehicle= result.iloc[1]['vehicle_number']
            second_count  = result.iloc[1]['stop_count']
            bottom_vehicle= result.iloc[-1]['vehicle_number']
            bottom_count  = result.iloc[-1]['stop_count']
            total         = result['stop_count'].sum()
            top_pct       = round(top_count / total * 100, 1)
            top2_combined = top_count + second_count

            show_insights(
                f"🥇 **Top Vehicle**\n\n{top_vehicle} flagged {top_count} times ({top_pct}% of top 10)",
                f"🚗 **Top 2 Combined**\n\n{top_vehicle} & {second_vehicle} together: {top2_combined} stops",
                f"📉 **Lowest in List**\n\n{bottom_vehicle} with {bottom_count} stops — least flagged of top 10"
            )

        elif selected_query == "Which vehicles were most frequently searched?":
            fig = px.bar(result, x="vehicle_number", y="search_count", title="Most Frequently Searched Vehicles")
            st.plotly_chart(fig, use_container_width=True)

            top_vehicle    = result.iloc[0]['vehicle_number']
            top_searches   = result.iloc[0]['search_count']
            second_vehicle = result.iloc[1]['vehicle_number']
            bottom_vehicle = result.iloc[-1]['vehicle_number']
            bottom_searches= result.iloc[-1]['search_count']

            show_insights(
                f"🥇 **Most Searched**\n\n{top_vehicle} searched {top_searches} time(s) — highest priority vehicle",
                f"🔁 **Top 2**\n\n{top_vehicle} & {second_vehicle} are repeatedly searched",
                f"📉 **Least in List**\n\n{bottom_vehicle} with {bottom_searches} search(es)"
            )

        elif selected_query == "gender distribution of drivers stopped in each country":
            fig = px.bar(result, x="country_name", y="stop_count", color="driver_gender", barmode="group",
                         title="Gender Distribution by Country")
            st.plotly_chart(fig, use_container_width=True)

            top_row        = result.loc[result['stop_count'].idxmax()]
            top_gender     = top_row['driver_gender']
            top_country    = top_row['country_name']
            top_count      = top_row['stop_count']
            male_total     = result[result['driver_gender'] == 'Male']['stop_count'].sum()
            female_total   = result[result['driver_gender'] == 'Female']['stop_count'].sum()
            dominant_gender= "Male" if male_total > female_total else "Female"

            show_insights(
                f"🥇 **Highest Group**\n\n{top_gender} drivers in {top_country} — {top_count} stops",
                f"📊 **Overall Gender**\n\n{dominant_gender} stopped more overall (M: {male_total}, F: {female_total})",
                f"⚖️ **Bias Watch**\n\nGender gap in stops may indicate disproportionate enforcement"
            )

        elif selected_query == "race and gender combination has the highest search rate":
            fig = px.bar(result, x="driver_race", y="race_gender", color="driver_gender", barmode="group",
                         title="Search Rate by Race and Gender")
            st.plotly_chart(fig, use_container_width=True)

            top_race     = result.iloc[0]['driver_race']
            top_gender   = result.iloc[0]['driver_gender']
            top_count    = result.iloc[0]['race_gender']
            second_race  = result.iloc[1]['driver_race']
            second_gender= result.iloc[1]['driver_gender']
            second_count = result.iloc[1]['race_gender']
            total        = result['race_gender'].sum()
            top_pct      = round(top_count / total * 100, 1)
            top2_combined= top_count + second_count

            show_insights(
                f"🥇 **Top Combination**\n\n{top_race} ({top_gender}) — {top_count} searches ({top_pct}% of total)",
                f"🔁 **Top 2 Combined**\n\n{top_race} {top_gender} & {second_race} {second_gender}: {top2_combined} searches",
                f"⚠️ **Policy Flag**\n\nLarge disparities between groups may signal bias in search decisions"
            )

        elif selected_query == "average stop duration for different violations":
            fig = px.bar(result, x="violation", y="average_stop_duration", title="Average Stop Duration by Violation")
            st.plotly_chart(fig, use_container_width=True)

            longest_violation  = result.iloc[0]['violation']
            longest_duration   = result.iloc[0]['average_stop_duration']
            shortest_violation = result.iloc[-1]['violation']
            shortest_duration  = result.iloc[-1]['average_stop_duration']
            overall_avg        = round(result['average_stop_duration'].mean(), 2)

            show_insights(
                f"⏱️ **Longest Stop**\n\n{longest_violation} — avg {longest_duration} min",
                f"⚡ **Shortest Stop**\n\n{shortest_violation} — avg {shortest_duration} min",
                f"📊 **Overall Average**\n\nAll violations average {overall_avg} min"
            )

        elif selected_query == "countries report the highest rate of drug-related stops":
            fig = px.bar(result, x="country_name", y="drugs_stop", title="Drug-Related Stop Rate by Country")
            st.plotly_chart(fig, use_container_width=True)

            top_country     = result.iloc[0]['country_name']
            top_rate        = result.iloc[0]['drugs_stop']
            top_stops       = result.iloc[0]['total_stops']
            second_country  = result.iloc[1]['country_name']
            bottom_country  = result.iloc[-1]['country_name']
            bottom_rate     = result.iloc[-1]['drugs_stop']

            show_insights(
                f"🥇 **Highest Rate**\n\n{top_country} — {top_rate}% drug-related out of {top_stops} stops",
                f"📈 **Top 2**\n\n{top_country} & {second_country} show elevated drug activity",
                f"📉 **Lowest Rate**\n\n{bottom_country} — {bottom_rate}%"
            )

        elif selected_query == "arrest rate by country and violation":
            fig = px.bar(result, x="violation", y="arrest_rate", color="country_name", barmode="group",
                         title="Arrest Rate by Country and Violation")
            st.plotly_chart(fig, use_container_width=True)

            top_row        = result.loc[result['arrest_rate'].idxmax()]
            top_violation  = top_row['violation']
            top_country    = top_row['country_name']
            top_rate       = top_row['arrest_rate']
            avg_rate       = round(result['arrest_rate'].mean(), 2)
            zero_count     = len(result[result['arrest_rate'] == 0])

            show_insights(
                f"🥇 **Highest Arrest Rate**\n\n{top_violation} in {top_country} — {top_rate}% (avg: {avg_rate}%)",
                f"🌍 **Country Variation**\n\nSame violation leads to different arrest rates per country",
                f"🟢 **Zero Arrest Combos**\n\n{zero_count} country-violation pairs have 0% arrest rate"
            )

        elif selected_query == "time of day sees the most traffic stops":
            fig = px.bar(result, x="hour_of_day", y="stop_count", title="Traffic Stops by Hour of Day")
            st.plotly_chart(fig, use_container_width=True)

            peak_hour  = int(result.iloc[0]['hour_of_day'])
            peak_count = result.iloc[0]['stop_count']
            quiet_hour = int(result.loc[result['stop_count'].idxmin()]['hour_of_day'])
            quiet_count= result.loc[result['stop_count'].idxmin()]['stop_count']
            top3_total = result.nlargest(3, 'stop_count')['stop_count'].sum()

            show_insights(
                f"🕐 **Peak Hour**\n\n{peak_hour}:00 with {peak_count} stops",
                f"🌙 **Quietest Hour**\n\n{quiet_hour}:00 with only {quiet_count} stops",
                f"📊 **Top 3 Hours**\n\nBusiest 3 hours account for {top3_total} stops combined"
            )

        elif selected_query == "driver age group had the highest arrest rate":
            fig = px.bar(result, x="age_group", y="arrest_rate", title="Arrest Rate by Driver Age Group",
                         labels={"age_group": "Age Group", "arrest_rate": "Arrest Rate (%)"},
                         color="arrest_rate", color_continuous_scale="Reds")
            st.plotly_chart(fig, use_container_width=True)

            top_age  = int(result.iloc[0]['age_group'])
            top_rate = result.iloc[0]['arrest_rate']

            show_insights(
                f"🥇 **Highest Risk Group**\n\nDrivers in their {top_age}s — arrest rate {top_rate:.2f}%",
                f"🎯 **Targeted Action**\n\nRoad safety programs for this age bracket could reduce arrests",
                f"🔎 **Concentrated Pattern**\n\nEnforcement is focused within a specific age cohort"
            )

        elif selected_query == "Are stops during the night more likely to lead to arrests?":
            if 'time_of_day' in result.columns:
                day_row   = result[result['time_of_day'] == 'Day']
                night_row = result[result['time_of_day'] == 'Night']
                if not day_row.empty and not night_row.empty:
                    day_rate    = day_row['arrest_rate_percent'].values[0]
                    night_rate  = night_row['arrest_rate_percent'].values[0]
                    day_stops   = day_row['total_stops'].values[0]
                    night_stops = night_row['total_stops'].values[0]
                    diff        = round(abs(night_rate - day_rate), 2)
                    verdict     = f"Night is {diff}% more likely to arrest" if night_rate > day_rate else f"Day is {diff}% more likely to arrest"

                    fig = px.bar(result, x="time_of_day", y="arrest_rate_percent", color="time_of_day",
                                 title="Day vs Night Arrest Rate (%)", labels={"arrest_rate_percent": "Arrest Rate (%)"})
                    st.plotly_chart(fig, use_container_width=True)

                    show_insights(
                        f"🌞 **Day Stops**\n\n{day_stops:,} total stops — arrest rate {day_rate:.2f}%",
                        f"🌙 **Night Stops**\n\n{night_stops:,} total stops — arrest rate {night_rate:.2f}%",
                        f"✅ **Verdict**\n\n{verdict}"
                    )

        elif selected_query == "Which violations are most associated with searches or arrests?":
            fig = px.bar(result, x="violation", y=["search_rate_percent", "arrest_rate_percent"],
                         barmode="group", title="Search & Arrest Rate by Violation")
            st.plotly_chart(fig, use_container_width=True)

            top_arrest_violation = result.loc[result['arrest_rate_percent'].idxmax()]['violation']
            top_arrest_rate      = result.loc[result['arrest_rate_percent'].idxmax()]['arrest_rate_percent']
            top_search_violation = result.loc[result['search_rate_percent'].idxmax()]['violation']
            top_search_rate      = result.loc[result['search_rate_percent'].idxmax()]['search_rate_percent']
            avg_arrest           = round(result['arrest_rate_percent'].mean(), 2)

            show_insights(
                f"🚔 **Highest Arrest Rate**\n\n{top_arrest_violation} — {top_arrest_rate}%",
                f"🔍 **Most Searched**\n\n{top_search_violation} — {top_search_rate}% search rate",
                f"📊 **Average Arrest Rate**\n\n{avg_arrest}% across all violations"
            )

        elif selected_query == "violations are most common among younger drivers (<25)":
            fig = px.bar(result, x="violation", y="no_of_drivers", title="Most Common Violations — Drivers Under 25")
            st.plotly_chart(fig, use_container_width=True)

            top_violation    = result.iloc[0]['violation']
            top_count        = result.iloc[0]['no_of_drivers']
            second_violation = result.iloc[1]['violation']
            second_count     = result.iloc[1]['no_of_drivers']
            total            = result['no_of_drivers'].sum()
            top_pct          = round(top_count / total * 100, 1)
            top2_pct         = round((top_count + second_count) / total * 100, 1)

            show_insights(
                f"🥇 **Top Violation**\n\n{top_violation} — {top_count} cases ({top_pct}% of under-25 stops)",
                f"🔁 **Top 2 Together**\n\n{top_violation} & {second_violation} make up {top2_pct}% of under-25 violations",
                f"🎓 **Recommendation**\n\nTargeted education on these violations could reduce youth incidents"
            )

        elif selected_query == "Is there a violation that rarely results in search or arrest?":
            fig = px.bar(result, x="violation", y="action_rate_percent", title="Action Rate (Search or Arrest) by Violation")
            st.plotly_chart(fig, use_container_width=True)

            low_violation  = result.loc[result['action_rate_percent'].idxmin()]['violation']
            low_rate       = result.loc[result['action_rate_percent'].idxmin()]['action_rate_percent']
            high_violation = result.loc[result['action_rate_percent'].idxmax()]['violation']
            high_rate      = result.loc[result['action_rate_percent'].idxmax()]['action_rate_percent']
            avg_rate       = round(result['action_rate_percent'].mean(), 2)

            show_insights(
                f"✅ **Lowest Risk**\n\n{low_violation} — only {low_rate}% action rate (mostly warnings)",
                f"⚠️ **Highest Risk**\n\n{high_violation} — {high_rate}% almost always leads to action",
                f"📊 **Average Rate**\n\nOverall action rate is {avg_rate}%"
            )

        elif selected_query == "country has the most stops with search conducted":
            fig = px.bar(result, x="country_name", y="most_stops", title="Country with Most Searched Stops")
            st.plotly_chart(fig, use_container_width=True)

            top_country = result.iloc[0]['country_name']
            top_stops   = result.iloc[0]['most_stops']

            show_insights(
                f"🥇 **Top Country**\n\n{top_country} — {top_stops} stops with search conducted",
                f"🔎 **Why So High?**\n\nMay reflect stricter search laws or higher crime rates",
                f"📋 **Single Outlier**\n\nThis country stands clearly above the rest"
            )

        elif selected_query == "Yearly Breakdown of Stops and Arrests by Country":
            fig = px.line(result, x="year", y="arrest_rate", color="country_name", markers=True,
                          title="Yearly Arrest Rate by Country")
            st.plotly_chart(fig, use_container_width=True)

            top_row     = result.loc[result['arrest_rate'].idxmax()]
            top_country = top_row['country_name']
            top_year    = int(top_row['year'])
            top_rate    = top_row['arrest_rate']
            avg_rate    = round(result['arrest_rate'].mean(), 2)
            num_countries = result['country_name'].nunique()

            show_insights(
                f"📈 **Highest Year**\n\n{top_country} in {top_year} — arrest rate {top_rate}%",
                f"🌍 **Coverage**\n\n{num_countries} countries tracked, avg arrest rate: {avg_rate}%",
                f"📉 **Trend Reading**\n\nRising lines = stricter enforcement; falling = relaxed"
            )

        elif selected_query == "Driver Violation Trends Based on Age and Race":
            fig = px.scatter(result, x="driver_age", y="total_violations", color="driver_race",
                             title="Violation Trends by Age and Race", hover_data=["violation"])
            st.plotly_chart(fig, use_container_width=True)

            top_row   = result.loc[result['total_violations'].idxmax()]
            top_race  = top_row['driver_race']
            top_age   = int(top_row['driver_age'])
            top_count = top_row['total_violations']
            num_races = result['driver_race'].nunique()
            age_min   = result['driver_age'].min()
            age_max   = result['driver_age'].max()

            show_insights(
                f"🥇 **Highest Density**\n\n{top_race} drivers aged {top_age} — {top_count} total violations",
                f"🎨 **Dataset Scope**\n\n{num_races} racial groups across ages {age_min}–{age_max}",
                f"📌 **Dense Clusters**\n\nClusters indicate high-rate age-race combos for outreach"
            )

        elif selected_query == "Number of Stops by Year,Month, Hour of the Day":
            fig = px.line(result, x="stop_hour", y="total_stops", color="stop_month",
                          facet_col="stop_year", title="Hourly Stop Trends by Month (Faceted by Year)")
            st.plotly_chart(fig, use_container_width=True)

            peak_row   = result.loc[result['total_stops'].idxmax()]
            low_row    = result.loc[result['total_stops'].idxmin()]
            num_years  = result['stop_year'].nunique()

            peak_label = f"Year {int(peak_row['stop_year'])}, Month {int(peak_row['stop_month'])}, {int(peak_row['stop_hour'])}:00"
            low_label  = f"Year {int(low_row['stop_year'])}, Month {int(low_row['stop_month'])}, {int(low_row['stop_hour'])}:00"

            show_insights(
                f"🕐 **Busiest Period**\n\n{peak_label} — {peak_row['total_stops']} stops",
                f"🌙 **Quietest Period**\n\n{low_label} — only {low_row['total_stops']} stops",
                f"📅 **Data Span**\n\n{num_years} year(s) of data"
            )

        elif selected_query == "Violations with High Search and Arrest Rates":
            fig = px.scatter(result, x="search_rate", y="arrest_rate", size="total_stops", color="violation",
                             title="Search vs Arrest Rate by Violation", hover_name="violation")
            st.plotly_chart(fig, use_container_width=True)

            top_arrest_violation = result.loc[result['arrest_rate'].idxmax()]['violation']
            top_arrest_rate      = result.loc[result['arrest_rate'].idxmax()]['arrest_rate']
            top_search_violation = result.loc[result['search_rate'].idxmax()]['violation']
            top_search_rate      = result.loc[result['search_rate'].idxmax()]['search_rate']
            avg_arrest           = round(result['arrest_rate'].mean(), 2)

            show_insights(
                f"🚔 **Highest Arrest Rate**\n\n{top_arrest_violation} — {top_arrest_rate}%",
                f"🔍 **Most Searched**\n\n{top_search_violation} — {top_search_rate}% search rate",
                f"📊 **Average**\n\nAvg arrest rate: {avg_arrest}%"
            )

        elif selected_query == "Driver Demographics by Country(Age, Gender, and Race)":
            fig = px.bar(result, x="country_name", y="total_drivers", color="driver_race",
                         barmode="stack", title="Driver Demographics by Country")
            st.plotly_chart(fig, use_container_width=True)

            top_row      = result.loc[result['total_drivers'].idxmax()]
            top_race     = top_row['driver_race']
            top_gender   = top_row['driver_gender']
            top_country  = top_row['country_name']
            top_count    = top_row['total_drivers']
            num_countries= result['country_name'].nunique()
            num_races    = result['driver_race'].nunique()

            show_insights(
                f"🥇 **Largest Group**\n\n{top_race} {top_gender} in {top_country} — {top_count} stops",
                f"🌍 **Coverage**\n\n{num_countries} countries × {num_races} racial groups tracked",
                f"⚖️ **Equity Check**\n\nTall segments for one race may warrant equity audits"
            )

        elif selected_query == "Top 5 Violations with Highest Arrest Rates":
            fig = px.bar(result, x="violation", y="arrest_rate", title="Top 5 Violations by Arrest Rate",
                         color="arrest_rate", color_continuous_scale="Reds")
            st.plotly_chart(fig, use_container_width=True)

            top_violation    = result.iloc[0]['violation']
            top_rate         = result.iloc[0]['arrest_rate']
            top_total        = result.iloc[0]['total']
            second_violation = result.iloc[1]['violation']
            top_arrests      = result.iloc[0]['arrests']
            second_arrests   = result.iloc[1]['arrests']
            total_arrests    = result['arrests'].sum()

            show_insights(
                f"🥇 **#1 Violation**\n\n{top_violation} — {top_rate}% arrest rate across {top_total} stops",
                f"🔁 **Top 2 Combined**\n\n{top_violation} & {second_violation}: {top_arrests + second_arrests} of {total_arrests} arrests",
                f"📋 **All High Risk**\n\nAll 5 violations are well above average arrest rate"
            )

        else:
            st.info("No chart available for this query.")

        st.markdown("---")
        st.markdown("#### Raw Data")
        st.dataframe(result, use_container_width=True)
    else:
        st.warning("No results found for the selected query.")