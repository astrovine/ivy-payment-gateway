from typing import Optional
from ..utilities.config import settings
from ..utilities.logger import setup_logger

logger = setup_logger(__name__)


class SMSService:
    def __init__(
        self,
        account_sid: Optional[str] = None,
        auth_token: Optional[str] = None,
        from_number: Optional[str] = None
    ):
        self.account_sid = account_sid or getattr(settings, 'TWILIO_ACCOUNT_SID', None)
        self.auth_token = auth_token or getattr(settings, 'TWILIO_AUTH_TOKEN', None)
        self.from_number = from_number or getattr(settings, 'TWILIO_FROM_NUMBER', None)
        self._client = None
    
    def _get_client(self):
        if self._client is None and self.account_sid and self.auth_token:
            try:
                from twilio.rest import Client
                self._client = Client(self.account_sid, self.auth_token)
            except ImportError:
                logger.warning("Twilio not installed - run: pip install twilio")
                return None
        return self._client
    
    def send_sms(self, to_number: str, message: str) -> bool:
        if not all([self.account_sid, self.auth_token, self.from_number]):
            logger.warning(f"SMS not configured - logging instead. To: {to_number}, Message: {message}")
            print(f"[SMS] To: {to_number}\nMessage: {message}")
            return True
        
        client = self._get_client()
        if not client:
            logger.warning(f"Twilio client not available - logging SMS. To: {to_number}")
            print(f"[SMS] To: {to_number}\nMessage: {message}")
            return True
        
        try:
            msg = client.messages.create(
                body=message,
                from_=self.from_number,
                to=to_number
            )
            logger.info(f"SMS sent successfully to {to_number}, SID: {msg.sid}")
            return True
        except Exception as e:
            logger.error(f"Failed to send SMS to {to_number}: {e}")
            return False
    
    def send_otp(self, to_number: str, otp_code: str) -> bool:
        message = f"Your Ivy Payments verification code is: {otp_code}. Valid for 5 minutes."
        return self.send_sms(to_number, message)
    
    def send_2fa_code(self, to_number: str, code: str) -> bool:
        message = f"Your Ivy Payments 2FA code is: {code}. Do not share this code."
        return self.send_sms(to_number, message)
    
    def send_transaction_notification(
        self,
        to_number: str,
        amount: str,
        currency: str,
        transaction_type: str
    ) -> bool:
        message = f"Ivy Payments: {transaction_type} of {amount} {currency} completed."
        return self.send_sms(to_number, message)
    
    def send_login_alert(self, to_number: str, ip_address: str) -> bool:
        message = f"Ivy Payments: New login from {ip_address}. If not you, secure your account."
        return self.send_sms(to_number, message)


sms_service = SMSService()
