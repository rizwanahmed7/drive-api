from django.http import JsonResponse
from django.shortcuts import get_object_or_404
from account.models import User  # Import your User model
from utils.cookie import create_login_cookie  # Import your createLoginCookie function

def user_update_check(request, user_id, uuid=None):
    try:
        user = get_object_or_404(User, id=user_id)  # Replace 'id' with your User model's identifier
    except :
        return JsonResponse({'error': 'User not found'}, status=404)

    if user.email_verified:
        # Assuming your 'generateAuthToken' function generates tokens
        access_token, refresh_token = user.generate_auth_token(uuid)
        create_login_cookie(request, access_token, refresh_token)

    stripped_user = {
        '_id': user.id,
        'emailVerified': user.email_verified,
        'email': user.email,
        'botChecked': False,
    }

    return JsonResponse(stripped_user)

# In your Django URLs configuration, map the URL path to the 'user_update_check' view.
# Example URL pattern in Django's urls.py:
# path('api/user/update-check/<int:user_id>/', user_update_check),
