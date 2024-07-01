from flask import Blueprint, render_template, url_for, redirect, jsonify, request, session, flash
from functools import wraps
import json
from helper_functions.database import execute_sql, sql_results_one, sql_results_all, execute_many_sql, execute_sql_return_id, Database
from helper_functions.email_functions import send_generic_email

admin_routes = Blueprint('admin', __name__, template_folder='admin')

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_roles' not in session or 'admin' not in session['user_roles']:
            flash("You need to be an admin to access this page.", 'error')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

@admin_routes.route('/')
@admin_required
def admin_home():
    return redirect(url_for('admin.admin_dashboard'))

@admin_routes.route('/dashboard')
@admin_required
def admin_dashboard():
    return render_template("admin/dashboard.html")

@admin_routes.route('/users', methods=['GET'])
@admin_required
def get_users():
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 10, type=int)
    start = (page - 1) * per_page

    status, message, users = sql_results_all("SELECT user_id, email, roles FROM users_and_roles LIMIT %s OFFSET %s", (per_page, start))
    if not status:
        return jsonify({'error': message}), 500
    
    status, message, total = sql_results_one("SELECT COUNT(*) FROM users;")
    if not status:
        return jsonify({'error': message}), 500

    # Format user data to be easily passable to the frontend
    formatted_users = []
    for user in users:
        roles = user[2].replace(",", ", ") if user[2] else ""
        formatted_user = {
            'user_id': user[0],
            'email': user[1],
            'roles': roles
        }
        formatted_users.append(formatted_user)
    
    return jsonify({
        'users': formatted_users,
        'total': total,
        'page': page,
        'per_page': per_page
    })

@admin_routes.route('/actions', methods=['POST'])
@admin_required
def admin_actions():
    """
    This route is used to add or remove roles from users.
    The request should contain the following parameters:
    - action: add_role or remove_role
    - role: The role to add or remove
    - user_ids: A list of user IDs to add or remove the role from
    """
    def validate_role(role):
        # Ensure the role is in the database
        status, message, result = sql_results_one("SELECT role_id FROM roles WHERE role_name = %s", (role,))
        if not status:
            return 500, message, None
        if not result:
            return 400, 'Role does not exist', None
        return 200, 'Good', result[0]
    
    # Get parameters from the request
    action = request.form.get('action')
    role = request.form.get('role')
    user_ids = request.form.getlist('user_ids')
    # Check if all required parameters are present
    if not action or not role or not user_ids:
        return jsonify({'error': 'Missing required parameters'}), 400
    
    # Handle adding roles
    if action == 'add_role':
        # Get the role_id and validate the role
        status, message, role_id = validate_role(role)
        if status != 200:
            return jsonify({'error': message}), status

        # --- Check if any users are already assigned the role --- #
        # Convert the list of user_ids to a string of placeholders
        user_id_placeholders = ','.join(['%s'] * len(user_ids))
        # Construct the query string with the placeholders for user_ids
        query = "SELECT user_id FROM user_roles WHERE role_id = %s AND user_id IN ({})".format(user_id_placeholders)
        # Concatenate the role_id and user_ids_list to form the values tuple
        values = (role_id,) + tuple(user_ids)
        # Check if any users are already assigned the role
        status, message, results = sql_results_all(query, values)
        if not status:
            return jsonify({'error': message}), 500
        if results:
            users_list = ", ".join([str(result[0]) for result in results])
            return jsonify({'error': 'The following users already have this role: {}'.format(users_list)}), 400
        # --- End check if any users are already assigned the role --- #

        # If the role was organizer, start initial setup and send email
        if role == 'organizer':
            success_list = []
            fail_list = []
            for user_id in user_ids:
                status, message = add_organizer(user_id)
                if status:
                    success_list.append(user_id)
                else:
                    fail_list.append((user_id, message))
            if fail_list:
                if success_list:
                    success_message = "Successfully added the organizer role to users: {}. ".format(success_list)
                else:
                    success_message = ""
                fail_message = ", ".join(["User {}: {}".format(user_id, message) for user_id, message in fail_list])
                return_message = "{}Failed to add the organizer role to users with error messages: {}".format(success_message, fail_message)
                return jsonify({'error': return_message}), 500

        # Add the role to the users
        user_role_values = [(int(user_id), role_id) for user_id in user_ids]
        status, message = execute_many_sql("INSERT INTO user_roles (user_id, role_id) VALUES (%s, %s)", user_role_values)
        if not status:
            return jsonify({'error': message}), 500
        
        # Return success
        return_message = "Added the {} role from selected users.".format(role)
        return jsonify(success=True, message=return_message), 200

    # Handle removing roles
    elif action == 'remove_role':
        # Get the role_id and validate the role
        status, message, role_id = validate_role(role)
        if status != 200:
            return jsonify({'error': message}), status

        # Prepare a SQL statement to remove the role from the users
        values_placeholder = " OR ".join(["(user_id = %s AND role_id = %s)"] * len(user_ids))
        values = []
        for user_id in user_ids:
            values.extend([user_id, role_id])
        query = f"DELETE FROM user_roles WHERE {values_placeholder}"

        # Remove the role from the users
        status, message = execute_sql(query, tuple(values))
        if not status:
            return jsonify({'error': message}), 500
        
        # Return success
        return_message = "Removed the {} role from selected users.".format(role)
        return jsonify(success=True, message=return_message), 200

    # Invalid action
    else:
        return jsonify({'error': 'Invalid action'}), 400
    
    # Return success
    return jsonify(success=True), 200


# --- Helper functions --- #
def add_organizer(user_id):
    with Database() as db:
        # Validate user_id
        status, message, result = db.execute_fetchone("SELECT user_id FROM users WHERE user_id = %s", (user_id,))
        if not status:
            db.rollback()
            return False, message
        if not result:
            db.rollback()
            return False, "User not found"
        
        # Get user email
        status, message, receiver_email = db.execute_fetchone("SELECT email FROM users WHERE user_id = %s", (user_id,))
        if not status:
            db.rollback()
            return False, message
        if not receiver_email:
            db.rollback()
            return False, "User email not found"
        receiver_email = receiver_email[0]

        # Send email to organizer
        base_url = request.host_url
        subject = "You have now been added as an organizer. Let's get started!"
        body = "Hello! You have been added as an organizer. You can now start creating challenges. " \
                "Please click on the link below to get started: {}/organizer/create".format(base_url)
        status, message = send_generic_email(receiver_email, subject, body)
        if not status:
            db.rollback()
            return False, message
        
        # Commit changes
        db.commit()

        return True, "Good"