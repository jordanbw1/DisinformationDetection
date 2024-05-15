from flask import Blueprint, render_template, url_for, redirect, jsonify, request, session, flash
from functools import wraps
from helper_functions.database import execute_sql, sql_results_one, sql_results_all

admin = Blueprint('admin', __name__, template_folder='admin')

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_roles' not in session or 'admin' not in session['user_roles']:
            flash("You need to be an admin to access this page.", 'error')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

@admin.route('/')
@admin_required
def admin_home():
    return redirect(url_for('admin.admin_dashboard')),

@admin.route('/dashboard')
@admin_required
def admin_dashboard():
    return render_template("admin/dashboard.html")

@admin.route('/users', methods=['GET'])
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