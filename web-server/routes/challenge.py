from flask import Blueprint, render_template, flash, redirect, url_for, request, session, jsonify
from helper_functions.database import execute_sql, sql_results_one, sql_results_all
from helper_functions.prompt import append_instructions, get_instructions
from web_detect import run_prompt
import json
from helper_functions.api import test_gemini_key
from helper_functions.security import check_filename_for_traversal
import threading
import os

SCRIPTS_DIRECTORY = os.path.dirname(os.path.abspath(__file__))
PARENT_DIRECTORY = os.path.dirname(SCRIPTS_DIRECTORY)
DATASETS_DIRECTORY = os.path.join(PARENT_DIRECTORY, 'dynamic', 'datasets')

challenge_routes = Blueprint('challenge_routes', __name__, template_folder='challenge')

@challenge_routes.route('/')
def home():
    # TODO: Render the home page with all challenges listed
    return render_template("challenge/list_challenges.html")

@challenge_routes.route('/<challenge_id>')
def challenge_page(challenge_id):
    # Check if user is in challenge, and get challenge details
    query = """SELECT name, description FROM challenge_participants
    LEFT JOIN challenges ON challenge_participants.challenge_id = challenges.id
    WHERE challenge_participants.challenge_id = %s AND user_id = %s;"""
    status, message, result = sql_results_one(query, (challenge_id, session["user_id"],))
    if not status:
        flash(f"Error occurred while checking if user is in challenge: {message}", "error")
        return redirect(url_for('index'))
    if not result:
        flash("You are not part of this challenge", "error")
        return redirect(url_for('index'))
    comp_name = result[0]
    description = result[1]

    # Get announcements for the challenge
    query = """SELECT announcement, announce_time FROM challenge_announcements WHERE challenge_id = %s ORDER BY announce_time DESC;"""
    status, message, result = sql_results_all(query, (challenge_id,))
    if not status:
        flash(f"Error occurred while getting challenge announcements: {message}", "error")
        return redirect(url_for('index'))
    if not result:
        announcements = None
    else:
        announcements = [{"announcement": row[0], "announce_time": str(row[1])[:-3]} for row in result]
    
    return render_template("challenge/challenge_page.html", comp_name=comp_name, description=description, announcements=announcements, challenge_id=challenge_id)

@challenge_routes.route('/join/<join_link>')
def welcome(join_link):
    # Get challenge id for the join link
    status, message, challenge_id = sql_results_one("SELECT id FROM challenges WHERE join_link = %s", (join_link,))
    if not status:
        flash(f"Error occurred while joining challenge: {message}", "error")
        return redirect(url_for('index'))
    if not challenge_id:
        flash("Invalid join link", "error")
        return redirect(url_for('index'))
    challenge_id = challenge_id[0]

    # Get the name and description for challenge
    status, message, result = sql_results_one("SELECT name, description FROM challenges WHERE id = %s", (challenge_id,))
    if not status:
        flash(f"Error occurred while joining challenge: {message}", "error")
        return redirect(url_for('index'))
    if not result:
        flash("Invalid challenge", "error")
        return redirect(url_for('index'))
    comp_name = result[0]
    description = result[1]
    register_url = url_for('challenge_routes.register', join_link=join_link)
    
    return render_template("challenge/welcome.html", comp_name=comp_name, description=description, register_url=register_url)

@challenge_routes.route('/register/<join_link>', methods=['GET', 'POST'])
def register(join_link):
    # Get challenge id for the join link
    status, message, challenge_id = sql_results_one("SELECT id FROM challenges WHERE join_link = %s", (join_link,))
    if not status:
        flash(f"Error occurred while joining challenge: {message}", "error")
        return redirect(url_for('index'))
    if not challenge_id:
        flash("Invalid join link", "error")
        return redirect(url_for('index'))
    challenge_id = challenge_id[0]

    if request.method == 'GET':
        # Get the name, rules, and terms of service for challenge
        status, message, result = sql_results_one("SELECT name, rules, terms_service FROM challenges WHERE id = %s", (challenge_id,))
        if not status:
            flash(f"Error occurred while joining challenge: {message}", "error")
            return redirect(url_for('index'))
        if not result:
            flash("Invalid challenge", "error")
            return redirect(url_for('index'))
        comp_name = result[0]
        rules = result[1].split("\n")
        terms_service = result[2].split("\n")
        
        return render_template("challenge/register.html", comp_name=comp_name, rules=rules, terms_service=terms_service)
    
    elif request.method == 'POST':
        # Ensure that the user has agreed to the terms of service
        if 'termsCheck' not in request.form or request.form['termsCheck'] != "on":
            flash("You must agree to the terms of service to register", "error")
            return redirect(url_for('challenge_routes.register', join_link=join_link))
        
        # Check if user is already part of the challenge  
        status, message, result = sql_results_one("SELECT * FROM challenge_participants WHERE challenge_id = %s AND user_id = %s", (challenge_id, session["user_id"],))
        if not status:
            flash(f"Error occurred while joining challenge: {message}", "error")
            return redirect(url_for('index'))
        if result:
            flash("You are already part of this challenge", "error")
            return redirect(url_for('challenge_routes.challenge_page', challenge_id=challenge_id))
        
        status, message = execute_sql("INSERT INTO challenge_participants (challenge_id, user_id) VALUES (%s, %s)", (challenge_id, session["user_id"],))
        if not status:
            flash(f"Error occurred while joining challenge: {message}", "error")
            return redirect(url_for('index'))
        
        flash("Successfully registered for challenge", "success")
        return redirect(url_for('challenge_routes.challenge_page', challenge_id=challenge_id))

