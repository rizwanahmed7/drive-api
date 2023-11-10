import uuid
from django.http import HttpResponse, JsonResponse
from services.services import UserPersonalService, UserService
from django.contrib.auth import get_user_model
from utils.cookie import create_login_cookie, create_logout_cookie
from django.shortcuts import get_object_or_404
from drive.models import File
from django.views.decorators.http import require_POST, require_GET
from core.permissions import jwt_login_required
from account.models import CustomUser
from rest_framework_simplejwt.tokens import AccessToken, RefreshToken
from drive.utils import add_to_storage_size



user_service = UserService()
User = get_user_model()
user_personal_service = UserPersonalService()

@require_POST
def get_token(request):
    token = request.POST['refresh']
    refresh_token = RefreshToken(token)
    access_token = refresh_token.access_token
    data = {
        "refresh": str(refresh_token),
        "access": str(access_token)
    }
    return JsonResponse(data=data)

@require_GET
@jwt_login_required 
def get_user(request):
    try:
        user = request.user
        user_data = {
            "id": str(user.id),
            "emailVerified": user.email_verified,
            "email": user.email,
        }
        return JsonResponse(user_data)
    except Exception as e:
        print("\nGet User Route Error:", e)
        code = 500
        return JsonResponse(status=code, data={"error":str(e)})

@require_POST 
def login(request):
    try:
        data = request.POST
        user, access_token, refresh_token = user_service.login(data)
        user_data = {
            "user": {
                "id": str(user.id),
                "emailVerified": user.email_verified,
                "email": user.email,
                "activeSubscription":user.active_subscription,
                "access": access_token,
                "refresh": refresh_token
            }
        }
        response = JsonResponse(user_data, status=200)
        response = create_login_cookie(response, access_token, refresh_token)
        response["Access-Control-Allow-Credentials"] = "true"
        return response
    except Exception as e:
        print("\nLogin User Route Error:", e)
        code = 500
        return JsonResponse(status=code, data={"error":f"Login User Route Error: {e}" })


@require_POST
@jwt_login_required
def logout(request):
    try:
        user_service.logout(request)
        response = JsonResponse(data={"success":"user logged out"})
        response = create_logout_cookie(response)
        return response
    except Exception as e:
        print("\nLogout User Route Error:", e)
        code = 500
        response = JsonResponse(status=code, data={"error":str(e)})
        response = create_logout_cookie(response)
        return response 

@require_POST 
def create_user(request):
    try:
        user, access_token, refresh_token = user_service.create(request.POST)
        user_data = {
            "user": {
                "_id": user.id,
                "emailVerified": user.email_verified,
                "email": user.email,
                "name": user.name
            },
        }
        user.generate_encryption_keys()
        user.generate_auth_keys()
        response = JsonResponse(data=user_data, status=201)
        create_login_cookie(response, access_token, refresh_token)

        return response
    except Exception as e:
        print("\nCreate User Route Error:", e)
        code = 500
        return JsonResponse(status=code, data={"error":str(e)})

@require_POST
@jwt_login_required 
def change_password(request):
    try:
        user_id = str(request.user.id)
        old_password = request.POST.get("oldPassword")
        new_password = request.POST.get("newPassword")
        print(user_id)
        access_token, refresh_token = user_service.change_password(user_id, old_password, new_password)

        response = JsonResponse(data={"success": "password updated"})
        create_login_cookie(response, access_token, refresh_token)

        return response
    except Exception as e:
        print("\nChange Password User Route Error:", e)
        code = 500
        return JsonResponse(status=code, data=f"Change Password User Route Error: {e}")


@require_GET
@jwt_login_required 
def refresh_storage_size(request):
    try:
        print(request.user)
        user = User.objects.get(id=request.user.id)

        file_list = File.objects.filter(owner=user.id, personal_file=None)

        size = 0

        for current_file in file_list:
            size += current_file.length

        user.storage_data = {"storageSize": size, "storageLimit": 0}
        user.save()

        return JsonResponse({"sucess":"Storage size updated successfully", "data":user.storage_data})
    except Exception as e:
        print(e)
        code = 500
        return JsonResponse(status=code, data={"error":str(e)})


