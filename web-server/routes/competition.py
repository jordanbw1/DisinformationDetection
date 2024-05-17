from flask import Blueprint, render_template, flash, redirect, url_for, request, session, jsonify
from helper_functions.database import execute_sql, sql_results_one, sql_results_all
from helper_functions.prompt import append_instructions, get_instructions
from web_detect import run_prompt
import json
from helper_functions.api import test_gemini_key
import threading

competition_routes = Blueprint('competition_routes', __name__, template_folder='competition')

@competition_routes.route('/')
def home():
    # TODO: Render the home page with all competitions listed
    return render_template("competition/list_competitions.html")

@competition_routes.route('/<competition_id>')
def competition_page(competition_id):
    # Check if user is in competition, and get competition details
    query = """SELECT name, description FROM competition_participants
    LEFT JOIN competitions ON competition_participants.competition_id = competitions.id
    LEFT JOIN competition_details ON competition_participants.competition_id = competition_details.competition_id
    WHERE competition_participants.competition_id = %s AND user_id = %s;"""
    status, message, result = sql_results_one(query, (competition_id, session["user_id"],))
    if not status:
        flash(f"Error occurred while checking if user is in competition: {message}", "error")
        return redirect(url_for('index'))
    if not result:
        flash("You are not part of this competition", "error")
        return redirect(url_for('index'))
    comp_name = result[0]
    description = result[1]

    # Get announcements for the competition
    query = """SELECT announcement, announce_time FROM competition_announcements WHERE competition_id = %s ORDER BY announce_time DESC;"""
    status, message, result = sql_results_all(query, (competition_id,))
    if not status:
        flash(f"Error occurred while getting competition announcements: {message}", "error")
        return redirect(url_for('index'))
    if not result:
        announcements = None
    else:
        announcements = [{"announcement": row[0], "announce_time": str(row[1])[:-3]} for row in result]
    
    return render_template("competition/competition_page.html", comp_name=comp_name, description=description, announcements=announcements, competition_id=competition_id)

@competition_routes.route('/join/<join_link>')
def welcome(join_link):
    # Get competition id for the join link
    status, message, competition_id = sql_results_one("SELECT id FROM competitions WHERE join_link = %s", (join_link,))
    if not status:
        flash(f"Error occurred while joining competition: {message}", "error")
        return redirect(url_for('index'))
    if not competition_id:
        flash("Invalid join link", "error")
        return redirect(url_for('index'))
    competition_id = competition_id[0]

    # Get the name and description for competition
    status, message, result = sql_results_one("SELECT name, description FROM competition_details INNER JOIN competitions WHERE competition_id = %s", (competition_id,))
    if not status:
        flash(f"Error occurred while joining competition: {message}", "error")
        return redirect(url_for('index'))
    if not result:
        flash("Invalid competition", "error")
        return redirect(url_for('index'))
    comp_name = result[0]
    description = result[1]
    register_url = url_for('competition_routes.register', join_link=join_link)
    
    return render_template("competition/welcome.html", comp_name=comp_name, description=description, register_url=register_url)

@competition_routes.route('/register/<join_link>', methods=['GET', 'POST'])
def register(join_link):
    # Get competition id for the join link
    status, message, competition_id = sql_results_one("SELECT id FROM competitions WHERE join_link = %s", (join_link,))
    if not status:
        flash(f"Error occurred while joining competition: {message}", "error")
        return redirect(url_for('index'))
    if not competition_id:
        flash("Invalid join link", "error")
        return redirect(url_for('index'))
    competition_id = competition_id[0]

    if request.method == 'GET':
        # Get the name, rules, and terms of service for competition
        status, message, result = sql_results_one("SELECT name, rules, terms_service FROM competition_details INNER JOIN competitions WHERE competition_id = %s", (competition_id,))
        if not status:
            flash(f"Error occurred while joining competition: {message}", "error")
            return redirect(url_for('index'))
        if not result:
            flash("Invalid competition", "error")
            return redirect(url_for('index'))
        comp_name = result[0]
        rules = result[1].split("\n")
        terms_service = result[2].split("\n")
        
        return render_template("competition/register.html", comp_name=comp_name, rules=rules, terms_service=terms_service)
    
    elif request.method == 'POST':
        # Ensure that the user has agreed to the terms of service
        if 'termsCheck' not in request.form or request.form['termsCheck'] != "on":
            flash("You must agree to the terms of service to register", "error")
            return redirect(url_for('competition_routes.register', join_link=join_link))
        
        # Check if user is already part of the competition  
        status, message, result = sql_results_one("SELECT * FROM competition_participants WHERE competition_id = %s AND user_id = %s", (competition_id, session["user_id"],))
        if not status:
            flash(f"Error occurred while joining competition: {message}", "error")
            return redirect(url_for('index'))
        if result:
            flash("You are already part of this competition", "error")
            return redirect(url_for('competition_routes.competition_page', competition_id=competition_id))
        
        status, message = execute_sql("INSERT INTO competition_participants (competition_id, user_id) VALUES (%s, %s)", (competition_id, session["user_id"],))
        if not status:
            flash(f"Error occurred while joining competition: {message}", "error")
            return redirect(url_for('index'))
        
        flash("Successfully registered for competition", "success")
        return redirect(url_for('competition_routes.competition_page', competition_id=competition_id))

