import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from decouple import config

EMAIL_ADDRESS = config("EMAIL_ADDRESS")
EMAIL_PASSWORD = config("EMAIL_PASSWORD")


def send_email(recipient, subject, body):
    """
    Sends an email to the specified recipient.

    Args:
        recipient: The email address of the recipient.
        subject: The subject of the email.
        body: The body of the email.
    """
    try:
        msg = MIMEMultipart()
        msg['From'] = EMAIL_ADDRESS
        msg['To'] = recipient
        msg['Subject'] = subject
        msg.attach(MIMEText(body, 'plain'))

        with smtplib.SMTP_SSL('smtp.gmail.com', 465) as smtp:
            smtp.login(EMAIL_ADDRESS, EMAIL_PASSWORD)
            smtp.send_message(msg)

    except Exception as e:
        print(f"Error sending email: {e}")