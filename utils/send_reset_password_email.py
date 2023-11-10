import os
from django.conf import settings
from django.core.mail import send_mail


def send_password_reset_email(user, password_reset_token):
    remote_url = settings.REMOTE_URL
    from_email = settings.EMAIL_FROM_USER
    subject="myDrive Password Reset"
    message=f"Please navigate to the following link to reset your password: {remote_url}/reset-password/{password_reset_token}",
    send_mail( 
        from_email=from_email,  
        subject=subject,
        message=message[0],
        recipient_list=[user.email],
        fail_silently=False
        )