import pymysql
import pandas as pd

# ─────────────────────────────────────────
# DATABASE CONFIGURATION
# ─────────────────────────────────────────
DB_HOST     = "localhost"
DB_USER     = "root"
DB_PASSWORD = "HiAshwin@91"
DB_NAME     = "Secure_check"


# ─────────────────────────────────────────
# 1. Create a connection to MySQL
# ─────────────────────────────────────────
def create_connection():
    try:
        return pymysql.connect(
            host=DB_HOST,
            user=DB_USER,
            password=DB_PASSWORD,
            database=DB_NAME,
            cursorclass=pymysql.cursors.DictCursor
        )
    except Exception as e:
        print(f"Database connection failed: {e}")
        return None


# ─────────────────────────────────────────
# 2. Run any SELECT query and return a DataFrame
# ─────────────────────────────────────────
def fetch_data(query, params=None):
    conn = create_connection()
    if conn:
        with conn.cursor() as cursor:
            cursor.execute(query, params or ())
            result = cursor.fetchall()
        conn.close()
        return pd.DataFrame(result)
    return pd.DataFrame()


# ─────────────────────────────────────────
# 3. Insert a new traffic stop into MySQL
# ─────────────────────────────────────────
def insert_stop(stop_date, stop_time, country_name, driver_gender, driver_age,
                driver_race, search_conducted, search_type, drugs_related,
                stop_duration, vehicle_number, violation, stop_outcome):
    conn = create_connection()
    if conn:
        try:
            with conn.cursor() as cursor:
                cursor.execute("""
                    INSERT INTO traffic_stops (
                        stop_date, stop_time, country_name, driver_gender, driver_age,
                        driver_race, search_conducted, search_type, drugs_related_stop,
                        stop_duration, vehicle_number, violation, stop_outcome,
                        is_arrested, timestamp
                    ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                """, (
                    stop_date, stop_time, country_name, driver_gender, int(driver_age),
                    driver_race,
                    1 if search_conducted == "Yes" else 0,
                    search_type if search_conducted == "Yes" else "No Search",
                    1 if drugs_related == "Yes" else 0,
                    stop_duration,
                    vehicle_number.strip().upper(),
                    violation,
                    stop_outcome,
                    1 if stop_outcome == "Arrest" else 0,
                    str(stop_date) + " " + str(stop_time)
                ))
            conn.commit()   # permanently saves the row in MySQL
            return True
        except Exception as e:
            print(f"Failed to save stop: {e}") 
            return False
        finally:
            conn.close()
    return False


# ─────────────────────────────────────────
# 4. Check if a vehicle number is flagged
# ─────────────────────────────────────────
def check_flagged_vehicle(vehicle_number):
    conn = create_connection()
    if conn:
        with conn.cursor() as cursor:
            cursor.execute(
                "SELECT * FROM flagged_vehicles WHERE vehicle_number = %s",
                (vehicle_number,)
            )
            result = cursor.fetchone()
        conn.close()
        return result   # returns the row if flagged, or None if clean
    return None
