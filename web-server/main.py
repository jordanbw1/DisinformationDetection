from flask import Flask, render_template, request, send_from_directory, redirect, url_for, session, flash
from web_detect import run_prompt
import threading
import os
import sys
from dotenv import load_dotenv
from helper_functions.email_functions import check_email, send_verification_email, resend_verification_email, validate_password, send_reset_password_email
from helper_functions.api import test_gemini_key, test_chatgpt_key
from routes.documents import documents_routes
from routes.account import account_routes
from routes.admin import admin_routes
from routes.challenge import challenge_routes
from routes.organizer import organizer_routes
from helper_functions.fail_running_tasks import fail_running_tasks
import mysql.connector
from helper_functions.database import get_db_connection, execute_sql, sql_results_one, sql_results_all, execute_sql_return_id
from helper_functions.prompt import append_instructions, get_instructions
from helper_functions.account_actions import is_valid_password_token, get_user_from_token, validate_user_name
from flask_wtf import CSRFProtect
import hashlib
import secrets
import json


# Decorator used to exempt route from requiring login
def login_exempt(f):
    f.login_exempt = True
    return f

# Determine the path to the .env file
env_path = os.path.join(os.path.dirname(sys.argv[0]), '..', '.env')

# Load .env variables
load_dotenv(env_path)

# Initialize App
app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY")
app.register_blueprint(documents_routes, url_prefix="/documents")
app.register_blueprint(account_routes, url_prefix="/account")
app.register_blueprint(admin_routes, url_prefix="/admin")
app.register_blueprint(challenge_routes, url_prefix="/challenge")
app.register_blueprint(organizer_routes, url_prefix="/organizer")

# Initialize CSRF protection
csrf = CSRFProtect()
csrf.init_app(app)


@app.before_request
def default_login_required():
    # exclude 404 errors and static routes
    # uses split to handle blueprint static routes as well
    if not request.endpoint or request.endpoint.rsplit('.', 1)[-1] == 'static':
        return

    view = app.view_functions[request.endpoint]

    if getattr(view, 'login_exempt', False):
        return

    if 'email' not in session:
        session['attempted_route'] = request.url
        return redirect(url_for('login'))
    
    if session['confirmed'] != True:
        return redirect(url_for('verify_email'))
    
@app.route('/', methods=['GET'])
def index():
    return render_template('index.html')

# for example, the login page shouldn't require login
@app.route('/login', methods=['GET', 'POST'])
@login_exempt
def login():
    if 'email' in session:
        return redirect(url_for('index'))
    if request.method == "GET":
        return render_template('login.html')
    elif request.method == "POST":
        email = request.form['email']
        password = request.form['password']

        # Use regex to confirm email is valid email format
        if not check_email(email):
            flash("Invalid email format", 'error')
            return render_template("register.html")

        conn = get_db_connection()
        cursor = conn.cursor()
        try:
            # Execute the SQL query to fetch the hashed password associated with the username
            status, message, result = sql_results_one("SELECT user_id, password, salt, confirmed, full_name FROM users WHERE email = %s;", (email,))

            # If no result found for the given username, return False
            if not result:
                flash(f"Username or password is invalid", 'error')
                return render_template("login.html")

            # Extract the hashed password and salt from the result
            hashed_password_in_db = result[1]
            salt = result[2]

            # Hash the provided password with the retrieved salt
            hashed_password = hash_password(password, salt)
            
            # Compare the hashed passwords
            if hashed_password != hashed_password_in_db:
                flash(f"Username or password is invalid", 'error')
                return render_template("login.html")
            
            # Set user as logged in
            session["user_id"] = result[0]
            session["email"] = email
            session["confirmed"] = bool(result[3])
            session["full_name"] = result[4]

            # Add any roles if user has them
            # Fetch user roles from the database
            status, message, user_roles = sql_results_all("SELECT role_name FROM user_roles JOIN roles ON user_roles.role_id = roles.role_id WHERE user_roles.user_id = %s;", (session["user_id"],))
            if status:
                session["user_roles"] = [role[0] for role in user_roles]
            else:
                print(f"Failed to fetch user roles: {message}")
                flash(f"Failed to fetch user roles: {message}", 'error')
                return render_template("login.html")
            
            # Get gemini key if they have one
            status, message, result = sql_results_one("SELECT `key` FROM gemini_keys WHERE user_id = %s;", (session["user_id"],))
            if status and result:
                session["gemini_key"] = result[0]
            else:
                session["gemini_key"] = None

            # Redirect them to their requested page
            if session.get('attempted_route'):
                return redirect(session.pop('attempted_route'))
            # Redirect them to the index page
            return redirect(url_for('index'))

        except mysql.connector.Error as err:
            flash(f"Unknown error occurred during login: {err}", 'error')
            return render_template("login.html")
        finally:
            conn.close()

