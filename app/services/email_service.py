
from typing import Optional

from pydantic import EmailStr

from ..utilities.logger import setup_logger

logger = setup_logger(__name__)


class EmailService:
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
            Payment Gateway Team
            """
            logger.info(f"Password reset email would be sent to: {email}")
            logger.info(f"Reset link: {reset_link}")
            logger.debug(f"Email subject: {subject}")
            logger.debug(f"Email body: {body}")


            print("PASSWORD RESET EMAIL")
            print(f"To: {email}")
            print(f"Subject: {subject}")
            print(f"\nReset Link:\n{reset_link}")
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
            Payment Gateway Team
            """

            logger.info(f"Password changed confirmation email would be sent to: {email}")

            print("PASSWORD CHANGED CONFIRMATION")
            print(f"To: {email}")
            print(f"Subject: {subject}")
            print(f"\n{body}")
            return True

        except Exception as e:
            logger.error(f"Failed to send password changed confirmation to {email}: {str(e)}", exc_info=True)
            return False


