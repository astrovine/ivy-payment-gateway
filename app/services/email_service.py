import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Optional

from pydantic import EmailStr

from ..utilities.config import settings
from ..utilities.logger import setup_logger

logger = setup_logger(__name__)


class EmailService:
    def __init__(
        self,
        smtp_host: str = "smtp.gmail.com",
        smtp_port: int = 587,
        smtp_user: Optional[str] = None,
        smtp_password: Optional[str] = None,
        from_email: str = "noreply@ivypayments.com"
    ):
        self.smtp_host = smtp_host
        self.smtp_port = smtp_port
        self.smtp_user = smtp_user or getattr(settings, 'SMTP_USER', None)
        self.smtp_password = smtp_password or getattr(settings, 'SMTP_PASSWORD', None)
        self.from_email = from_email
    
    def _send_email(
        self,
        to_email: str,
        subject: str,
        body_html: str,
        body_text: Optional[str] = None
    ) -> bool:
        if not self.smtp_user or not self.smtp_password:
            logger.warning(f"Email not configured - logging instead. To: {to_email}, Subject: {subject}")
            print(f"[EMAIL] To: {to_email}\nSubject: {subject}\n{body_text or 'HTML content'}")
            return True
        
        try:
            msg = MIMEMultipart("alternative")
            msg["Subject"] = subject
            msg["From"] = self.from_email
            msg["To"] = to_email
            
            if body_text:
                msg.attach(MIMEText(body_text, "plain"))
            msg.attach(MIMEText(body_html, "html"))
            
            with smtplib.SMTP(self.smtp_host, self.smtp_port) as server:
                server.starttls()
                server.login(self.smtp_user, self.smtp_password)
                server.sendmail(self.from_email, to_email, msg.as_string())
            
            logger.info(f"Email sent successfully to {to_email}: {subject}")
            return True
        
        except Exception as e:
            logger.error(f"Failed to send email to {to_email}: {e}")
            return False
    
    @staticmethod
    def send_password_reset_email(email: str, reset_token: str, user_name: str) -> bool:
        try:
            frontend_url = "http://localhost:5173/"
            reset_link = f"{frontend_url}/reset-password?token={reset_token}"

            subject = "Password Reset Request"
            body = f"""
            Hello {user_name},
            
            You have requested to reset your password. Click the link below to reset your password:
            
            {reset_link}
            
            This link will expire in 15 minutes.
            
            If you did not request this password reset, please ignore this email.
            
            Best regards,
            Ivy Payments Team
            """
            logger.info(f"Password reset email would be sent to: {email}")
            logger.info(f"Reset link: {reset_link}")
            print(f"[PASSWORD RESET] To: {email}\nReset Link: {reset_link}")
            return True

        except Exception as e:
            logger.error(f"Failed to send password reset email to {email}: {str(e)}", exc_info=True)
            return False

    @staticmethod
    def send_password_changed_confirmation(email: str, user_name: str) -> bool:
        try:
            subject = "Password Changed Successfully"
            body = f"""
            Hello {user_name},
            
            Your password has been successfully changed.
            
            If you did not make this change, please contact support immediately.
            
            Best regards,
            Ivy Payments Team
            """
            logger.info(f"Password changed confirmation email would be sent to: {email}")
            print(f"[PASSWORD CHANGED] To: {email}")
            return True

        except Exception as e:
            logger.error(f"Failed to send password changed confirmation to {email}: {str(e)}", exc_info=True)
            return False
    
    def send_verification_email(self, to_email: str, verification_link: str) -> bool:
        subject = "Verify Your Email - Ivy Payments"
        body_html = f"""
        <html>
        <body style="font-family: Arial, sans-serif; line-height: 1.6;">
            <h2>Welcome to Ivy Payments!</h2>
            <p>Please verify your email address by clicking the link below:</p>
            <p><a href="{verification_link}" style="background-color: #4CAF50; color: white; padding: 10px 20px; text-decoration: none; border-radius: 5px;">Verify Email</a></p>
            <p>If you didn't create an account, you can safely ignore this email.</p>
            <p>This link expires in 24 hours.</p>
        </body>
        </html>
        """
        body_text = f"Welcome to Ivy Payments! Verify your email: {verification_link}"
        return self._send_email(to_email, subject, body_html, body_text)
    
    def send_2fa_enabled_notification(self, to_email: str) -> bool:
        subject = "Two-Factor Authentication Enabled - Ivy Payments"
        body_html = """
        <html>
        <body style="font-family: Arial, sans-serif; line-height: 1.6;">
            <h2>Two-Factor Authentication Enabled</h2>
            <p>Two-factor authentication has been enabled on your account.</p>
            <p>If you didn't do this, please contact support immediately.</p>
        </body>
        </html>
        """
        return self._send_email(to_email, subject, body_html, "2FA has been enabled on your account.")
    
    def send_login_alert(self, to_email: str, ip_address: str, user_agent: str) -> bool:
        subject = "New Login Detected - Ivy Payments"
        body_html = f"""
        <html>
        <body style="font-family: Arial, sans-serif; line-height: 1.6;">
            <h2>New Login to Your Account</h2>
            <p>A new login was detected:</p>
            <ul>
                <li>IP Address: {ip_address}</li>
                <li>Device: {user_agent}</li>
            </ul>
            <p>If this wasn't you, please change your password immediately.</p>
        </body>
        </html>
        """
        return self._send_email(to_email, subject, body_html)


email_service = EmailService()
