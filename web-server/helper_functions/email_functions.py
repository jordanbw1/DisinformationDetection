from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

def send_email(receiver_email, file_download_link):
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