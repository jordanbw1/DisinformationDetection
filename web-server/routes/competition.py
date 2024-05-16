from flask import Blueprint, render_template, flash, redirect, url_for, request, session
from helper_functions.database import execute_sql, sql_results_one, sql_results_all

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
    
    # TODO: Render the competition page with correct settings
    return render_template("competition/competition_page.html", comp_name=comp_name, description=description)

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
