import os
from django.conf import settings
from django.core.mail import send_mail


def send_verification_email(user, email_token):
    remote_url = settings.REMOTE_URL
    from_email = settings.EMAIL_FROM_USER
    subject="myDrive Email Verification",
    message=f"Please navigate to the following link to verify your email address: {remote_url}/verify-email/{str(email_token)}",
    send_mail( 
        from_email=from_email,  
        subject=subject,
        message=message[0],
        recipient_list=[user.email],
        fail_silently=False
        )