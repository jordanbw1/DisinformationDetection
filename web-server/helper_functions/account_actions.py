# Import the MySQL connector module
import datetime
import secrets
from helper_functions.database import execute_sql, sql_results_one


TOKEN_EXPIRATION_TIME = 3600  # 1 hour expiration

# ------------ RESET PASSWORD FUNCTIONS ------------ #
# Create and insert the password reset token
def create_password_reset_token(user_id):
    # If a token already exists, delete it
    status, message = delete_password_reset_token_for_user(user_id)
    if not status:
        return False, f"Error occurred while deleting password reset token: {message}", None

    # Generate a unique token
    token = secrets.token_urlsafe(20)

    # Insert token into database
    status, message = insert_password_reset_token(user_id, token)
    if not status:
        return False, f"Error occurred while inserting password reset token: {message}", None
    
    # Return token and status
    return status, "Good", token

# Insert a password reset token into the database
def insert_password_reset_token(user_id, token):
    status, message = execute_sql("INSERT INTO password_reset_tokens (user_id, token) VALUES (%s, %s);", (user_id, token))
    return status, message

# Check if a password reset token is valid
def is_valid_password_token(token):
    # Get creation time of token
    status, message, result = sql_results_one("SELECT created_at FROM password_reset_tokens WHERE token = %s;", (token,))
    if not status:
        return False, f"Unknown error occurred while trying to get token creation time: {message}"
    
    # If there is no result, the token is invalid
    if not result:
        return False, "Invalid or expired token"
    
    # Check if the token is expired (you can adjust the expiration time as needed)
    created_at = result[0].replace(tzinfo=datetime.timezone.utc)
    if (datetime.datetime.now(datetime.timezone.utc) - created_at).total_seconds() > TOKEN_EXPIRATION_TIME:
        # Delete the invalid token from the database
        status, message = delete_password_reset_token(token)
        return False, "Invalid or expired token"

    # Return True if the token is valid
    return True, "Valid token"

# Delete a password reset token from the database
def delete_password_reset_token(token):
    status, message = execute_sql("DELETE FROM password_reset_tokens WHERE token = %s;", (token,))
    return status, message

# Delete a password reset token from the database
def delete_password_reset_token_for_user(user_id):
    status, message = execute_sql("DELETE FROM password_reset_tokens WHERE user_id = %s;", (user_id,))
    return status, message

# Check if a user exists in the database and return the user_id
def get_user_from_email(email):
    status, message, result = sql_results_one("SELECT user_id FROM users WHERE email = %s;", (email,))
    # If an error occurred, return False and the error message
    if not status:
        return False, f"Unknown error occurred while trying to get user_id: {message}", None
    # If the user does not exist, return False and a message
    if not result:
        return False, "User not found", None
    # If the user exists, return True and the user_id
    return True, "Good", result[0]

# Check if a user exists in the database and return the user_id
def get_user_from_token(token):
    status, message, result = sql_results_one("SELECT user_id FROM password_reset_tokens WHERE token = %s;", (token,))
    # If an error occurred, return False and the error message
    if not status:
        return False, f"Unknown error occurred while trying to get user_id: {message}", None
    # If the user does not exist, return False and a message
    if not result:
        return False, "User not found", None
    # If the user exists, return True and the user_id
    return True, "Good", result[0]
# ------------ END RESET PASSWORD FUNCTIONS ------------ #

# ------------ DELETE ACCOUNT FUNCTIONS ------------ #
# Create and insert the account delete token
def create_account_removal_token(user_id):
    # If a token already exists, delete it
    status, message = delete_account_removal_token_for_user(user_id)
    if not status:
        return False, f"Error occurred while removing user delete token: {message}", None

    # Generate a unique token
    token = secrets.token_urlsafe(20)

    # Insert token into database
    status, message = insert_account_removal_token(user_id, token)
    if not status:
        return False, f"Error occurred while inserting user delete token: {message}", None
    
    # Return token and status
    return status, "Good", token

# Insert account removal token into the database
def insert_account_removal_token(user_id, token):
    status, message = execute_sql("INSERT INTO account_removal_tokens (user_id, token) VALUES (%s, %s);", (user_id, token))
    return status, message

# Check if a account removal token is valid
def is_valid_account_removal_token(token):
    # Get creation time of token
    status, message, result = sql_results_one("SELECT created_at FROM account_removal_tokens WHERE token = %s;", (token,))
    if not status:
        return False, f"Unknown error occurred while trying to get token creation time: {message}"
    
    # If there is no result, the token is invalid
    if not result:
        return False, "Invalid or expired token"
    
    # Check if the token is expired (you can adjust the expiration time as needed)
    created_at = result[0].replace(tzinfo=datetime.timezone.utc)
    if (datetime.datetime.now(datetime.timezone.utc) - created_at).total_seconds() > TOKEN_EXPIRATION_TIME:
        # Delete the invalid token from the database
        status, message = delete_account_removal_token(token)
        return False, "Invalid or expired token"

    # Return True if the token is valid
    return True, "Valid token"

# Delete account removal token from the database
def delete_account_removal_token(token):
    status, message = execute_sql("DELETE FROM account_removal_tokens WHERE token = %s;", (token,))
    return status, message

# Delete account removal token from the database
def delete_account_removal_token_for_user(user_id):
    status, message = execute_sql("DELETE FROM account_removal_tokens WHERE user_id = %s;", (user_id,))
    return status, message

def validate_user_name(full_name):
    if not full_name or full_name.isspace():
        return False, "Full name cannot be empty"
    if len(full_name) > 255:
        return False, "Full name cannot be longer than 255 characters"
    if not full_name.replace(" ", "").isalnum():
        return False, "Full name can only contain letters, numbers, and spaces"
    return True, "Good"
# ------------ END DELETE ACCOUNT FUNCTIONS ------------ #