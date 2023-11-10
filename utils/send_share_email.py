from django.conf import settings
from django.core.mail import send_mail


def send_share_email(file, recp):
    print(file)
    remote_url = settings.REMOTE_URL
    from_email = settings.EMAIL_FROM_USER
    subject="A File Was Shared With You Through myDrive",
    message=f"Please navigate to the following link to view the file {remote_url}/download-page/{file['currentFile'][0]['pk']}/{file['currentFile'][0]['fields']['link']}",
    send_mail( 
        from_email=from_email,  
        subject=subject,
        message=message[0],
        recipient_list=[recp],
        fail_silently=False
        )