@challenge_routes.route('/prompt-editor/<comp_id>', methods=['GET', 'POST'])
def prompt_editor(comp_id):
    # Ensure user has a Gemini key before testing prompts
    if not session.get("gemini_key"):
        flash("Please enter a Gemini key before testing prompts.", 'info')
        return redirect(url_for('account.account_page'))
    
    # Check if user is in challenge, and get challenge details
    query = """SELECT name FROM challenge_participants
    LEFT JOIN challenges ON challenge_participants.challenge_id = challenges.id
    WHERE challenge_participants.challenge_id = %s AND user_id = %s;"""
    status, message, result = sql_results_one(query, (comp_id, session["user_id"],))
    if not status:
        flash(f"Error occurred while checking if user is in challenge: {message}", "error")
        return redirect(url_for('index'))
    if not result:
        flash("You are not part of this challenge", "error")
        return redirect(url_for('index'))
    comp_name = result[0]

    if request.method == 'GET':
        # Load dataset names
        dataset_mapping = load_dataset_mapping()

        # Create a list of tuples containing dataset name and max rows
        datasets = {name: mapping["rows"] for name, mapping in dataset_mapping.items()}
        
        # Get instructions for the prompt
        instructions = "\n" + get_instructions()

        # Render the index page with dataset names
        return render_template('challenge/prompt_editor.html', datasets=datasets, instructions=instructions, comp_name=comp_name, comp_id=comp_id)
    
    elif request.method == 'POST':      
        # Get prompt and email
        prompt = request.form['prompt']
        email = session["email"]
        api_key = session["gemini_key"]

        # Get dataset for the challenge
        status, message, result = sql_results_one("SELECT file_name, num_rows, subject, friendly_name FROM challenge_datasets WHERE challenge_id = %s", (comp_id,))
        if not status:
            flash(f"Error occurred while getting challenge dataset: {message}", "error")
            return redirect(url_for('index'))
        if not result:
            flash("No dataset found for challenge", "error")
            return redirect(url_for('index'))
        
        # Get dataset information
        dataset_filename = result[0]
        num_rows = int(result[1])
        dataset_subject = result[2]
        dataset_name = result[3]

        # Check filename for traversal
        if not check_filename_for_traversal(dataset_filename):
            flash("Invalid dataset filename", "error")
            return redirect(url_for('challenge_routes.prompt_editor', comp_id=comp_id))
        
        # Get dataset file path
        dataset_path = os.path.join(DATASETS_DIRECTORY, str(comp_id), dataset_filename)

        # Check to see if user has another prompt currently running
        status, message, result = sql_results_all("SELECT * FROM running_tasks WHERE user_id = %s AND status = 'RUNNING';", (session["user_id"],))
        if not status:
            flash(f"Error checking for running tasks: {message}", 'error')
            return redirect(url_for('challenge_routes.prompt_editor', comp_id=comp_id))
        if result:
            flash("You already have a prompt running. Please wait for it to finish before submitting another.", 'error')
            return redirect(url_for('challenge_routes.prompt_editor', comp_id=comp_id))
        
        # Test API key before starting
        success, message = test_gemini_key(api_key=api_key)
        if not success:
            flash(f"API Key error: {message}", 'error')
            return redirect(url_for('challenge_routes.prompt_editor', comp_id=comp_id))

        # Get the url for the server
        base_url = request.host_url

        # Get the user_id
        user_id = session["user_id"]

        # Prepare dataset info
        dataset_info = {
            'name': dataset_name,
            'file_path': dataset_path,
            'filename': dataset_filename,
            'subject': dataset_subject,
            'num_rows': num_rows
        }

        # Create a thread and pass the function to it
        thread = threading.Thread(target=run_prompt, args=(api_key,prompt,email,base_url,user_id,dataset_info,num_rows,comp_id,))
        thread.start()
        
        # Save their prompt to the session to be displayed later
        full_prompt = append_instructions(prompt=prompt)
        session['prompt'] = full_prompt

        # Redirect to the confirmation page
        return redirect(url_for('confirmation'))

