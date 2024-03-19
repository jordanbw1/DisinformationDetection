import math
import smtplib
import os
import sys
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from dotenv import load_dotenv
import re
import random
import string
from helper_functions.database import get_db_connection
import mysql.connector

# Determine the path to the .env file
env_path = os.path.join(os.path.dirname(sys.argv[0]), '..', '.env')

# Load .env variables
load_dotenv(env_path)

def send_email(receiver_email, file_download_link, stats, prompt):
    sender_email = os.environ['EMAIL']
    sender_password = os.environ['EMAIL_PASSWORD']

    message = MIMEMultipart()
    message['From'] = sender_email
    message['To'] = receiver_email
    message['Subject'] = "Disinformation Detection Results"

    # prep body variables
    stats["prompt"] = prompt
    stats["download_link"] = file_download_link
    stats["percent_correct"] = math.floor((stats["num_correct"] / stats["num_rows"]) * 100)
    stats["percent_tPos"] = math.floor((stats["tPos"] / stats["num_rows"]) * 100)
    stats["percent_fPos"] = math.floor((stats["fPos"] / stats["num_rows"]) * 100)
    stats["percent_tNeg"] = math.floor((stats["tNeg"] / stats["num_rows"]) * 100)
    stats["percent_fNeg"] = math.floor((stats["fNeg"] / stats["num_rows"]) * 100)
    
    # Calculate Accuracy
    stats["accuracy"] = round(stats["num_correct"] / stats["num_rows"], 2)

    # Calculate Recall
    if stats["tPos"] + stats["fNeg"] == 0:
        stats["recall"] = 0
    else:
        stats["recall"] = round(stats["tPos"] / (stats["tPos"] + stats["fNeg"]), 2)

    # Calculate Precision
    if stats["tPos"] + stats["fPos"] == 0:
        stats["precision"] = 0
    else:
        stats["precision"] = round(stats["tPos"] / (stats["tPos"] + stats["fPos"]), 2)

    # Calculate F-score
    if stats["precision"] + stats["recall"] == 0:
        stats["fscore"] = 0
    else:
        stats["fscore"] = round(2 * ((stats["precision"] * stats["recall"]) / (stats["precision"] + stats["recall"])), 2)
    
    # write body of email
    body = """Your Disinformation Detection prompt results:

Prompt: {prompt}

Your prompt identified {num_correct}/{num_rows} ({percent_correct}%) posts correctly.

Statistics:

True Positives (AI identifies as disinformation when post is actually disinformation):
    {tPos}/{num_rows} ({percent_tPos}%)

False Positives (AI identifies as disinformation when post is true):
    {fPos}/{num_rows} ({percent_fPos}%)

True Negatives (AI identifies as true when post is actually true):
    {tNeg}/{num_rows} ({percent_tNeg}%)

False Negatives (AI identifies as true when post is actually disinformation):
    {fNeg}/{num_rows} ({percent_fNeg}%)

Accuracy: {accuracy}
Recall: {recall}
Precision: {precision}
fScore: {fscore}

If you have any questions on the meaning of these statistics you can visit this site: https://blog.nillsf.com/index.php/2020/05/23/
confusion-matrix-accuracy-recall-precision-false-positive-rate-and-f-scores-explained/

Your results csv file can be downloaded from the Disinformation Detection website using the following link: {download_link}
""".format(**stats)
    
    # testing
    print(body)

    message.attach(MIMEText(body, 'plain'))

    try:
        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.starttls()
        server.login(sender_email, sender_password)
        text = message.as_string()
        server.sendmail(sender_email, receiver_email, text)
        print("Email sent successfully!")
    except Exception as e:
        print(f"An error occurred: {e}")
    finally:
        server.quit()


