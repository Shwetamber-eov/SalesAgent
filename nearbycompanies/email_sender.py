import os
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders
from config import SENDER_EMAIL, RECIPIENT_EMAILS, APP_PASSWORD, CSV_FILE_PATH


SMTP_SERVER = "smtp.gmail.com"
SMTP_PORT = 587


def send_email_with_attachment(recipient_emails, subject, body, attachment_path=None):
    """CSV attachment ke sath (ya bina attachment ke) email bhejo."""

    if not SENDER_EMAIL or not APP_PASSWORD:
        print("SENDER_EMAIL ya APP_PASSWORD .env file mein missing hai.")
        return

    msg = MIMEMultipart()
    msg["From"] = SENDER_EMAIL
    msg["To"] = ", ".join(recipient_emails)
    msg["Subject"] = subject

    msg.attach(MIMEText(body, "plain"))

    # 👇 Attachment sirf tab attach karo jab path diya gaya ho
    if attachment_path:
        if not os.path.exists(attachment_path):
            print(f"Attachment file nahi mili: {attachment_path}")
            return

        with open(attachment_path, "rb") as f:
            part = MIMEBase("application", "octet-stream")
            part.set_payload(f.read())

        encoders.encode_base64(part)
        filename = os.path.basename(attachment_path)
        part.add_header("Content-Disposition", f"attachment; filename={filename}")
        msg.attach(part)

    try:
        server = smtplib.SMTP(SMTP_SERVER, SMTP_PORT)
        server.starttls()
        server.login(SENDER_EMAIL, APP_PASSWORD)

        server.sendmail(SENDER_EMAIL, recipient_emails, msg.as_string())
        server.quit()

        print(f"Email successfully sent: {', '.join(recipient_emails)}")

    except smtplib.SMTPAuthenticationError:
        print("Authentication failed — App Password check karo.")
    except Exception as e:
        print(f"Email bhejne mein error aaya: {e}")


if __name__ == "__main__":
    send_email_with_attachment(
        recipient_emails=RECIPIENT_EMAILS,
        subject="Nearby Companies — Contact List (Pune Region)",
        body=(
            "Hi,\n\n"
            "Please find attached the latest contact list of nearby companies, "
            "compiled based on our recent search.\n\n"
            "The attached CSV includes company names, key contact persons, "
            "designations, and available contact details.\n\n"
            "Let me know if you need this filtered further by industry or location.\n\n"
            "Best regards,\n"
            "Vedanti Bele"
        ),
        attachment_path=CSV_FILE_PATH,
    )