@app.route('/logout')
@login_exempt
def logout():
    session.clear()
    return redirect(url_for('login'))

@app.route('/register', methods=['GET', 'POST'])
@login_exempt
def register():
    if 'email' in session:
        return redirect(url_for('index'))
    if request.method == "GET":
        return render_template('register.html')
    elif request.method == "POST":
        # Get form values
        full_name = request.form['fullName']
        email = request.form['email']
        password = request.form['password']
        confirm_password = request.form['confirmpassword']

        # Check that users name is alphanumeric
        status, message = validate_user_name(full_name)
        if not status:
            flash(message, "error")
            return render_template("register.html")

        # Confirm that passwords match
        if password != confirm_password:
            flash("Password and confirm password do not match", 'error')
            return render_template("register.html")
        
        # Confirm strong password
        status, message = validate_password(password)
        if not status:
            flash(message, 'error')
            return render_template("register.html")

        # Use regex to confirm email is valid email format
        if not check_email(email):
            flash("Invalid email format", 'error')
            return render_template("register.html")
        
        # Generate salt
        salt = generate_salt()
        
        # Hash the password with salt
        hashed_password = hash_password(password, salt)
        
        status, message, result = execute_sql_return_id("INSERT INTO users (full_name, email, password, salt) VALUES (%s, %s, %s, %s);", (full_name, email, hashed_password, salt))
        if not status:
            if message.find("Duplicate entry") != -1:
                flash("Email already registered to an account", 'error')
            else:
                flash(f"Registration failed: {message}", 'error')
            return render_template("register.html")
        if not result:
            flash(f"Registration failed: {message}", 'error')
            return render_template("register.html")
        user_id = result

        # Set session variables
        session["full_name"] = full_name
        session["user_id"] = user_id
        session["email"] = email
        session['confirmed'] = False

        # Send verification code to email
        status, message = send_verification_email(email)
        # Handle email send errors.
        if not status:
            # Remove created user account from DB
            status2, message2 = execute_sql("""DELETE FROM users WHERE user_id = %s""", (user_id),)
            session.clear() # Clear session so no weird auth happens
            # Handle errors in DB call
            if not status2:
                flash(f"Unknown error occured: {message2} While trying to handle another error: {message}", "error")
                return render_template("register.html")
            # Tell user the email failed to send, account changes reverted
            flash(f"Unknown error occured while trying to send verification email, user account changes reverted. Please try again or contact support. Error: {message}")
            return render_template("register.html")

        return redirect(url_for('verify_email'))

@app.route('/verify-email', methods=['GET', 'POST'])
@login_exempt
def verify_email():
    # Send them to register if they haven't created an account yet
    if 'email' not in session:
        return redirect(url_for('register'))
    # If they have already verified their email, send them to index
    if session["confirmed"] != False:
        return redirect(url_for('index'))
    if request.method == "GET":
        return render_template('verify_email.html')
    elif request.method == "POST":
        # If the verification code matches, confirm them in the database and change session variable to True
        conn = get_db_connection()
        cursor = conn.cursor()
        try:
            email = session["email"]
            code = request.form["code"]
            # Check if code is valid
            sql = """SELECT COUNT(*) AS count FROM users
                        JOIN verify_code
                        WHERE email = %s AND code = %s;"""
            val = (email, code)
            cursor.execute(sql, val)
            # Get the result as bool
            is_authenticated = bool(cursor.fetchone()[0])
            # Close connections
            cursor.close()
            conn.close()
            if not is_authenticated:
                return False, "Code doesn't match"
            
            # Mark user as authenticated in the db now
            conn = get_db_connection()
            cursor = conn.cursor()
            sql = """UPDATE users
                        SET confirmed = 1
                        WHERE email = %s;"""
            val = (email,)
            cursor.execute(sql, val)
            conn.commit()
            cursor.close()

            # Remove the old verification code
            conn = get_db_connection()
            cursor = conn.cursor()
            sql = """DELETE FROM verify_code
                        WHERE user_id = (SELECT user_id FROM users WHERE email = %s);"""
            val = (email,)
            cursor.execute(sql, val)
            conn.commit()
            cursor.close()

            session["confirmed"] = True

            # Redirect them to their requested page
            if session.get('attempted_route'):
                return redirect(session.pop('attempted_route'))
            # Send them to the index page
            return redirect(url_for('index'))
        except Exception as e:
            flash(f"Verification failed: unknown error occurred.", 'error')
            return redirect(url_for('verify_email'))
        finally:
            conn.close()

