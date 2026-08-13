import hashlib
import os
from datetime import datetime
from email_sender import send_email_with_attachment
from config import RECIPIENT_EMAILS, CSV_FILE_PATH

HASH_FILE = "last_hash.txt"


def get_file_hash(file_path):
    """File ka current hash (fingerprint) nikalo."""
    with open(file_path, "rb") as f:
        return hashlib.md5(f.read()).hexdigest()


def get_saved_hash():
    """Pichli baar ka saved hash padho."""
    if os.path.exists(HASH_FILE):
        with open(HASH_FILE, "r") as f:
            return f.read().strip()
    return None


def save_hash(hash_value):
    """Naya hash save karo agli baar compare karne ke liye."""
    with open(HASH_FILE, "w") as f:
        f.write(hash_value)


def check_and_send():
    if not os.path.exists(CSV_FILE_PATH):
        print(f"CSV file not found: {CSV_FILE_PATH}")
        return

    current_hash = get_file_hash(CSV_FILE_PATH)
    old_hash = get_saved_hash()

    if current_hash != old_hash:
        # Data update hua hai
        print("New data detected — sending email with attachment...")
        send_email_with_attachment(
            recipient_emails=RECIPIENT_EMAILS,
            subject=f"Updated Contacts List — {datetime.now().strftime('%d-%m-%Y')}",
            body=(
                "Hi,\n\n"
                "The contacts list has been updated. "
                "Please find the latest contacts.csv attached.\n\n"
                "Best regards,\n"
                "Vedanti Bele"
            ),
            attachment_path=CSV_FILE_PATH,
        )
        save_hash(current_hash)

    else:
        # Koi change nahi hua
        print("No changes detected — sending status email (no attachment)...")
        send_email_with_attachment(
            recipient_emails=RECIPIENT_EMAILS,
            subject=f"No Update Today — {datetime.now().strftime('%d-%m-%Y')}",
            body=(
                "Hi,\n\n"
                "No new updates were found in the contacts list today.\n\n"
                "Best regards,\n"
                "Vedanti Bele"
            ),
            attachment_path=None,
        )


if __name__ == "__main__":
    check_and_send()