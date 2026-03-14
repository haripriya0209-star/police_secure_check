# SecureCheck: A Python-SQL Digital Ledger for Police Post Logs

SecureCheck is a real-time traffic stop logging and analytics system designed for law enforcement agencies. It digitizes police check post operations using Python, SQL, and Streamlit — enabling faster decision-making, predictive tagging, and insightful dashboards.

---

## Project Overview

| Field | Details |
|---|---|
| **Domain** | Law Enforcement & Public Safety |
| **Tech Stack** | Python, MySQL, Streamlit |
| **Goal** | Replace manual logging with a centralized, intelligent system for tracking vehicle stops, violations, and officer actions |

---

## Key Features

- Real-time logging of traffic stops via Streamlit form
- **Live INSERT to MySQL** — every submitted stop is saved directly to the database
- **Role-based login** — Officer and Admin access levels with sidebar authentication
- **Flagged vehicle alert** — cross-checks every stop against a `flagged_vehicles` watchlist table
- Rule-based prediction of violations and outcomes
- SQL-powered analytics with 20 advanced queries
- Interactive dashboard with KPI metrics and Plotly visualizations
- Centralized MySQL database for check post operations
- **Modular code structure** — database logic separated into `db.py`

---

## Skills Demonstrated

- Python data preprocessing (`pandas`, `datetime`)
- SQL schema design and query optimization
- Streamlit dashboard development
- Plotly visualizations (bar, line, scatter, pie)
- `pymysql` integration for live database connectivity — reads and writes
- Rule-based logic and predictive tagging
- Role-based access control (Officer / Admin)
- Modular Python architecture — UI layer (`police.py`) separated from DB layer (`db.py`)

---

## Dataset

**Source**: `traffic_stops` table (MySQL) — loaded from `cleaned_traffic_stop.csv`

**Fields Include**:

| Column | Description |
|---|---|
| `stop_date`, `stop_time` | Date and time of the stop |
| `country_name` | Location of the check post |
| `driver_gender`, `driver_age`, `driver_race` | Driver demographics |
| `violation` | Type of traffic violation |
| `search_conducted`, `search_type` | Whether a search was done and its type |
| `stop_outcome` | Result (Warning / Citation / Arrest) |
| `is_arrested` | Boolean arrest flag |
| `stop_duration` | Duration category (0–15 Min, 16–30 Min, 30+ Min) |
| `drugs_related_stop` | Whether the stop was drug-related |
| `vehicle_number` | Registered vehicle number |
| `timestamp` | Combined datetime of the stop |

---

## Notebook Workflow (`setup_database.ipynb`)

The notebook prepares and loads traffic stop data into MySQL:

1. **Data Cleaning**
   - Drops empty columns
   - Fills missing `search_type` with `"No Search"`
   - Removes raw columns (`violation_raw`, `driver_age_raw`)

2. **Timestamp Creation**
   - Converts `stop_time` string to `datetime.time`
   - Combines `stop_date` and `stop_time` into a `timestamp` column
   - Saves updated CSV before database upload

3. **Database Setup**
   - Creates `Secure_check` database and `traffic_stops` table
   - Adds `timestamp` column using `information_schema` check to prevent duplicate column errors

4. **Data Insertion**
   - Reads cleaned CSV
   - Inserts all rows into MySQL using bulk upload

---

## Streamlit App Structure (`police.py`)

### Sidebar — Role-Based Login
- Select role: **Officer** or **Admin**
- Admin requires password (`admin123`) to unlock Tab 3
- Tab access is blocked with `st.stop()` if credentials are not met

### Tab 1 — Log a Stop
- Streamlit form for entering traffic stop details
- Validation checks for all required fields
- Rule-based prediction of violation type and stop outcome
- Auto-generated stop summary for officer review
- **Saves the stop to MySQL** via `insert_stop()` on every valid submission
- **Flagged vehicle check** — if the vehicle number is in the `flagged_vehicles` table, a red 🚨 alert is shown with the reason

### Tab 2 — View Insights
- **5 KPI metrics**: Total Stops, Total Arrests, Searches Conducted, Drug-Related Stops, Violation Detection Rate
- **6 Plotly charts**: Violations, Stop Outcomes, Gender, Race, Hourly Trends, Top Countries
- **50-row recent stops table** with full stop details

### Tab 3 — Advanced Queries (Admin only)
- Dropdown with **20 pre-built SQL queries**
- Dynamic query execution and result display
- Plotly charts (bar, line, scatter, pie) per query
- **3-column insight cards** highlighting key data findings per query
- Special day vs night arrest rate comparison logic

### Database Integration
- Connects to MySQL using `pymysql`
- Reusable `fetch_data()` function returns results as pandas DataFrames

---

## Install Dependencies

### 1. Create a virtual environment (optional)

```bash
python -m venv venv
venv\Scripts\activate
```

### 2. Install required packages

```bash
pip install streamlit==1.29.0 pandas==2.1.1 plotly==5.18.0 pymysql==1.1.0
```

Or install from a `requirements.txt`:

```
streamlit==1.29.0
pandas==2.1.1
plotly==5.18.0
pymysql==1.1.0
```

---

## How to Run

### 1. Set Up MySQL Database

- Create the `Secure_check` database in MySQL
- Run all cells in `setup_database.ipynb` to clean data and populate the `traffic_stops` table
- Create the `flagged_vehicles` watchlist table by running this in MySQL Workbench:

```sql
USE Secure_check;
CREATE TABLE IF NOT EXISTS flagged_vehicles (
    id INT AUTO_INCREMENT PRIMARY KEY,
    vehicle_number VARCHAR(20),
    reason VARCHAR(255),
    flagged_date DATE
);
-- Optional: add sample flagged vehicles for testing
INSERT INTO flagged_vehicles (vehicle_number, reason, flagged_date) VALUES
('AB1234', 'Repeat drug offender', '2026-01-15'),
('XY9999', 'Stolen vehicle', '2026-02-20');
```

### 2. Launch Streamlit Dashboard

```bash
streamlit run police.py
```

### 3. Login

| Role | Password | Access |
|---|---|---|
| Officer | *(none)* | Tab 1 + Tab 2 |
| Admin | `admin123` | Tab 1 + Tab 2 + Tab 3 |

---

## Dashboard Preview

| Tab | Description |
|---|---|
| **Log a Stop** | Form-based entry, rule-based prediction, INSERT to MySQL, flagged vehicle alert |
| **View Insights** | 5 KPI cards, 6 interactive charts, recent stops table |
| **Advanced Queries** | Admin only — 20 SQL queries with dynamic charts and insight cards |

---

## Project File Structure

| File | Purpose |
|---|---|
| `police.py` | Streamlit UI — all tabs, forms, charts, and layout |
| `db.py` | Database layer — `fetch_data`, `insert_stop`, `check_flagged_vehicle` |
| `setup_database.ipynb` | Data cleaning and MySQL table setup |
| `cleaned_traffic_stop.csv` | Source data (65,538 rows) |

