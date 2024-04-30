from flask import Flask, render_template, request, send_from_directory, redirect, url_for, session, flash
from web_detect import run_prompt
import threading
import os
import sys
from dotenv import load_dotenv
from helper_functions.email_functions import check_email, send_verification_email, resend_verification_email, validate_password, send_reset_password_email
from helper_functions.api import test_key
from routes.documents import documents
import mysql.connector
from helper_functions.database import get_db_connection, execute_sql, sql_results_one
from helper_functions.prompt import append_instructions
from helper_functions.reset_password import is_valid_token, get_user_from_token
import hashlib
import secrets


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
app.register_blueprint(documents, url_prefix="/documents")


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
        return redirect(url_for('login'))
    
    if session['confirmed'] != True:
        return redirect(url_for('verify_email'))
    
@app.route('/', methods=['GET'])
def index():
   # Render the index page
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

        conn = get_db_connection()
        cursor = conn.cursor()
        try:
            # Execute the SQL query to fetch the hashed password associated with the username
            query = "SELECT user_id, password, salt, confirmed FROM users WHERE email = %s"
            cursor.execute(query, (email,))
            result = cursor.fetchone()
            cursor.close()
            conn.close()

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
            session["confirmed"] = bool(result[1])

            return redirect(url_for('index'))

        except mysql.connector.Error as err:
            flash(f"Unknown error occurred during login.", 'error')
            return render_template("login.html")
        finally:
            conn.close()

@app.route('/logout')
@login_exempt
def logout():
    session.pop('user_id', None)
    session.pop('email', None)
    session.pop('confirmed', None)
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
        email = request.form['email']
        password = request.form['password']
        confirm_password = request.form['confirmpassword']

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
        
        status, message = execute_sql("INSERT INTO users (email, password, salt) VALUES (%s, %s, %s);", (email, hashed_password, salt))
        if not status:
            flash(f"Registration failed: {message}", 'error')
            return render_template("register.html")
        
        # Get the user_id
        status, message, result = sql_results_one("SELECT user_id FROM users WHERE email = %s;", (email,))
        if not status or not result:
            flash(f"Registration failed: {message}", 'error')
            return render_template("register.html")
        user_id = result[0]

        # Set session variables
        session["user_id"] = user_id
        session["email"] = email
        session['confirmed'] = False

        # Send verification code to email
        send_verification_email(email)
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
    # Get prompt and email
    email = session["email"]
    prompt = request.form['prompt']
    api_key = request.form['api-key']
    num_rows = request.form.get('num-rows', type=int)
    if num_rows is None or num_rows < 1 or num_rows > 500:
        print(f"out of bounds: {num_rows}")
        num_rows = 300

    # Ensure that correct email syntax is used
    if not check_email(email=email):
        flash("The email address you provided does not meet correct email format guidelines. Please try again.", 'error')
        return redirect(url_for('index'))
    
    # Test API key before starting
    success, message = test_key(api_key=api_key)
    if not success:
        flash(f"API Key error: {message}", 'error')
        return redirect(url_for('index'))
    
    # Add instructions to the user's prompt
    full_prompt = append_instructions(prompt=prompt)

    # Get the url for the server
    base_url = request.host_url

    # Create a thread and pass the function to it
    thread = threading.Thread(target=run_prompt, args=(api_key,full_prompt,email,base_url,num_rows,))
    thread.start()
    
    # Save their prompt to the session to be displayed later
    session['prompt'] = full_prompt

    # Redirect to the confirmation page
    return redirect(url_for('confirmation'))

@app.route('/test-key', methods=['GET', 'POST'])
def test_key_route():
    if request.method == 'POST':
        api_key = request.form['api-key']
        
        # Create a thread and pass the function to it
        status, message = test_key(api_key)

        if status:
            flash("Your API key successfully established a connection!", 'success')
        else:
            flash("Your API key failed to establish a connection.", 'error')

        # Redirect to the confirmation page
        return render_template("test_key.html")
    return render_template("test_key.html")

# Define the route for downloading files
@app.route('/download/<path:filename>',  methods=['GET'])
def download(filename):
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
        status, message = is_valid_token(token)
        if not status:
            flash(message, 'error')
            return redirect(url_for('forgot_password'))
        return render_template('reset_password.html')
    elif request.method == 'POST':
        # Verify the token and check if it's still valid
        status, message = is_valid_token(token)
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

## --------- Helper Functions --------- ##
# Generate a random salt
def generate_salt():
    return secrets.token_hex(16)  # 16 bytes = 128 bits

# Hash the password with the provided salt
def hash_password(password, salt):
    return hashlib.sha256((password + salt).encode()).hexdigest()
## --------- End Helper Functions --------- ##

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080, debug=True)
