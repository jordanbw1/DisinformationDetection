from flask import Flask, render_template, request
import subprocess
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import os

app = Flask(__name__)

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        prompt = request.form['prompt']
        email = request.form['email']
        
        # Call detect.py script with prompt
        detect_script = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'web_detect.py')
        subprocess.run(['python', detect_script, prompt])
        
        # Send CSV file as attachment via email
        send_email(email)
        
    return render_template('index.html')

def send_email(receiver_email):
    sender_email = "your_sender_email@example.com"
    sender_password = "your_sender_password"
    
    message = MIMEMultipart()
    message['From'] = sender_email
    message['To'] = receiver_email
    message['Subject'] = "Disinformation Detection Results"
    
    filename = "results.csv"
    attachment = open(filename, "rb")
    
    part = MIMEText("Please find the attached CSV file for Disinformation Detection results.")
    message.attach(part)
    
    part = MIMEBase('application', 'octet-stream')
    part.set_payload((attachment).read())
    encoders.encode_base64(part)
    part.add_header('Content-Disposition', "attachment; filename= %s" % filename)
    message.attach(part)
    
    server = smtplib.SMTP('smtp.gmail.com', 587)
    server.starttls()
    server.login(sender_email, sender_password)
    text = message.as_string()
    server.sendmail(sender_email, receiver_email, text)
    server.quit()

if __name__ == '__main__':
    app.run(debug=True)
