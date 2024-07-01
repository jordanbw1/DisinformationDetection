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
    # Get the first challenge that the user is an organizer for
    status, message, dashboard_id = get_first_comp(session['user_id'])
    if not status:
        flash(message, 'error')
        return redirect(url_for('index'))
    return redirect(url_for('organizer.organizer_dashboard', dashboard_id=dashboard_id))

@organizer_routes.route('/dashboard')
@organizer_required
def organizer_dashboard_empty():
    # Get the first challenge that the user is an organizer for
    status, message, dashboard_id = get_first_comp(session['user_id'])
    if not status:
        flash(message, 'error')
        return redirect(url_for('index'))
    # If they don't have any challenges, redirect them to creating a challenge
    if not dashboard_id:
        redirect(url_for('organizer.create'))
    return redirect(url_for('organizer.organizer_dashboard', dashboard_id=dashboard_id))


@organizer_routes.route('/dashboard/<int:dashboard_id>')
@organizer_required
def organizer_dashboard(dashboard_id):    
    # Confirm that the challenge_id is valid for this user
    query = "SELECT name, join_link, start_date, end_date "\
        "FROM challenges INNER JOIN challenge_organizer ON challenges.id = challenge_organizer.challenge_id "\
        "WHERE challenges.id = %s AND challenge_organizer.user_id = %s"
    status, message, result = sql_results_one(query, (dashboard_id, session['user_id']))
    if not status:
        flash(message, 'error')
        return redirect(url_for('index'))
    if not result:
        flash("You do not have access to this challenge.", 'error')
        return redirect(url_for('index'))
    challenge_name, join_link, start_date, end_date = result

    # Get list of challenges that the user is an organizer for, excluding the current challenge
    query = "SELECT id, name FROM challenges INNER JOIN challenge_organizer "\
        "ON challenges.id = challenge_organizer.challenge_id "\
        "WHERE user_id = %s AND challenges.id != %s"
    status, message, challenges = sql_results_all(query, (session['user_id'], dashboard_id))
    if not status:
        flash(message, 'error')
        return redirect(url_for('index'))
    if challenges:
        challenges = [{"id": challenge[0], "name": challenge[1]} for challenge in challenges]
    else:
        challenges = [{"id": dashboard_id, "name": challenge_name}]

    # Get list of draft challenges for the organizer
    query = "SELECT id, name FROM challenge_drafts WHERE user_id = %s"
    status, message, unfinished_challenges = sql_results_all(query, (session['user_id'],))
    if not status:
        flash(message, 'error')
        return redirect(url_for('index'))
    
    # Prepare the list of draft challenges
    unfinished_challenges = [{"id": challenge[0], "name": challenge[1]} for challenge in unfinished_challenges]
    # Replace the name of the draft challenges with "Draft X" if the name is None
    count = 0
    for challenge in unfinished_challenges:
        if challenge["name"] is None:
            count += 1
            challenge["name"] = f"Draft {count}"

    # Prepare the current challenge
    current_challenge = {"id": dashboard_id, "name": challenge_name, "join_link": join_link, "start_date": start_date, "end_date": end_date}

    # Render the dashboard with the challenge information
    return render_template("organizer/dashboard.html", current_challenge=current_challenge, challenges=challenges, unfinished_challenges=unfinished_challenges)

@organizer_routes.route('/setup/<int:draft_id>')
@organizer_required
def setup_challenge(draft_id):
    """Redirect to the first part of the challenge setup process."""
    return redirect(url_for('organizer.setup_challenge_parts', draft_id=draft_id, setup_part=1))

@organizer_routes.route('/setup/<int:draft_id>/<int:setup_part>')
@organizer_required
def setup_challenge_parts(draft_id, setup_part):
    # Confirm that the draft_id is valid for this user
    query = "SELECT name FROM challenge_drafts WHERE id = %s AND user_id = %s"
    status, message, result = sql_results_one(query, (draft_id, session['user_id']))
    if not status:
        flash(message, 'error')
        return redirect(url_for('index'))
    if not result:
        flash("Either challenge does not exist or you do not have access to it.", 'error')
        return redirect(url_for('index'))
    
    # Get relevant values from the query result
    challenge_name = result[0]
    
    # Figure out which part of setup organizer is at
    # TODO: Query the relevant tables for each part of the setup process
    # TODO: Check tables for Landing Page
    # TODO: Check tables for Challenge Info
    # TODO: Check tables for Model & Dataset
    # TODO: Check tables for Evaluation Builder
    # TODO: Check tables for Wrap Up

    # # Check if the basic setup has been done
    # query = "SELECT id, name, join_link, start_date, end_date, is_setup FROM challenge_configured WHERE challenge_id = %s"
    # status, message, is_setup = sql_results_one(query, (challenge_id,))
    # if not status:
    #     flash(message, 'error')
    #     return redirect(url_for('index'))
    # if is_setup:
    #     flash("This challenge has already been configured.", 'error')
    #     return redirect(url_for('organizer.organizer_dashboard', dashboard_id=challenge_id))
    
    # TODO: Continue implementing the setup_challenge route
    flash("This route is not yet implemented.", 'error')
    # return redirect(url_for('organizer.organizer_dashboard', dashboard_id=challenge_id))
    return render_template("organizer/setup.html", draft_id=draft_id, challenge_name=challenge_name, setup_part=setup_part)


@organizer_routes.route('/create')
@organizer_required
def create():
    # Create a draft challenge
    query = "INSERT INTO challenge_drafts (user_id) VALUES (%s);"
    status, message, result = execute_sql_return_id(query, (session['user_id'],))
    if not status:
        flash(message, 'error')
        return redirect(url_for('index'))
    if not result:
        flash(message, 'error')
        return redirect(url_for('index'))
    draft_id = result
    
    # Redirect to setup page
    return redirect(url_for('organizer.setup_challenge_parts', draft_id=draft_id, setup_part=1))


# --- Helper functions --- #
def get_first_comp(user_id):
    # Get the first challenge that the user is an organizer for
    query = "SELECT id FROM challenges INNER JOIN challenge_organizer "\
        "ON challenges.id = challenge_organizer.challenge_id "\
        "WHERE user_id = %s LIMIT 1"
    status, message, dashboard_id = sql_results_one(query, (user_id,))
    if not status:
        return False, message, None
    if not dashboard_id:
        return False, "You do not have access to any challenges.", None
    return True, "Good", dashboard_id[0]