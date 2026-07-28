"""
Automated Email OTP Fetcher.

Connects to Gmail / IMAP inbox to automatically extract 6-digit verification codes
sent by company career portals (Workday, Greenhouse, Taleo, ICIMS, etc.) so the agent
can complete account signups with zero human intervention.
"""

import re
import time
import imaplib
import email
from email.header import decode_header

IMAP_SERVER = "imap.gmail.com"
IMAP_PORT = 993

def fetch_latest_otp(email_address: str, app_password: str = "", max_wait_seconds: int = 40) -> str:
    """
    Polls the email inbox for up to max_wait_seconds to find newly arrived OTP verification codes.
    Returns the extracted 4-8 digit OTP code string, or empty string if not found.
    """
    if not app_password:
        return ""

    print(f"  [AUTOMATED OTP 📧] Checking inbox for newly arrived verification code...")
    start_time = time.time()
    
    while time.time() - start_time < max_wait_seconds:
        try:
            mail = imaplib.IMAP4_SSL(IMAP_SERVER, IMAP_PORT)
            mail.login(email_address, app_password)
            mail.select("INBOX")

            # Search recent unread messages
            status, response = mail.search(None, '(UNSEEN)')
            if status == "OK":
                mail_ids = response[0].split()
                # Check most recent 5 emails
                for m_id in reversed(mail_ids[-5:]):
                    res, msg_data = mail.fetch(m_id, "(RFC822)")
                    if res != "OK":
                        continue
                    for response_part in msg_data:
                        if isinstance(response_part, tuple):
                            msg = email.message_from_bytes(response_part[1])
                            subject, encoding = decode_header(msg["Subject"])[0]
                            if isinstance(subject, bytes):
                                subject = subject.decode(encoding or "utf-8", errors="ignore")
                            
                            # Extract email body text
                            body = ""
                            if msg.is_multipart():
                                for part in msg.walk():
                                    content_type = part.get_content_type()
                                    if content_type == "text/plain":
                                        body = part.get_payload(decode=True).decode("utf-8", errors="ignore")
                                        break
                            else:
                                body = msg.get_payload(decode=True).decode("utf-8", errors="ignore")

                            full_text = f"{subject} {body}"
                            
                            # Look for verification keywords
                            if any(kw in full_text.lower() for kw in ["verification", "verify", "otp", "security code", "passcode", "confirm"]):
                                # Match 4 to 8 digit OTP codes
                                matches = re.findall(r'\b\d{4,8}\b', full_text)
                                if matches:
                                    otp_code = matches[0]
                                    print(f"  [AUTOMATED OTP ⚡] Automatically retrieved OTP code: {otp_code}")
                                    mail.logout()
                                    return otp_code
            mail.logout()
        except Exception:
            pass
            
        time.sleep(5)  # wait 5 seconds before re-checking inbox

    return ""
