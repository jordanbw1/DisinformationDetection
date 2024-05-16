from helper_functions.database import execute_sql

def fail_running_tasks():
    try:
        status, message = execute_sql("UPDATE running_tasks SET status = 'FAILED' WHERE status = 'RUNNING';")
        if not status:
            print(f"Error failing running task: {message}")
            return False, f"Error failing running task: {message}"
        return True, "Good"
    except Exception as e:
        print(f"Error failing running tasks: {str(e)}")
        return False, f"Error failing running tasks: {str(e)}"
    
    