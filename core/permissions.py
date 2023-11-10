from functools import wraps
from django.http import JsonResponse
from rest_framework_simplejwt.tokens import AccessToken, RefreshToken
from django.contrib.auth import get_user_model


User = get_user_model()

def jwt_login_required(view_func):
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        try:
            access_token = request.META.get("HTTP_AUTHORIZATION")
            if not access_token:
                return JsonResponse({"error": "Please login"}, status=501)
            try: 
                access_token = AccessToken(access_token)
                exp = access_token.check_exp()
                if exp:
                    token = request.COOKIES.get("refresh-token")
                    refresh_token = RefreshToken(token)
                    access_token = refresh_token.access_token
            except: 
                    token = request.COOKIES.get("refresh-token")
                    refresh_token = RefreshToken(token)
                    access_token = refresh_token.access_token
            user_id = access_token.payload.get('user_id')
            user = User.objects.get(id=user_id)
            request.user = user  
        except Exception as e:
            print(f"Permission {e}")
            return JsonResponse({"error": str(e)}, status=501)        
        return view_func(request, *args, **kwargs)
    
    return _wrapped_view

import json

class ReadData:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if request.method == 'POST':
            try:
                data = json.loads(request.body.decode('utf-8'))
                request.POST = data
            except Exception as e:
                print(e)
        response = self.get_response(request)
        return response