@competition_routes.route('/prompt-editor/<comp_id>', methods=['GET', 'POST'])
def prompt_editor(comp_id):
    # Ensure user has a Gemini key before testing prompts
    if not session.get("gemini_key"):
        flash("Please enter a Gemini key before testing prompts.", 'info')
        return redirect(url_for('account.account_page'))
    
    # Check if user is in competition, and get competition details
    query = """SELECT name FROM competition_participants
    LEFT JOIN competitions ON competition_participants.competition_id = competitions.id
    WHERE competition_participants.competition_id = %s AND user_id = %s;"""
    status, message, result = sql_results_one(query, (comp_id, session["user_id"],))
    if not status:
        flash(f"Error occurred while checking if user is in competition: {message}", "error")
        return redirect(url_for('index'))
    if not result:
        flash("You are not part of this competition", "error")
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
        return render_template('competition/prompt_editor.html', datasets=datasets, instructions=instructions, comp_name=comp_name, comp_id=comp_id)
    
    elif request.method == 'POST':      
        # Get prompt and email
        prompt = request.form['prompt']
        email = session["email"]
        api_key = session["gemini_key"]
        dataset_name = "WELFAKE Dataset"

        # Validate dataset name against mapping
        dataset_mapping = load_dataset_mapping()
        if dataset_name not in dataset_mapping:
            flash("Invalid dataset selected.", 'error')
            return redirect(url_for('competition_routes.prompt_editor', comp_id=comp_id))
        
        # Get folder, filename, and num rows for the selected dataset
        dataset_info = dataset_mapping.get(dataset_name)
        if dataset_info is None or 'directory' not in dataset_info:
            flash("Dataset not in allowed list.", 'error')
            return redirect(url_for('competition_routes.prompt_editor', comp_id=comp_id))
        
        dataset_folder, dataset_filename = dataset_info.get('directory', (None, None))
        if dataset_folder is None or dataset_filename is None:
            flash("Invalid dataset information.", 'error')
            return redirect(url_for('competition_routes.prompt_editor', comp_id=comp_id))
        dataset_subject = dataset_info.get('subject', '')
        num_rows = dataset_info.get('rows', 10000)

        # Check to see if user has another prompt currently running
        status, message, result = sql_results_all("SELECT * FROM running_tasks WHERE user_id = %s AND status = 'RUNNING';", (session["user_id"],))
        if not status:
            flash(f"Error checking for running tasks: {message}", 'error')
            return redirect(url_for('competition_routes.prompt_editor', comp_id=comp_id))
        if result:
            flash("You already have a prompt running. Please wait for it to finish before submitting another.", 'error')
            return redirect(url_for('competition_routes.prompt_editor', comp_id=comp_id))
        
        # Test API key before starting
        success, message = test_gemini_key(api_key=api_key)
        if not success:
            flash(f"API Key error: {message}", 'error')
            return redirect(url_for('competition_routes.prompt_editor', comp_id=comp_id))

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
        thread = threading.Thread(target=run_prompt, args=(api_key,prompt,email,base_url,user_id,dataset_info,num_rows,comp_id,))
        thread.start()
        
        # Save their prompt to the session to be displayed later
        full_prompt = append_instructions(prompt=prompt)
        session['prompt'] = full_prompt

        # Redirect to the confirmation page
        return redirect(url_for('confirmation'))

