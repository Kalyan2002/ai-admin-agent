"""
Path: tools/email_tool.py
Handles email notifications for AI-Admin-Agent incidents.
"""

import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from dotenv import load_dotenv
class EmailTool:
    def __init__(
        self,
        sender: str,
        password: str,
        receiver: str,
        smtp_server: str = "smtp.gmail.com",
        smtp_port: int = 587
    ):
        self.sender = sender
        self.password = password
        self.receiver = receiver
        self.smtp_server = smtp_server
        self.smtp_port = smtp_port

    def send_email(self, subject: str, body: str):
        """Send an email using provided credentials."""
        try:
            msg = MIMEMultipart()
            msg["From"] = self.sender
            msg["To"] = self.receiver
            msg["Subject"] = subject
            msg.attach(MIMEText(body, "plain"))

            print(f"📡 Connecting to SMTP server: {self.smtp_server}:{self.smtp_port}")
            print(f"📧 Sending from {self.sender} → {self.receiver}")

            server = smtplib.SMTP(self.smtp_server, self.smtp_port)
            server.ehlo()
            server.starttls()
            server.ehlo()
            server.login(self.sender, self.password)
            server.send_message(msg)
            server.quit()

            print(f"✅ Email sent successfully to {self.receiver}")
            return {"status": "success", "receiver": self.receiver}

        except smtplib.SMTPAuthenticationError as e:
            print(f"❌ Authentication failed: {e.smtp_error.decode()}")
            return {"status": "error", "error": str(e)}
        except smtplib.SMTPConnectError as e:
            print(f"❌ Connection error: {e}")
            return {"status": "error", "error": str(e)}
        except Exception as e:
            print(f"❌ Unexpected error while sending email: {repr(e)}")
            return {"status": "error", "error": repr(e)}
