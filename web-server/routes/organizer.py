from flask import Blueprint, render_template, url_for, redirect, jsonify, request, session, flash
from functools import wraps
from helper_functions.database import execute_sql, sql_results_one, sql_results_all, execute_many_sql, execute_sql_return_id

def organizer_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        flash_message = "You need to be an organizer to access this page."
        # First check session for user_roles, then check if 'organizer' is in the user_roles list
        if 'user_roles' not in session:
            flash(flash_message, 'error')
            return redirect(url_for('login'))
        if 'organizer' not in session['user_roles']:
            # Check the database to see if the user is an organizer
            status, message, user_roles = sql_results_one("SELECT roles FROM users_and_roles WHERE user_id = %s", (session['user_id'],))
            # If the query fails, return an error
            if not status:
                flash(message, 'error')
                return redirect(url_for('index'))
            # If the user is not an organizer, return an error
            if 'organizer' not in user_roles[0]:
                flash(flash_message, 'error')
                return redirect(url_for('index'))
            # If the user is an organizer, update session to reflect that
            session["user_roles"] = [role[0] for role in user_roles]
        return f(*args, **kwargs)
    return decorated_function

organizer_routes = Blueprint('organizer', __name__, template_folder='organizer')

@organizer_routes.route('/')
@organizer_required
def organizer_home():
    # Get the first competition that the user is an organizer for
    status, message, dashboard_id = get_first_comp(session['user_id'])
    if not status:
        flash(message, 'error')
        return redirect(url_for('index'))
    return redirect(url_for('organizer.organizer_dashboard', dashboard_id=dashboard_id))

@organizer_routes.route('/dashboard')
@organizer_required
def organizer_dashboard_empty():
    # Get the first competition that the user is an organizer for
    status, message, dashboard_id = get_first_comp(session['user_id'])
    if not status:
        flash(message, 'error')
        return redirect(url_for('index'))
    return redirect(url_for('organizer.organizer_dashboard', dashboard_id=dashboard_id))

@organizer_routes.route('/dashboard/<int:dashboard_id>')
@organizer_required
def organizer_dashboard(dashboard_id):    
    # Confirm that the competition_id is valid for this user
    query = "SELECT name, join_link, start_date, end_date, is_setup "\
        "FROM competitions INNER JOIN competition_organizer ON competitions.id = competition_organizer.competition_id "\
        "INNER JOIN competition_configured ON competitions.id = competition_configured.competition_id "\
        "WHERE competitions.id = %s AND competition_organizer.user_id = %s"
    status, message, result = sql_results_one(query, (dashboard_id, session['user_id']))
    if not status:
        flash(message, 'error')
        return redirect(url_for('index'))
    if not result:
        flash("You do not have access to this competition.", 'error')
        return redirect(url_for('index'))
    competition_name, join_link, start_date, end_date, is_setup = result

    # Get list of competitions that the user is an organizer for, excluding the current competition
    query = "SELECT id, name, is_setup FROM competitions INNER JOIN competition_organizer "\
        "ON competitions.id = competition_organizer.competition_id "\
        "INNER JOIN competition_configured ON competitions.id = competition_configured.competition_id "\
        "WHERE user_id = %s AND competitions.id != %s"
    status, message, competitions = sql_results_all(query, (session['user_id'], dashboard_id))
    if not status:
        flash(message, 'error')
        return redirect(url_for('index'))
    if competitions:
        competitions = [{"id": competition[0], "name": competition[1], "is_setup": competition[2]} for competition in competitions]
    else:
        competitions = [{"id": dashboard_id, "name": competition_name, "is_setup": is_setup}]

    # Prepare the competition information for the dashboard
    unfinished_competitions = [{"id": competition["id"], "name": "Unnamed Competition", "is_setup": is_setup} for competition in competitions if not competition["is_setup"]]
    competitions = [competition for competition in competitions if competition["is_setup"]]
    if is_setup:
        current_competition = {"id": dashboard_id, "name": competition_name, "join_link": join_link, "start_date": start_date, "end_date": end_date, "is_setup": is_setup}
    else:
        current_competition = {"id": dashboard_id, "name": "Unnamed Competition", "join_link": "Not yet configured", "start_date": "Not yet configured", "end_date": "Not yet configured", "is_setup": is_setup}

    # Render the dashboard with the competition information
    return render_template("organizer/dashboard.html", current_competition=current_competition, competitions=competitions, unfinished_competitions=unfinished_competitions)

@organizer_routes.route('/setup/<int:competition_id>')
@organizer_required
def setup_competition(competition_id):
    # Confirm that the competition_id is valid for this user
    query = "SELECT name FROM competitions INNER JOIN competition_organizer ON competitions.id = competition_organizer.competition_id "\
        "WHERE competitions.id = %s AND competition_organizer.user_id = %s"
    status, message, result = sql_results_one(query, (competition_id, session['user_id']))
    if not status:
        flash(message, 'error')
        return redirect(url_for('index'))
    if not result:
        flash("You do not have access to this competition.", 'error')
        return redirect(url_for('index'))
    competition_name = result[0]
    
    # Figure out which part of setup organizer is at
    # Check if the basic setup has been done
    query = "SELECT id, name, join_link, start_date, end_date, is_setup FROM competition_configured WHERE competition_id = %s"
    status, message, is_setup = sql_results_one(query, (competition_id,))
    if not status:
        flash(message, 'error')
        return redirect(url_for('index'))
    if is_setup:
        flash("This competition has already been configured.", 'error')
        return redirect(url_for('organizer.organizer_dashboard', dashboard_id=competition_id))
    
    # TODO: Continue implementing the setup_competition route
    flash("This route is not yet implemented.", 'error')
    return redirect(url_for('organizer.organizer_dashboard', dashboard_id=competition_id))


# --- Helper functions --- #
def get_first_comp(user_id):
    # Get the first competition that the user is an organizer for
    query = "SELECT id FROM competitions INNER JOIN competition_organizer "\
        "ON competitions.id = competition_organizer.competition_id "\
        "WHERE user_id = %s LIMIT 1"
    status, message, dashboard_id = sql_results_one(query, (user_id,))
    if not status:
        return False, message, None
    if not dashboard_id:
        return False, "You do not have access to any competitions.", None
    return True, "Good", dashboard_id[0]