@competition_routes.route('/scoreboard/<comp_id>', methods=['GET'])
def get_scoreboard(comp_id):
    # Confirm user is in competition
    status, message, result = sql_results_one("SELECT * FROM competition_participants WHERE competition_id = %s AND user_id = %s", (comp_id, session["user_id"],))
    if not status:
        return jsonify({'error': message}), 500
    if not result:
        return jsonify({'error': 'User is not in competition'}), 403
    
    # Get the page and per_page parameters
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 10, type=int)
    start = (page - 1) * per_page

    # Get the top scores for the competition
    status, message, scores = sql_results_all("SELECT full_name, highest_fscore, ranking FROM competition_scoreboard_fscore WHERE competition_id = %s ORDER BY highest_fscore DESC LIMIT %s OFFSET %s", (comp_id, per_page, start))
    if not status:
        return jsonify({'error': message}), 500
    
    # Get the total number of scores for the competition
    status, message, total = sql_results_one("SELECT COUNT(*) FROM competition_scoreboard_fscore;")
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

@competition_routes.route('/registered/', methods=['GET'])
def get_registered_competitions():
    # Get the page and per_page parameters
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 10, type=int)
    start = (page - 1) * per_page

    # Get the registered competition information for the user
    query = """SELECT competition_id, name, highest_fscore, ranking, start_date, end_date
    FROM competition_scoreboard_fscore 
    INNER JOIN competitions ON competitions.id = competition_scoreboard_fscore.competition_id
    WHERE user_id = %s ORDER BY highest_fscore DESC LIMIT %s OFFSET %s"""
    status, message, scores = sql_results_all(query, (session["user_id"], per_page, start,))
    if not status:
        return jsonify({'error': message}), 500
    
    # Get the total number of competitions
    status, message, total = sql_results_one("SELECT COUNT(*) FROM competition_scoreboard_fscore INNER JOIN competitions ON competitions.id = competition_scoreboard_fscore.competition_id WHERE user_id = %s;", (session["user_id"],))
    if not status:
        return jsonify({'error': message}), 500

    # Format user data to be easily passable to the frontend
    registered_competitions = []
    for score in scores:
        formatted_score = {
            'competition_id': score[0],
            'name': score[1],
            'score': score[2],
            'rank': score[3],
            'start_date': str(score[4])[:-9],
            'end_date': str(score[5])[:-9] if score[4] else ""
        }
        registered_competitions.append(formatted_score)
    
    # Send back the registered competitions
    return jsonify({
        'competitions': registered_competitions,
        'total': total,
        'page': page,
        'per_page': per_page
    })

@competition_routes.route('/available/', methods=['GET'])
def get_available_competitions():
    # Get the page and per_page parameters
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 10, type=int)
    start = (page - 1) * per_page

    # Get the available competition information
    query = """SELECT name, start_date, end_date, join_link
    FROM competitions
    LEFT JOIN competition_settings ON competitions.id = competition_settings.competition_id
    WHERE public = TRUE
    LIMIT %s OFFSET %s;"""
    status, message, scores = sql_results_all(query, (per_page, start,))
    if not status:
        return jsonify({'error': message}), 500
    
    # Get the total number of competitions
    status, message, total = sql_results_one("SELECT COUNT(*) FROM competitions LEFT JOIN competition_settings ON competitions.id = competition_settings.competition_id WHERE public = TRUE;")
    if not status:
        return jsonify({'error': message}), 500

    # Format user data to be easily passable to the frontend
    available_competitions = []
    for score in scores:
        formatted_score = {
            'name': score[0],
            'start_date': str(score[1])[:-9],
            'end_date': str(score[2])[:-3] if score[2] else "",
            'join_path': score[3]
        }
        available_competitions.append(formatted_score)
    
    # Send back the available competitions
    return jsonify({
        'competitions': available_competitions,
        'total': total,
        'page': page,
        'per_page': per_page
    })

def load_dataset_mapping():
    with open('static/datasets/dataset_mapping.json', 'r') as f:
        return json.load(f)
