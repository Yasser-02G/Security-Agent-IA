import smtplib
from email.message import EmailMessage
from app.config import Config

def send_report(attacker_ip, report_text):
    msg = EmailMessage()
    msg.set_content(f"ALERTE INTRUSION\n\nIP Bloquée: {attacker_ip}\n\nAnalyse Gemini:\n{report_text}")
    msg['Subject'] = f"🚨 Attaque bloquée : {attacker_ip}"
    msg['From'] = Config.GMAIL_USER
    msg['To'] = Config.RECIPIENT_EMAIL

    with smtplib.SMTP_SSL('smtp.gmail.com', 465) as smtp:
        smtp.login(Config.GMAIL_USER, Config.GMAIL_APP_PASSWORD)
        smtp.send_message(msg)