def check_email(email):
    # Regex string for checking email
    # email_regex = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,7}\b'    # pass the regular expression
    email_regex = r"""(?:[a-z0-9!#$%&'*+/=?^_`{|}~-]+(?:\.[a-z0-9!#$%&'*+/=?^_`{|}~-]+)*|"(?:[\x01-\x08\x0b\x0c\x0e-\x1f\x21\x23-\x5b\x5d-\x7f]|\\[\x01-\x09\x0b\x0c\x0e-\x7f])*")@(?:(?:[a-z0-9](?:[a-z0-9-]*[a-z0-9])?\.)+[a-z0-9](?:[a-z0-9-]*[a-z0-9])?|\[(?:(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.){3}(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?|[a-z0-9-]*[a-z0-9]:(?:[\x01-\x08\x0b\x0c\x0e-\x1f\x21-\x5a\x53-\x7f]|\\[\x01-\x09\x0b\x0c\x0e-\x7f])+)\])"""
    # Check if email is valid
    if(re.fullmatch(email_regex, email)):
        return True
    else:
        return False
    

def send_verification_email(receiver_email):
    if not check_email(receiver_email):
        return False, "Bad email address"
    
    if not(receiver_email.endswith(".byu.edu") or receiver_email.endswith("@byu.edu")):
        return False, "Not a BYU email address"

    # Get the verification code
    verification_code, error_message = generate_verification_code(receiver_email)
    if not verification_code:
        return False, error_message

    sender_email = os.environ['EMAIL']
    sender_password = os.environ['EMAIL_PASSWORD']

    message = MIMEMultipart()
    message['From'] = sender_email
    message['To'] = receiver_email
    message['Subject'] = "Verify Your Email - Disinformation Detection"
    body = f"""
    Your verification code for Disinformation Detection is: {verification_code}
    """
    message.attach(MIMEText(body, 'plain'))

    try:
        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.starttls()
        server.login(sender_email, sender_password)
        text = message.as_string()
        server.sendmail(sender_email, receiver_email, text)
        return True, "Email sent"
    except Exception as e:
        print(f"An error occurred: {e}")
        return False, f"An error occurred: {e}"
    finally:
        server.quit()

# Function to generate a random verification code
def generate_verification_code(receiver_email):
    # Generate code
    verification_code = ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))
    # Insert into database
    try:
        # Make connection
        conn = get_db_connection()
        cursor = conn.cursor()
        # Query the database
        sql = "INSERT INTO verify_code (user_id, code) VALUES ((SELECT user_id FROM users WHERE email = %s), %s);"
        val = (receiver_email, verification_code)
        cursor.execute(sql, val)
        conn.commit()
        cursor.close()
        conn.close()
        return verification_code, "Good"
    except Exception as e:
        print(f"An error occurred: {e}")
        return False, f"An error occurred: {e}"
    finally:
        conn.close()
        
    

def get_verification_code_from_db(receiver_email):
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        sql = """SELECT code FROM verify_code
                JOIN users
                WHERE email = %s;"""
        val = (receiver_email,)
        cursor.execute(sql, val)
        code = cursor.fetchone()[0]
        cursor.close()

        return code, "Good"
    except Exception as e:
        print(f"An error occurred: {e}")
        return False, f"An error occurred: {e}"
    finally:
        conn.close()


def resend_verification_email(receiver_email):
    if not check_email(receiver_email):
        return False, "Bad email address"
    
    verification_code, error_message = get_verification_code_from_db(receiver_email)
    if not verification_code:
        return False, error_message

    sender_email = os.environ['EMAIL']
    sender_password = os.environ['EMAIL_PASSWORD']

    message = MIMEMultipart()
    message['From'] = sender_email
    message['To'] = receiver_email
    message['Subject'] = "Verify Your Email - Disinformation Detection"
    body = f"""
    Your verification code for Disinformation Detection is: {verification_code}
    """
    message.attach(MIMEText(body, 'plain'))

    try:
        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.starttls()
        server.login(sender_email, sender_password)
        text = message.as_string()
        server.sendmail(sender_email, receiver_email, text)
        return True, "Email sent"
    except Exception as e:
        print(f"An error occurred: {e}")
        return False, f"An error occurred: {e}"
    finally:
        server.quit()


def validate_password(password):
    # Check password length
    if len(password) < 8:
        return False, "Password must be at least 8 characters long."

    # Check for uppercase, lowercase, and number
    if not re.search(r"^(?=.*\d)(?=.*[a-z])(?=.*[A-Z]).{8,}$", password):
        return False, "Password must contain at least one uppercase letter, one lowercase letter, and one number."

    return True, "Password is valid."
