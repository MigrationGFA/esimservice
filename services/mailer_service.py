# mailer.py
import os
import ssl
import smtplib
import logging
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from jinja2 import Environment, FileSystemLoader
from config import smtp_server, smtp_port, smtp_user, smtp_password, smtp_sender, smtp_sender_name


# Initialize Jinja2 environment
env = Environment(loader=FileSystemLoader("templates"))


async def send_mail(data):
    logging.info("Starting mailing process")

    sender_name = smtp_sender_name
    sender_email = smtp_sender
    mail_subject = data.get("mail_subject")
    receiver_email = data.get("receiver_email")

    # Load and render the email template
    template = env.get_template("onboarding.html")
    mail_body = template.render(name=data.get("name"))
    print(f"Mail body: {mail_body}")

    # Create a multipart message and set headers
    message = MIMEMultipart()
    message["From"] = f"{sender_name} <{sender_email}>"
    message["To"] = receiver_email
    message["Subject"] = mail_subject

    # Attach the HTML content
    message.attach(MIMEText(mail_body, "html"))
    context = ssl.create_default_context()

    try:
        # Create SMTP session
        with smtplib.SMTP_SSL(smtp_server, smtp_port, context=context) as server:
            server.login(smtp_user, smtp_password)
            # Send the email and capture the response
            response = server.sendmail(sender_email, receiver_email, message.as_string())

            if not response:
                logging.info("Email sent successfully without any errors.")
            else:
                logging.warning(f"Sendmail response: {response}")

    except Exception as e:
        logging.error(f"An error occurred while sending the email: {str(e)}")
