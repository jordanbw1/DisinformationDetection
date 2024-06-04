import os
import mysql.connector

# Get database connection
def get_db_connection():
    """
    Get a connection to the database.
    
    :return: A connection to the database
    """
    conn = mysql.connector.connect(
        host=os.getenv("DB_HOST"),
        user=os.getenv("DB_USER"),
        password=os.getenv("DB_PASSWORD"),
        database=os.getenv("DB_DATABASE")
    )
    return conn

# Execute generic sql query
def execute_sql(query, values=None):
    """
    Execute a SQL query.
    
    :param query: The SQL query to execute
    :param values: The values to pass to the query
    :return: A tuple containing a boolean indicating success and a message
    """
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
def execute_many_sql(query, values=None):
    """
    Execute a SQL query using executemany.
    
    :param query: The SQL query to execute
    :param values: The values to pass to the query
    :return: A tuple containing a boolean indicating success and a message
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        if values:
            cursor.executemany(query, values)
        else:
            cursor.executemany(query)
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
    """
    Execute a SQL query and return the id of inserted result.
    
    :param query: The SQL query to execute
    :param values: The values to pass to the query
    :return: A tuple containing a boolean indicating success, a message, and the inserted item id
    """
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
    """
    Execute a SQL query and return the first result.
    
    :param query: The SQL query to execute
    :param values: The values to pass to the query
    :return: A tuple containing a boolean indicating success, a message, and the result
    """
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
    """
    Execute a SQL query and return all results.
    
    :param query: The SQL query to execute
    :param values: The values to pass to the query
    :return: A tuple containing a boolean indicating success, a message, and the results
    """
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

# Database class for executing without commmiting
class Database:
    def __init__(self):
        self.conn = None
        self.cursor = None
        self.in_transaction = False

    def connect(self):
        """
        Establish a connection to the database.
        """
        if not self.conn:
            self.conn = get_db_connection()
            self.cursor = self.conn.cursor()

    def disconnect(self):
        """
        Close the database connection.
        """
        if self.conn:
            self.cursor.close()
            self.conn.close()
            self.conn = None
            self.cursor = None

    def begin_transaction(self):
        """
        Begin a database transaction.
        """
        if not self.in_transaction:
            self.connect()
            self.cursor.execute("BEGIN")
            self.in_transaction = True

    def commit(self):
        """
        Commit the current transaction.
        """
        if self.in_transaction:
            self.conn.commit()
            self.in_transaction = False

    def rollback(self):
        """
        Rollback the current transaction.
        """
        if self.in_transaction:
            self.conn.rollback()
            self.in_transaction = False

    def execute(self, query, values=None):
        """
        Execute a SQL query.
        
        :param query: The SQL query to execute
        :param values: The values to pass to the query
        :return: A tuple containing a boolean indicating success and a message
        """
        try:
            if values:
                self.cursor.execute(query, values)
            else:
                self.cursor.execute(query)
            return True, "Good"
        except mysql.connector.Error as err:
            print(f"Error executing SQL query: {err}")
            return False, f"Error executing SQL query: {err}"
    
    def execute_return_id(self, query, values):
        try:
            self.cursor.execute(query, values)
            last_insert_id = self.cursor.lastrowid
            return True, "Good", last_insert_id
        except mysql.connector.Error as err:
            print(f"Error executing SQL query: {err}")
            return False, f"Error executing SQL query: {err}", None
        
    def execute_fetchone(self, query, values=None):
        """
        Execute a SQL query and return the first result.
        
        :param query: The SQL query to execute
        :param values: The values to pass to the query
        :return: A tuple containing a boolean indicating success, a message, and the result
        """
        status, message = self.execute(query, values)
        if status:
            result = self.cursor.fetchone()
            return True, message, result
        else:
            return False, message, None

    def execute_fetchall(self, query, values=None):
        """
        Execute a SQL query and return all results.
        
        :param query: The SQL query to execute
        :param values: The values to pass to the query
        :return: A tuple containing a boolean indicating success, a message, and the results
        """
        status, message = self.execute(query, values)
        if status:
            results = self.cursor.fetchall()
            return True, message, results
        else:
            return False, message, None

    def __enter__(self):
        """
        Context manager for entering a transaction.
        """
        self.begin_transaction()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """
        Context manager for committing or rolling back a transaction.
        """
        if exc_type:
            self.rollback()
        elif self.in_transaction:
            self.commit()
            self.disconnect()