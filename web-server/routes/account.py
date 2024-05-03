from flask import Blueprint, render_template, request, redirect, url_for


account = Blueprint('account', __name__, template_folder='account')

# Account page
@account.route('/', methods=['GET'])
def account_page():
    return render_template('account.html')

# TODO: Implement route
@account.route('/delete-account', methods=['GET'])
def delete_account():
    return render_template("delete_account.html")

# TODO: Implement route
@account.route('/delete-account-confirm/<token>', methods=['GET', 'POST'])
def delete_account_confirm(token):
    if request.method == 'POST':
        # Delete the account
        pass
    return render_template("delete_account.html")

# TODO: Implement route
@account.route('/update-api-key', methods=['POST'])
def update_api_key():
    if request.method == 'POST':
        # Update the ChatGPT key
        return redirect(url_for('account.account_page'))