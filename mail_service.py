import smtplib
import ssl

from config import APP_PASSWORD, EMAIL


def send_mail(recipient_email, subject, body):
    if not EMAIL or not APP_PASSWORD:
        print("Mail error: EMAIL and APP_PASSWORD must be set.")
        return False

    if not recipient_email:
        print("Mail error: recipient email is required.")
        return False

    message = (
        f"From: {EMAIL}\n"
        f"To: {recipient_email}\n"
        f"Subject: {subject}\n\n"
        f"{body}"
    )
    context = ssl.create_default_context()

    try:
        with smtplib.SMTP_SSL("smtp.gmail.com", 465, context=context) as server:
            server.login(EMAIL, APP_PASSWORD)
            server.sendmail(EMAIL, recipient_email, message)
        return True
    except Exception as error:
        print("Mail error:", error)
        return False
