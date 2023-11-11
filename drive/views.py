import hashlib
import uuid
from django.http import FileResponse, Http404, JsonResponse, HttpResponse, HttpResponseServerError
from django.shortcuts import get_object_or_404
from django.views import View
from .models import File
import boto3
import json
from django.http import HttpResponse, JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST, require_GET
from utils.validate_video import validate_video_extension
from utils.validate_image import image_checker as validate_image
from .utils import *
from account.models import CustomUser as User
from utils.send_share_email import send_share_email
from services.services import FolderService, UserPersonalService, MongoFileService
from django.http import JsonResponse, HttpResponse
from django.utils import timezone
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
import os as Crypto
from core.permissions import jwt_login_required
import boto3
from botocore.exceptions import NoCredentialsError
from django.conf import settings
from django.http import JsonResponse
from rest_framework.decorators import api_view
from rest_framework import status
from drive.models import File, Folder
from django.utils.timezone import now
from services.chunk_services import ChunkServices
from datetime import datetime
from .utils import upload_file_to_s3
from django.core import serializers

chunk_services = ChunkServices()
user_service_personal = UserPersonalService()
folder_service = FolderService()
file_service = MongoFileService()


@require_POST
@jwt_login_required
def upload_file(request):
    user = request.user
    form_data = request.POST
    file = request.FILES['file']  # Adjust the field name as needed
    filename = file.name
    parent = None if form_data.get(
        "parent", None) == "/" else form_data.get("parent", None)
    parent_list = form_data.get("parentList") or "/"
    personal_file = form_data.get("personal-file") is not None
    has_thumbnail = False
    is_video = validate_video_extension(file)
    system_file_name = uuid.uuid4().hex
    image_check = validate_image(filename)
    s3_id = f"{system_file_name}-{filename}"
    date = datetime.now()
    current_file = File(
        length=file.size,
        filename=filename,
        upload_date=date,
        link_type="public",
        owner_id=request.user.id,
        parent_list=parent_list,
        has_thumbnail=has_thumbnail,
        is_video=is_video,
        is_image=image_check,
        s3_id=s3_id,
        size=file.size
    )
    if parent:
        current_file.parent = Folder.objects.get(id=parent)
    current_file.save()
    upload_file_to_s3(file, s3_id, user)
    add_to_storage_size(user, file.size, personal_file)
    url = generate_s3_presigned_url(user, current_file.s3_id)
    data = json.loads(serializers.serialize('json', [current_file]))
    return JsonResponse(data={"success": "File Uploaded", "url": url, "data": data})


@require_GET
@jwt_login_required
def get_list(request):
    user = request.user
    try:
        query = request.GET
        file_list = file_service.get_list(user, query)
        return JsonResponse(data=file_list, safe=False)

    except Exception as e:
        print(f"Get File List Error File Route: {str(e)}")
        return HttpResponse(status=500)


@require_POST
@jwt_login_required
def delete_file(request):
    try:
        user = request.user
        file_id = request.POST.get('id')
        file_service.delete_file(user, file_id)
        return JsonResponse(data={"success": f"File with id {file_id} deleted"})

    except Exception as e:
        print(f"Delete File Error File Route: {e}")
        code = e.code if hasattr(e, 'code') else 500
        return HttpResponse(status=code)


@require_GET
def get_public_download(request, tempToken):
    # try:
    url = file_service.get_public_download(tempToken)
    return JsonResponse({"url": url})
    # except Exception as e:
    print(f"Get Public Download Error File Route: {str(e)}")
    return HttpResponse(status=500)


def remove_temp_token(request, temp_token, uuid):
    user = request.user
    if not user:
        return JsonResponse({}, status=400)

    try:
        file_service.remove_temp_token(user, temp_token, uuid)
        return JsonResponse({}, status=200)
    except Exception as e:
        print(f"Remove Temp Token Error File Route: {str(e)}")
        return JsonResponse({}, status=500)


@require_GET
@jwt_login_required
def remove_link(request, id):
    user = request.user
    try:
        file_service.remove_link(user.id, id)
        return JsonResponse(status=200, data={"success": "link was removed"})
    except Exception as e:
        print(f"Remove Public Link Error File Route: {str(e)}")
        return HttpResponse(status=500)


