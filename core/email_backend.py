"""
Custom email backend that bypasses SSL certificate verification issues.
"""
import ssl
import smtplib
from django.core.mail.backends.smtp import EmailBackend


class CustomEmailBackend(EmailBackend):
    """
    Custom SMTP email backend that handles SSL certificate verification issues.
    """
    
    def open(self):
        if self.connection:
            return False
        
        try:
            # Create an unverified SSL context
            context = ssl.create_default_context()
            context.check_hostname = False
            context.verify_mode = ssl.CERT_NONE
            
            self.connection = smtplib.SMTP(self.host, self.port, timeout=self.timeout)
            self.connection.ehlo()
            
            if self.use_tls:
                self.connection.starttls(context=context)
                self.connection.ehlo()
            
            if self.username and self.password:
                self.connection.login(self.username, self.password)
            
            return True
        except (smtplib.SMTPException, OSError) as e:
            if not self.fail_silently:
                raise
            return False
