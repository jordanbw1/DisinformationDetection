from flask import Flask, render_template, request, send_from_directory, redirect, url_for, session, flash
from web_detect import run_prompt
import threading
import os
import sys
from dotenv import load_dotenv
from helper_functions.email_functions import check_email

# Determine the path to the .env file
env_path = os.path.join(os.path.dirname(sys.argv[0]), '..', '.env')

# Load .env variables
load_dotenv(env_path)

# Initialize App
app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY")


@app.route('/', methods=['GET'])
def index():
   # Render the index page
    return render_template('index.html')

@app.route('/submit-prompt', methods=['POST'])
def submit_prompt():
    # Get prompt and email
    prompt = request.form['prompt']
    email = request.form['email']

    # Ensure that correct email syntax is used
    if not check_email(email=email):
        flash("The email address you provided does not meet correct email format guidelines. Please try again.")
        return render_template('index.html')
    
    # Create a thread and pass the function to it
    thread = threading.Thread(target=run_prompt, args=(prompt,email,))
    thread.start()
    
    # Save their email and prompt to the session to be displayed later
    session['email'] = email
    session['prompt'] = prompt

    # Redirect to the confirmation page
    return redirect(url_for('confirmation'))

# Define the route for downloading files
@app.route('/download/<path:filename>',  methods=['GET'])
def download(filename):
    # Send the file to the user
    return send_from_directory("dynamic/prompt_results", filename)

@app.route('/confirmation', methods=["GET"])
def confirmation():
    if not session.get('email') or not session.get('prompt'):
        return redirect(url_for('index'))
    email = session.pop('email', None)
    prompt = session.pop('prompt', None)
    return render_template("confirmation.html", email=email, prompt=prompt)

if __name__ == '__main__':
    app.run(debug=True)
