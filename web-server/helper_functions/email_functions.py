import math
import smtplib
import os
import sys
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from dotenv import load_dotenv
import re

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
    stats["prompt": prompt]
    stats["download_link": file_download_link]
    stats["percent_correct": math.floor((stats["num_correct"] / stats["num_rows"]) * 100)]
    stats["percent_tPos": math.floor((stats["tPos"] / stats["num_rows"]) * 100)]
    stats["percent_fPos": math.floor((stats["fPos"] / stats["num_rows"]) * 100)]
    stats["percent_tNeg": math.floor((stats["tNeg"] / stats["num_rows"]) * 100)]
    stats["percent_fNeg": math.floor((stats["fNeg"] / stats["num_rows"]) * 100)]
    
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
    email_regex = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,7}\b'    # pass the regular expression
    # Check if email is valid
    if(re.fullmatch(email_regex, email)):
        return True
    else:
        return False