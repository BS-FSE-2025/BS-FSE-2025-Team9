"""
Custom email backend for handling SSL certificate verification issues.
"""
import smtplib
import ssl
from django.core.mail.backends.smtp import EmailBackend


class CustomEmailBackend(EmailBackend):
    """
    Custom SMTP backend that bypasses SSL certificate verification.
    This is needed for Gmail SMTP due to certificate validation issues.
    """
    
    def open(self):
        """
        Override the open method to use an unverified SSL context.
        """
        if self.connection is not None:
            return False
        
        try:
            # Create an unverified SSL context
            ssl_context = ssl.create_default_context()
            ssl_context.check_hostname = False
            ssl_context.verify_mode = ssl.CERT_NONE
            
            self.connection = smtplib.SMTP(
                self.host,
                self.port,
                timeout=self.timeout,
            )
            
            if self.use_tls:
                self.connection.starttls(context=ssl_context)
            elif self.use_ssl:
                self.connection.starttls()
            
            if self.username and self.password:
                self.connection.login(self.username, self.password)
            
            return True
        except smtplib.SMTPException as err:
            if not self.fail_silently:
                raise