@require_GET
@jwt_login_required
def make_public(request, id):
    user = request.user
    try:
        user_id = user.id
        token = file_service.make_public(user_id, id)
        return JsonResponse({"token": token})

    except Exception as e:
        print(f"Make Public Error File Route: {str(e)}")
        return HttpResponse(status=500)


@require_GET
def get_public_info(request, tempToken):
    try:
        file = file_service.get_public_info(tempToken)
        return JsonResponse(file, safe=False)
    except Exception as e:
        print(f"Get Public Info Error File Route: {str(e)}")
        return HttpResponse(status=500)


@require_GET
@jwt_login_required
def make_one_time_public(request, id):
    user = request.user
    try:
        token = file_service.make_one_time_public(user.id, id)
        return JsonResponse({"token": token})

    except Exception as e:
        print(f"Make One Time Public Link Error File Route: {str(e)}")
        return HttpResponse(status=500)


@require_GET
@jwt_login_required
def get_file_info(request, id):
    user = request.user
    try:
        user_id = user.id
        file = file_service.get_file_info(user_id, id)
        return JsonResponse(file)

    except Exception as e:
        print(f"Get File Info Error File Route: {str(e)}")
        return HttpResponse(status=500)


@require_GET
@jwt_login_required
def get_quick_list(request):
    user = request.user
    try:
        quick_list = file_service.get_quick_list(user)
        return JsonResponse(quick_list, safe=False)
    except Exception as e:
        print(f"Get Quick List Error File Route: {str(e)}")
        return HttpResponse(status=500)


@require_GET
@jwt_login_required
def get_download_token(request):
    user = request.user
    if not user:
        return HttpResponse(status=400)

    try:
        temp_token = file_service.get_download_token(user)

        return JsonResponse({"tempToken": temp_token})

    except Exception as e:
        print(f"Get Download Token Error File Route: {str(e)}")
        return HttpResponse(status=500)


@require_GET
@jwt_login_required
def get_suggested_list(request):
    try:
        user_id = request.user.id
        search_query = request.GET.get('search', '')
        response_data = file_service.get_suggested_list(user_id, search_query)
        return JsonResponse(response_data)

    except Exception as e:
        print(f"Get Suggested List Error File Route: {e}")
        code = e.code if hasattr(e, 'code') else 500
        return HttpResponse(status=code)


def list_all_s3_keys(bucket_name):
    s3 = boto3.client('s3')

    keys = []
    paginator = s3.get_paginator('list_objects_v2')
    for result in paginator.paginate(Bucket=bucket_name):
        for content in result.get('Contents', []):
            keys.append(content['Key'])

    return keys


@require_GET
@jwt_login_required
def download_file(request, id):
    try:
        user = request.user
        url = file_service.download_file(user, id)
        # Assuming download_file handles the response directly
        return JsonResponse({"url": url})

    except Exception as e:
        print(f"Download File Error File Route: {e}")
        code = e.code if hasattr(e, 'code') else 500
        return HttpResponse(status=code)


@require_POST
@jwt_login_required
def rename_file(request):
    try:
        file_id = request.POST.get('id')
        title = request.POST.get('title')
        user_id = request.user.id
        file = file_service.rename_file(user_id, file_id, title)

        return JsonResponse({"success": f"File with id {id} renamed to {title}", "file": file})

    except Exception as e:
        print(f"Rename File Error File Route: {e}")
        code = e.code if hasattr(e, 'code') else 500
        return HttpResponse(status=code)


@require_POST
@jwt_login_required
def send_email_share(request):

    try:
        user = request.user
        file_id = request.POST['id']
        recipient = request.POST['resp']
        file = file_service.get_file_info(user.id, file_id)

        send_share_email(file, recipient)
        return HttpResponse()

    except Exception as e:
        print(f"Send Share Email Error File Route: {e}")
        code = e.code if hasattr(e, 'code') else 500
        return HttpResponse(status=code)


@require_POST
@jwt_login_required
def move_file(request):
    try:
        file_id = request.POST["id"]
        parent_id = None if request.POST['parent'] == "/" else request.POST['parent']
        user_id = request.user.id

        file_service.move_file(user_id, file_id, parent_id)
        return HttpResponse()

    except Exception as e:
        print(f"Move File Error File Route: {e}")
        code = e.code if hasattr(e, 'code') else 500
        return HttpResponse(status=code)


