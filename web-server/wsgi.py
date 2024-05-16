from main import app
from helper_functions.fail_running_tasks import fail_running_tasks

if __name__ == "__main__":
    fail_running_tasks()
    app.run(port=8080)