@challenge_routes.route('/scoreboard/<comp_id>', methods=['GET'])
def get_scoreboard(comp_id):
    # Confirm user is in challenge
    status, message, result = sql_results_one("SELECT * FROM challenge_participants WHERE challenge_id = %s AND user_id = %s", (comp_id, session["user_id"],))
    if not status:
        return jsonify({'error': message}), 500
    if not result:
        return jsonify({'error': 'User is not in challenge'}), 403
    
    # Get the page and per_page parameters
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 10, type=int)
    start = (page - 1) * per_page

    # Get the top scores for the challenge
    status, message, scores = sql_results_all("SELECT full_name, highest_fscore, ranking FROM challenge_scoreboard_fscore WHERE challenge_id = %s ORDER BY highest_fscore DESC LIMIT %s OFFSET %s", (comp_id, per_page, start))
    if not status:
        return jsonify({'error': message}), 500
    
    # Get the total number of scores for the challenge
    status, message, total = sql_results_one("SELECT COUNT(*) FROM challenge_scoreboard_fscore;")
    if not status:
        return jsonify({'error': message}), 500

    # Format user data to be easily passable to the frontend
    formatted_scoreboard = []
    for score in scores:
        formatted_score = {
            'name': score[0],
            'score': score[1],
            'rank': score[2]
        }
        formatted_scoreboard.append(formatted_score)
    
    # Send back the formatted scoreboard
    return jsonify({
        'scoreboard': formatted_scoreboard,
        'total': total,
        'page': page,
        'per_page': per_page
    })

@challenge_routes.route('/registered/', methods=['GET'])
def get_registered_challenges():
    # Get the page and per_page parameters
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 10, type=int)
    start = (page - 1) * per_page

    # Get the registered challenge information for the user
    query = """SELECT challenge_id, name, highest_fscore, ranking, start_date, end_date
    FROM registered_leaderboard_view 
    WHERE user_id = %s ORDER BY highest_fscore DESC LIMIT %s OFFSET %s"""
    status, message, scores = sql_results_all(query, (session["user_id"], per_page, start,))
    if not status:
        return jsonify({'error': message}), 500
    
    # Get the total number of challenges
    status, message, total = sql_results_one("SELECT COUNT(*) FROM registered_leaderboard_view WHERE user_id = %s;", (session["user_id"],))
    if not status:
        return jsonify({'error': message}), 500

    # Format user data to be easily passable to the frontend
    registered_challenges = []
    for score in scores:
        formatted_score = {
            'challenge_id': score[0],
            'name': score[1],
            'score': score[2],
            'rank': score[3],
            'start_date': str(score[4])[:-9],
            'end_date': str(score[5])[:-9] if score[4] else ""
        }
        registered_challenges.append(formatted_score)
    
    # Send back the registered challenges
    return jsonify({
        'challenges': registered_challenges,
        'total': total,
        'page': page,
        'per_page': per_page
    })

@challenge_routes.route('/available/', methods=['GET'])
def get_available_challenges():
    # Get the page and per_page parameters
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 10, type=int)
    start = (page - 1) * per_page

    # Get the available challenge information
    query = """SELECT name, start_date, end_date, join_link
    FROM challenges
    WHERE public_visibility = TRUE
    LIMIT %s OFFSET %s;"""
    status, message, scores = sql_results_all(query, (per_page, start,))
    if not status:
        return jsonify({'error': message}), 500
    
    # Get the total number of challenges
    status, message, total = sql_results_one("SELECT COUNT(*) FROM challenges WHERE public_visibility = TRUE;")
    if not status:
        return jsonify({'error': message}), 500

    # Format user data to be easily passable to the frontend
    available_challenges = []
    for score in scores:
        formatted_score = {
            'name': score[0],
            'start_date': str(score[1])[:-9],
            'end_date': str(score[2])[:-3] if score[2] else "",
            'join_path': score[3]
        }
        available_challenges.append(formatted_score)
    
    # Send back the available challenges
    return jsonify({
        'challenges': available_challenges,
        'total': total,
        'page': page,
        'per_page': per_page
    })

def load_dataset_mapping():
    with open('static/datasets/dataset_mapping.json', 'r') as f:
        return json.load(f)
