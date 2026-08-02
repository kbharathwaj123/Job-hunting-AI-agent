"""
Automated Email OTP Fetcher.

Support both:
1. Browser Tab Inbox Reading (Playwright context via mail.google.com — zero credentials required!)
2. IMAP SSL Inbox Polling (via imap.gmail.com)
"""

import re
import time
import imaplib
import email
from email.header import decode_header
from playwright.sync_api import BrowserContext

IMAP_SERVER = "imap.gmail.com"
IMAP_PORT = 993


def fetch_latest_otp_from_browser(context: BrowserContext, max_wait_seconds: int = 35) -> str:
    """
    Opens a secondary browser tab to mail.google.com within the persistent Playwright browser context,
    checks the latest unread/received email for a 4-8 digit verification code, closes the tab,
    and returns the extracted OTP code string. Zero IMAP setup required!
    """
    if not context:
        return ""
        
    print("  [AUTOMATED OTP 📧] Opening browser Gmail tab to retrieve newly arrived verification code...")
    mail_page = None
    start_time = time.time()

    try:
        mail_page = context.new_page()
        mail_page.set_default_timeout(15000)
        mail_page.goto("https://mail.google.com/mail/u/0/#inbox", timeout=20000)
        time.sleep(3)

        while time.time() - start_time < max_wait_seconds:
            try:
                # Check for top unread email rows in Gmail inbox
                rows = mail_page.locator("tr.zA, tr[role='row'], div.zA").all()
                for row in rows[:5]:
                    text = row.inner_text().lower()
                    if any(kw in text for kw in ["verification", "verify", "otp", "code", "passcode", "confirm", "security"]):
                        # Open the email thread
                        row.click()
                        time.sleep(2)
                        
                        # Extract message body text
                        body_text = mail_page.locator("div[role='main'], div.a3s").inner_text()
                        
                        # Match 4 to 8 digit OTP codes
                        matches = re.findall(r'\b\d{4,8}\b', body_text)
                        if matches:
                            otp_code = str(matches[0]).strip()
                            print(f"  [AUTOMATED OTP ⚡] Successfully retrieved OTP code from Gmail tab: {otp_code}")
                            mail_page.close()
                            return otp_code
            except Exception:
                pass
                
            time.sleep(4)
            # Refresh inbox listing
            try:
                refresh_btn = mail_page.locator("div[act='20'], div[aria-label*='Refresh']")
                if refresh_btn.count() > 0 and refresh_btn.first.is_visible():
                    refresh_btn.first.click()
                else:
                    mail_page.reload()
            except Exception:
                pass
                
    except Exception as e:
        print(f"  [AUTOMATED OTP WARNING] Browser Gmail check: {e}")
        
    if mail_page:
        try:
            mail_page.close()
        except Exception:
            pass
            
    return ""


def fetch_latest_otp(email_address: str, app_password: str = "", max_wait_seconds: int = 40) -> str:
    """
    Polls the email inbox via IMAP SSL for up to max_wait_seconds to find newly arrived OTP codes.
    Returns the extracted 4-8 digit OTP code string, or empty string if not found.
    """
    if not app_password:
        return ""

    print(f"  [AUTOMATED OTP 📧] Checking IMAP inbox for newly arrived verification code...")
    start_time = time.time()
    
    while time.time() - start_time < max_wait_seconds:
        try:
            mail = imaplib.IMAP4_SSL(IMAP_SERVER, IMAP_PORT)
            mail.login(email_address, app_password)
            mail.select("INBOX")

            status, response = mail.search(None, '(UNSEEN)')
            if status == "OK":
                mail_ids = response[0].split()
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
                            
                            if any(kw in full_text.lower() for kw in ["verification", "verify", "otp", "security code", "passcode", "confirm"]):
                                matches = re.findall(r'\b\d{4,8}\b', full_text)
                                if matches:
                                    otp_code = matches[0]
                                    print(f"  [AUTOMATED OTP ⚡] Automatically retrieved OTP code via IMAP: {otp_code}")
                                    mail.logout()
                                    return otp_code
            mail.logout()
        except Exception:
            pass
            
        time.sleep(5)

    return ""
