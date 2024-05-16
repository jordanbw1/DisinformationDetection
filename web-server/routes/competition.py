from flask import Blueprint, render_template, flash, redirect, url_for, request, session
from helper_functions.database import execute_sql, sql_results_one, sql_results_all

competition_routes = Blueprint('competition_routes', __name__, template_folder='competition')

@competition_routes.route('/')
def home():
    # TODO: Render the home page with all competitions listed
    return render_template("competition/home.html")

@competition_routes.route('/<competition_id>')
def competition_page(competition_id):
    # Check if user is in competition, and get competition details
    query = """SELECT name FROM competition_participants
    LEFT JOIN competitions ON competition_participants.competition_id = competitions.id
    WHERE competition_id = %s AND user_id = %s;"""
    status, message, result = sql_results_one(query, (competition_id, session["user_id"],))
    if not status:
        flash(f"Error occurred while checking if user is in competition: {message}", "error")
        return redirect(url_for('index'))
    if not result:
        flash("You are not part of this competition", "error")
        return redirect(url_for('competition_routes.home'))
    
    comp_name = result[0]
    
    # TODO: Render the competition page with correct settings
    return render_template("competition/competition_page.html", comp_name=comp_name)

@competition_routes.route('/join/<join_link>')
def join(join_link):
    # Get competition id for the join link
    status, message, competition_id = sql_results_one("SELECT id FROM competitions WHERE join_link = %s", (join_link,))
    if not status:
        flash(f"Error occurred while joining competition: {message}", "error")
        return redirect(url_for('index'))
    
    if not competition_id:
        flash("Invalid join link", "error")
        return redirect(url_for('index'))
    competition_id = competition_id[0]

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
    
    return redirect(url_for('competition_routes.competition_page', competition_id=competition_id))