@app.route('/resend-verify-code', methods=['GET'])
@login_exempt
def resend_verify_code():
    email = session["email"]
    resend_verification_email(email)
    return redirect(url_for("verify_email"))

@app.route('/submit-prompt', methods=['POST'])
def submit_prompt():
    # Retrieve user's roles from the session
    user_roles = session.get("user_roles", [])
    # Determine the maximum number of rows allowed based on user roles
    if "prompt_engineer" in user_roles:
        max_rows = None  # Set to None to indicate no limit for engineers
    else:
        max_rows = 500  # Default maximum rows for non-engineers
    
    # Get prompt and email
    email = session["email"]
    prompt = request.form['prompt']
    dataset_name = request.form['dataset']
    num_rows = request.form.get('num-rows', type=int)
    api_key = session["gemini_key"]
    
    # If the user doesn't have a gemini key, redirect them to the account page
    if api_key is None:
        flash("Please enter a Gemini key before testing prompts.", 'info')
        return redirect(url_for('account.account_page'))

    # Check if the specified number of rows exceeds the maximum allowed
    if num_rows is None or (max_rows is not None and (num_rows < 1 or num_rows > max_rows)):
        num__rows = 300  # Default to 300 rows if invalid or not specified

    # Validate dataset name against mapping
    dataset_mapping = load_dataset_mapping()
    if dataset_name not in dataset_mapping:
        flash("Invalid dataset selected.", 'error')
        return redirect(url_for('index'))
    
    # Get folder and filename for the selected dataset
    dataset_info = dataset_mapping.get(dataset_name)
    if dataset_info is None or 'directory' not in dataset_info:
        flash("Dataset not in allowed list.", 'error')
        return redirect(url_for('index'))

    dataset_folder, dataset_filename = dataset_info.get('directory', (None, None))
    if dataset_folder is None or dataset_filename is None:
        flash("Invalid dataset information.", 'error')
        return redirect(url_for('index'))
    dataset_subject = dataset_info.get('subject', '')

    # Check to see if user has another prompt currently running
    status, message, result = sql_results_all("SELECT * FROM running_tasks WHERE user_id = %s AND status = 'RUNNING';", (session["user_id"],))
    if not status:
        flash(f"Error checking for running tasks: {message}", 'error')
        return redirect(url_for('index'))
    if result:
        flash("You already have a prompt running. Please wait for it to finish before submitting another.", 'error')
        return redirect(url_for('index'))
    
    # Test API key before starting
    success, message = test_gemini_key(api_key=api_key)
    if not success:
        flash(f"API Key error: {message}", 'error')
        return redirect(url_for('index'))

    # Get the url for the server
    base_url = request.host_url

    # Get the user_id
    user_id = session["user_id"]

    # Prepare dataset info
    dataset_info = {
        'name': dataset_name,
        'folder': dataset_folder,
        'filename': dataset_filename,
        'subject': dataset_subject
    }

    # Create a thread and pass the function to it
    thread = threading.Thread(target=run_prompt, args=(api_key,prompt,email,base_url,user_id,dataset_info,num_rows,None,))
    thread.start()
    
    # Save their prompt to the session to be displayed later
    full_prompt = append_instructions(prompt=prompt)
    session['prompt'] = full_prompt

    # Redirect to the confirmation page
    return redirect(url_for('confirmation'))

