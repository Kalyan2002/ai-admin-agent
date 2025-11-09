from tools.email_tool import EmailTool
from dotenv import load_dotenv
import os

load_dotenv()

print("📨 Testing Email Sending...")

email_tool = EmailTool(
    sender=os.getenv("EMAIL_SENDER"),
    password=os.getenv("EMAIL_PASSWORD"),
    receiver=os.getenv("EMAIL_RECEIVER"),
    smtp_server=os.getenv("SMTP_SERVER", "smtp.gmail.com"),
    smtp_port=int(os.getenv("SMTP_PORT", 587))
)

subject = "🚨 AI Admin Agent Test Email"
body = (
    "This is a test alert from AI Admin Agent.\n\n"
    "✅ If you received this email, your alert system is configured correctly."
)

result = email_tool.send_email(subject, body)
print(result)
