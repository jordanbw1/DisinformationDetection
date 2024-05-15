from flask import Blueprint, render_template, url_for, redirect

admin = Blueprint('admin', __name__, template_folder='admin')

@admin.route('/')
def admin_home():
    return redirect(url_for('admin.admin_dashboard')),

@admin.route('/dashboard')
def admin_dashboard():
    return render_template("admin/dashboard.html")