@require_GET
@jwt_login_required 
def get_user_detailed(request):
    try:
        user_id = str(request.user.id)

        user_detailed = user_service.get_user_detailed(user_id)

        user_data = {
            "_id": str(user_detailed.id),
            "emailVerified": user_detailed.email_verified,
            "email": user_detailed.email,
            "name": user_detailed.name,
            "size": user_detailed.storage_size,
        }
        return JsonResponse(data=user_data)
    except Exception as e:
        print("\nGet User Detailed User Route Error:", e)
        code = 500
        return JsonResponse(status=code, data={"error":f"Get User Detailed User Route Error: {e}"})


@require_GET
def verify_email(request, token):
    try:
        user_service.verify_email(token)
        response = JsonResponse(data={"success": "email verified"})
        return response
    except Exception as e:
        print("\nVerify Email User Route Error:", e)
        code = 500
        return JsonResponse(status=code, data={"error":str(e)})

@require_POST
def resend_verify_email(request):
    try:
        user_id = str(request.POST['email'])
        user_service.resend_verify_email(user_id)
        return JsonResponse(data={"sucess": "email sent"})
    except Exception as e:
        print("\nResend Email User Route Error:", e)
        code = 500
        return JsonResponse(status=code, data={"error":str(e)})

@require_POST 
def send_password_reset(request):
    try:
        email = request.POST.get('email')
        print(request.POST)
        user_service.send_password_reset(email)

        return JsonResponse({"sucess": "Reset Password email was sent"})
    except Exception as e:
        print("\nSend Password Reset Email User Route Error:", e)
        code = 500
        return JsonResponse(status=code, data={"error":str(e)})

@require_POST 
def reset_password(request):
    try:
        password_token = request.POST.get("passwordToken")
        password = request.POST.get("password")
        if not password_token or not password:
            return JsonResponse({"error": "password or password token not found"})
        user_service.reset_password(password_token, password)

        return JsonResponse(data={"success":"password updated"})
    except Exception as e:
        print("\nReset Password User Route Error:", e)
        code = 500
        return JsonResponse(status=code, data={"error":str(e)})

@require_POST
@jwt_login_required
def add_s3_storage(request):
    try:
        user = request.user
        s3_data = request.POST

        user_personal_service.add_s3_storage(user, s3_data)

        return JsonResponse(data={"success":"S3 added succecfully"})
    except Exception as e:
        print("\nAdd S3 Storage Error Personal User Route:", e)
        code = 500
        return JsonResponse(status=code, data={"error":str(e)})

@require_GET
@jwt_login_required
def remove_s3_storage(request):
    try:
        user = request.user
        user_personal_service.remove_s3_storage(user)
        return JsonResponse(data={"success":"S3 Data removed"})
    except Exception as e:
        print("\nRemove S3 Storage Error Personal User Route:", e)
        code = 500
        return JsonResponse(status=code, data={"error":str(e)})

@require_GET
@jwt_login_required
def remove_s3_metadata(request):
    try:
        user = request.user
        user_personal_service.remove_s3_metadata(user)
        return JsonResponse(data={"success":"S3 Metadata removed"})
    except Exception as e:
        print("\nRemove S3 Metadata Error Personal User Route:", e)
        code = 500
        return JsonResponse(status=code, data={"error":str(e)})


@require_GET
@jwt_login_required
def download_personal_file_list(request):
    try:
        user = request.user
        personal_file_list = user_personal_service.download_personal_file_list(user)
        return JsonResponse(data=personal_file_list)
    except Exception as e:
        print("\nDownload S3 Metadata Error Personal User Route:", e)
        code = 500
        return JsonResponse(status=code, data={"error":str(e)})


@require_POST
@jwt_login_required
def upload_personal_file_list(request):
    try:
        user = request.user
        file_list = request.POST
        user_personal_service.upload_personal_file_list(user, file_list)
        return JsonResponse(data={"success":"Personal Files Uploaded succecfully"})
    except Exception as e:
        print("\nUpload S3 Metadata Error Personal User Route:", e)
        code = 500
        return JsonResponse(status=code, data={"error":str(e)})


@require_POST
@jwt_login_required
def add_name(request):
    user_id = request.user.id
    name = request.POST.get('name')
    if not name or len(name) == 0:
        return HttpResponse("No name", status=403)

    user = get_object_or_404(User, id=user_id)

    user.name = name
    user.save()

    return HttpResponse("Name updated successfully")