# Recieves request to download a file and redirects to downloading route
@app.route('/download/<path:filename>',  methods=['GET'])
def download(filename):
    # Render page that redirects user to download file route
    return render_template("download_redirect.html", filename=filename)

# Define the route for downloading files
@app.route('/download-file/<path:filename>',  methods=['GET'])
def download_file(filename):
    # Send the file to the user
    return send_from_directory("dynamic/prompt_results", filename)

@app.route('/confirmation', methods=["GET"])
def confirmation():
    # Make sure prompt is set
    if not session.get('prompt'):
        return redirect(url_for('index'))
    # Remove prompt from session
    prompt = session.pop('prompt', None)
    return render_template("confirmation.html", prompt=prompt)

# Define a route for the reset password request form
@app.route('/forgot-password', methods=['GET', 'POST'])
@login_exempt
def forgot_password():
    if request.method == 'GET':
        return render_template('forgot_password.html')
    elif request.method == 'POST':
        email = request.form['email']

        # Send an email to the user with a link to the reset password page
        base_url = request.host_url
        status, message = send_reset_password_email(base_url, email)
        if not status:
            flash(f"Error sending reset password email: {message}", 'error')
            return render_template('forgot_password.html')

        # Redirect the user to a confirmation page
        return redirect(url_for('reset_password_confirmation'))

# Define a route for the reset password page
@app.route('/reset-password/<token>', methods=['GET', 'POST'])
@login_exempt
def reset_password(token):    
    if request.method == 'GET':
        # Verify the token and check if it's still valid
        status, message = is_valid_password_token(token)
        if not status:
            flash(message, 'error')
            return redirect(url_for('forgot_password'))
        return render_template('reset_password.html')
    elif request.method == 'POST':
        # Verify the token and check if it's still valid
        status, message = is_valid_password_token(token)
        if not status:
            flash(message, 'error')
            return redirect(url_for('forgot_password'))
        
        # Get passwords from the form
        new_password = request.form['password']
        confirm_password = request.form['confirmpassword']

        # Confirm that passwords match
        if new_password != confirm_password:
            flash("Password and confirm password do not match", 'error')
            return render_template('reset_password.html')
        
        # Confirm strong password
        status, message = validate_password(new_password)
        if not status:
            flash(message, 'error')
            return render_template("reset_password.html")

        # Get the user_id associated with the token
        status, message, user_id = get_user_from_token(token)
        if not status:
            flash(message, 'error')
            return redirect(url_for('forgot_password'))
        
        # Update the user's password in the database
        # Generate salt
        salt = generate_salt()
        
        # Hash the password with salt
        hashed_password = hash_password(new_password, salt)
        
        # Update the password
        status, message = execute_sql("UPDATE users SET password = %s, salt = %s WHERE user_id = %s;", (hashed_password, salt, user_id))
        if not status:
            flash(f"Error updating password: {message}", 'error')
            return render_template('reset_password.html')

        # Delete the token from the database
        status, message = execute_sql("DELETE FROM password_reset_tokens WHERE token = %s;", (token,))
        if not status:
            flash(f"Error deleting password reset token: {message}", 'error')
            return render_template('reset_password.html')

        # Redirect the user to a confirmation page or login page
        return redirect(url_for('login'))  # You can choose where to redirect after password reset

# Define a route for the reset password confirmation page
@app.route('/reset-password-confirmation', methods=['GET'])
@login_exempt
def reset_password_confirmation():
    return render_template('reset_password_confirmation.html')

# Privacy Policy
@app.route('/privacy', methods=['GET'])
@login_exempt
def privacy():
    return render_template('privacy.html')

# Cookies Policy
@app.route('/cookies', methods=['GET'])
@login_exempt
def cookies():
    return render_template('cookies.html')


## --------- Helper Functions --------- ##
# Generate a random salt
def generate_salt():
    return secrets.token_hex(16)  # 16 bytes = 128 bits

# Hash the password with the provided salt
def hash_password(password, salt):
    return hashlib.sha256((password + salt).encode()).hexdigest()

def load_dataset_mapping():
    with open('static/datasets/dataset_mapping.json', 'r') as f:
        return json.load(f)
## --------- End Helper Functions --------- ##

if __name__ == '__main__':
    fail_running_tasks()
    app.run(host='0.0.0.0', port=8080, debug=True)
