from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from helper_functions.database import execute_sql, sql_results_one
from helper_functions.api import test_gemini_key, test_chatgpt_key


account = Blueprint('account', __name__, template_folder='account')

# Account page
@account.route('/', methods=['GET'])
def account_page():
    return render_template('account.html')

# Save the API key provided by the user
@account.route('/update-api-key', methods=['POST'])
def update_api_key():
    if request.method == 'POST':
        # Get the API key type
        api_key_type = request.form.get('api_key_type')
        if not api_key_type:
            flash("API key type is required", "error")
            return redirect(url_for('account.account_page'))
        # Determine api key type
        if api_key_type != 'gemini_key' and api_key_type != 'chatgpt_key':
            flash("Invalid API key type", "error")
            return redirect(url_for('account.account_page'))
        
        # Get the API key
        api_key = request.form.get(api_key_type)
        
        # Call helper function to test the API key before saving, unless it is None.
        if api_key == "None" or api_key == "" or api_key == None:
            helper_delete_query_key(api_key_type)
            session[api_key_type] = None
            flash("API key deleted successfully", "success")
            return redirect(url_for('account.account_page'))

        status, message = helper_test_query_key(api_key_type, api_key)
        if not status:
            flash(f"Error ocurred while testing API key: {message}", "error")
            return redirect(url_for('account.account_page'))

        # Call helper functions to save the API key
        status, message = helper_save_query_key(api_key_type, api_key)
        if not status:
            flash(f"Error ocurred while saving API key: {message}", "error")
            return redirect(url_for('account.account_page'))
        
        session[api_key_type] = api_key
        flash("API key updated successfully", "success")
        return redirect(url_for('account.account_page'))

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

def helper_save_query_key(api_key_type, api_key):
    # Get the table name
    if api_key_type == 'gemini_key':
        select_query = 'SELECT * FROM gemini_keys WHERE `user_id` = %s;'
        update_query = 'UPDATE gemini_keys SET `key` = %s WHERE `user_id` = %s;'
        insert_query = 'INSERT INTO gemini_keys (`user_id`, `key`) VALUES (%s, %s);'
    elif api_key_type == 'chatgpt_key':
        select_query = 'SELECT * FROM chat_gpt_keys WHERE `user_id` = %s;'
        update_query = 'UPDATE chat_gpt_keys SET `key` = %s WHERE `user_id` = %s;'
        insert_query = 'INSERT INTO chat_gpt_keys (`user_id`, `key`) VALUES (%s, %s);'
    else:
        return False, "Invalid API key type"
    
    # Check if key already exists
    status, message, result = sql_results_one(select_query, (session["user_id"],))
    if not status:
        return False, message
    if result:
        # Update the API key
        status, message = execute_sql(update_query, (api_key, session["user_id"],))
        if not status:
            return False, message
        return True, "API key updated successfully"

    # Insert new API key record into correct table
    status, message = execute_sql(insert_query, (session["user_id"], api_key,))
    if not status:
        return False, message
    return True, "API key saved successfully"

def helper_test_query_key(api_key_type, api_key):
    # Test api key by type
    if api_key_type == 'gemini_key':
        status, message = test_gemini_key(api_key)
        return status, message
    elif api_key_type == 'chatgpt_key':
        status, message = test_chatgpt_key(api_key)
        return status, message
    else:
        return False, "Invalid API key type"
    
def helper_delete_query_key(api_key_type):
    # Get the table name
    if api_key_type == 'gemini_key':
        delete_query = 'DELETE FROM gemini_keys WHERE `user_id` = %s;'
    elif api_key_type == 'chatgpt_key':
        delete_query = 'DELETE FROM chat_gpt_keys WHERE `user_id` = %s;'
    else:
        return False, "Invalid API key type"
    
    # Delete the API key
    status, message = execute_sql(delete_query, (session["user_id"],))
    if not status:
        return False, message
    return True, "API key deleted successfully"