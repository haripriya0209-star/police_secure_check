# SecureCheck: A Python-SQL Digital Ledger for Police Post Logs
SecureCheck is a real-time traffic stop logging and analytics system designed for law enforcement agencies. It digitizes police check post operations using Python, SQL, and Streamlit — enabling faster decision-making, predictive tagging, and insightful dashboards.

## Project Overview
- **Domain**: Law Enforcement & Public Safety  
- **Tech Stack**: Python, SQL (MySQL/PostgreSQL), Streamlit  
- **Goal**: Replace manual logging with a centralized, intelligent system for tracking vehicle stops, violations, and officer actions.
- 
- ##  Key Features
- Real-time logging of traffic stops via Streamlit form  
- Rule-based prediction of violations and outcomes  
- SQL-powered analytics and advanced queries  
- Interactive dashboard with visualizations (Plotly, Matplotlib)  
- Centralized database for multi-location check posts  

## Skills Demonstrated

- Python data preprocessing (`pandas`, `datetime`)  
- SQL schema design and query optimization  
- Streamlit dashboard development  
- Plotly visualizations  
- Integration of rule-based logic and predictive tagging

- ## Dataset

**Source**: `traffic_stops`  
**Fields Include**:
- `stop_date`, `stop_time`, `country_name`, `driver_gender`, `driver_age`, `driver_race`  
- `violation`, `search_conducted`, `search_type`, `stop_outcome`, `is_arrested`, `stop_duration`, `drugs_related_stop`, `vehicle_number`

- ## VS code ipynb file Workflow

The notebook prepares and loads traffic stop data into MySQL:

1. **Data Cleaning**  
   - Drops empty columns  
   - Fills missing `search_type` with `"No Search"`  
   - Removes raw columns (`violation_raw`, `driver_age_raw`)

2. **Timestamp Creation**  
   - Combines `stop_date` and `stop_time` into a `timestamp` column

3. **Database Setup**  
   - Creates `Secure_check` database and `traffic_stops` table  
   - Adds `timestamp` column and ensures `stop_time` is stored as `TIME`

4. **Data Insertion**  
   - Reads cleaned CSV  
   - Inserts all rows into MySQL using bulk upload

---
## 🔧 Streamlit App Structure (`police.py`)

This Python file powers the SecureCheck dashboard:

### 1. **Log a Stop (Tab 1)**
- Streamlit form for entering traffic stop details  
- Validation checks for required fields  
- Rule-based prediction of violation and outcome  
- Summary generator for officer review

### 2. **View Insights (Tab 2)**
- Displays recent traffic stops from the database  
- Formats `stop_time` for readability (e.g., `12:30 PM`)  
- Handles missing or improperly stored time values gracefully

### 3. ** Advanced Queries (Tab 3)**
- Dropdown menu with 15+ SQL queries  
- Dynamic execution and result display  
- Visualizations using Plotly (bar, line, scatter)  
- Special logic for comparing day vs night arrest rates

### 4. ** Database Integration**
- Connects to MySQL using `pymysql`  
- Uses a reusable `fetch_data()` function to run queries and return results as DataFrames

---

## Install Dependencies

To run the dashboard locally:

### 1. Create a virtual environment (optional)
```bash
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

Install required packages:

streamlit==1.29.0
pandas==2.1.1
plotly==5.18.0
matplotlib==3.8.0
pymysql==1.1.0
mysql-connector-python==8.3.0


## How to run

1. **Clone the Repository**
bash
git clone https://github.com/your-username/SecureCheck.git
cd SecureCheck

2. **Set Up MySQL Database**
Create database Secure_check

Run the schema and data upload steps from the notebook

3. **Launch Streamlit Dashboard**
bash
streamlit run police.py

 **Dashboard Preview**
Tab 1: Log a Stop — Form-based entry with rule-based prediction

Tab 2: View Insights — Recent logs with formatted timestamps

Tab 3: Advanced Queries — Select and visualize SQL analytics
