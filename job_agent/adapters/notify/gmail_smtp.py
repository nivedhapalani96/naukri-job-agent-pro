import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import List, Optional
from job_agent.models.config import GmailCfg

class GmailSMTPClient:
    """SMTP client for Gmail."""
    
    def __init__(self, cfg: GmailCfg):
        self.cfg = cfg
        self.smtp_server = "smtp.gmail.com"
        self.smtp_port = 587
    
    def send_email(
        self,
        from_email: str,
        to_emails: List[str],
        subject: str,
        html_body: str,
        text_body: Optional[str] = None,
    ):
        """Send an email via Gmail SMTP."""
        if not self.cfg.enabled:
            return
        
        msg = MIMEMultipart("alternative")
        msg["Subject"] = subject
        msg["From"] = from_email
        msg["To"] = ", ".join(to_emails)
        
        if text_body:
            msg.attach(MIMEText(text_body, "plain"))
        msg.attach(MIMEText(html_body, "html"))
        
        with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
            server.starttls()
            server.login(self.cfg.username, self.cfg.gmail_app_password)
            server.send_message(msg)