@require_POST
@jwt_login_required
def upload_folder(request):
    try:
        data = request.POST
        folder = Folder.objects.create(
            owner_id=request.user.id,
            personal_folder=data.get('personal', False),
            name=data['name'],
            parent=None if data.get(
                'parent') == "/" else Folder.objects.get(id=data.get('parent')),
            parent_list=data.get('parent_list', "/")
        )
        folder.save()
        from django.core import serializers
        import json
        folder = json.loads(serializers.serialize('json', [folder]))
        return JsonResponse({"data": folder})
    except Exception as e:
        print(e)
        return JsonResponse({"error": str(e)})


@require_POST
@jwt_login_required
def delete_folder(request):
    try:
        user_id = request.user.id
        folder_id = request.POST['id']
        files = File.objects.filter(owner_id=user_id, parent_id=folder_id)
        for file in files:
            delete_s3_object(request.user, file.s3_id)
        folder = Folder.objects.filter(owner_id=user_id, id=folder_id).get()
        folder.delete()
        return JsonResponse({"sucess": f"Folder with id {folder_id} was deleted"})
    except Exception as e:
        print(f"Delete Folder Error Folder Route: {e}")
        code = e.code if hasattr(e, 'code') else 500
        return JsonResponse(status=code, data={"error": str(e)})


@require_GET
@jwt_login_required
def get_subfolder_full_list(request):
    try:
        user = request.user
        folder_id = request.GET['id']
        subfolder_list = folder_service.get_subfolder_full_list(
            user, folder_id)
        print(subfolder_list)
        return JsonResponse(subfolder_list, safe=False)

    except Exception as e:
        print(f"Get Subfolder List Error Folder Route: {e}")
        code = e.code if hasattr(e, 'code') else 500
        return JsonResponse(status=code, data={"error": str(e)})


@require_GET
@jwt_login_required
def delete_all(request):
    if not request.user:
        return HttpResponse(status=401)

    try:
        user = request.user
        folder_service.delete_all(user)
        return JsonResponse({"success": "All Folders are deleted"})

    except Exception as e:
        print(f"Delete All Error Folder Route: {e}")
        code = e.code if hasattr(e, 'code') else 500
        return HttpResponse(status=code)


@require_GET
@jwt_login_required
def get_info(request, id):
    try:
        user_id = request.user.id
        folder = folder_service.get_folder_info(user_id, id)
        folder = json.loads(serializers.serialize('json', [folder]))
        return JsonResponse(data=folder, safe=False)

    except Exception as e:
        print(f"Get Info Error Folder Route: {e}")
        code = e.code if hasattr(e, 'code') else 500
        return JsonResponse(status=code, data={'error': str(e)})


@require_GET
@jwt_login_required
def get_subfolder_list(request):
    if not request.user:
        return HttpResponse(status=401)

    try:
        user_id = request.user.id
        folder_id = request.GET['id']
        data = folder_service.get_folder_sublist(user_id, folder_id)
        return JsonResponse(data)

    except Exception as e:
        print(f"Get Subfolder Error Folder Route: {e}")
        code = e.code if hasattr(e, 'code') else 500
        return HttpResponse(status=code)


@require_GET
@jwt_login_required
def get_folder_list(request):
    try:
        user = request.user
        query = request.GET
        folder_list = folder_service.get_folder_list(user, query)
        folder_list = json.loads(serializers.serialize('json', folder_list))
        return JsonResponse(folder_list, safe=False)

    except Exception as e:
        print(f"Get Folder List Error Folder Route: {e}")
        code = e.code if hasattr(e, 'code') else 500
        return HttpResponse(status=code)


@require_POST
@jwt_login_required
def move_folder(request):
    try:
        user_id = request.user.id
        folder_id = request.POST['id']
        parent = None if request.POST.get(
            'parent', None) == "/" else request.POST.get('parent', None)
        folder_service.move_folder(user_id, folder_id, parent)
        return HttpResponse()

    except Exception as e:
        print(f"Move Folder Error Folder Route: {e}")
        code = e.code if hasattr(e, 'code') else 500
        return HttpResponse(status=code)


@require_POST
@jwt_login_required
def rename_folder(request):
    try:
        user_id = request.user.id
        title = request.POST['title']
        folder_id = request.POST['id']
        folder = folder_service.rename_folder(user_id, folder_id, title)
        return JsonResponse({"success": "Folder renamed", "data": folder})

    except Exception as e:
        print(f"Rename Folder Error Folder Route: {e}")
        code = e.code if hasattr(e, 'code') else 500
        return HttpResponse(status=code)
