import os
import mysql.connector

# Get database connection
def get_db_connection():
    conn = mysql.connector.connect(
        host=os.getenv("DB_HOST"),
        user=os.getenv("DB_USER"),
        password=os.getenv("DB_PASSWORD"),
        database=os.getenv("DB_DATABASE")
    )
    return conn

# Execute generic sql query
def execute_sql(query, values=None):
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        if values:
            cursor.execute(query, values)
        else:
            cursor.execute(query)
        conn.commit()
    except mysql.connector.Error as err:
        print(f"Error executing SQL query: {err}")
        conn.rollback()
        return False, f"Error executing SQL query: {err}"
    finally:
        cursor.close()
        conn.close()
    return True, "Good"

# Execute generic sql query
def execute_sql_return_id(query, values):
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute(query, values)
        conn.commit()
        last_insert_id = cursor.lastrowid
    except mysql.connector.Error as err:
        print(f"Error executing SQL query: {err}")
        conn.rollback()
        return False, f"Error executing SQL query: {err}", None
    finally:
        cursor.close()
        conn.close()
    return True, "Good", last_insert_id

# Execute generic sql query
def sql_results_one(query, values=None):
    conn = get_db_connection()
    cursor = conn.cursor()
    results = None
    try:
        if values:
            cursor.execute(query, values)
        else:
            cursor.execute(query)
        results = cursor.fetchone()
    except mysql.connector.Error as err:
        print(f"Error executing SQL query: {err}")
        conn.rollback()
        return False, f"Error executing SQL query: {err}", None
    finally:
        cursor.close()
        conn.close()
    return True, "Good", results

# Execute generic sql query
def sql_results_all(query, values=None):
    conn = get_db_connection()
    cursor = conn.cursor()
    results = None
    try:
        if values:
            cursor.execute(query, values)
        else:
            cursor.execute(query)
        results = cursor.fetchall()
    except mysql.connector.Error as err:
        print(f"Error executing SQL query: {err}")
        conn.rollback()
        return False, f"Error executing SQL query: {err}", None
    finally:
        cursor.close()
        conn.close()
    return True, "Good", results