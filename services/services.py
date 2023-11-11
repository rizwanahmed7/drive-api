import json
import jwt
import datetime
from datetime import datetime
from utils.sort_by_switch_folder import sort_by_switch_folder
from utils.file_utils import DbUtil as FileUtils
from utils.folder_utils import DbUtil as FolderUtils
from drive.models import File, Folder  # Import your Django models
from django.core.exceptions import ObjectDoesNotExist
from utils.sort_by_switch import sort_by_switch
from drive.utils import generate_s3_presigned_url, delete_s3_object
from django.conf import settings
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth import get_user_model
from django.core.exceptions import ObjectDoesNotExist
from utils.send_reset_password_email import send_password_reset_email
from utils.send_verification_email import send_verification_email
import jwt
import boto3
from django.core import serializers
from django.db.models import Q


User = get_user_model()
fileUtils = FileUtils()
folderUtils = FolderUtils()


def calculate_s3_size(access_key, secret_key, bucket_name):
    s3 = boto3.client(
        's3',
        aws_access_key_id=access_key,
        aws_secret_access_key=secret_key
    )
    size = 0

    try:
        response = s3.list_objects(Bucket=bucket_name)
        if 'Contents' in response:
            for obj in response['Contents']:
                if 'Size' in obj:
                    size += obj['Size']
    except Exception as e:
        print(f"An error occurred: {e}")
        return 0

    return size


class UserPersonalService:
    def __init__(self):
        pass

    def add_s3_storage(self, user, s3_data):
        id = s3_data['id']
        key = s3_data['key']
        bucket = s3_data['bucket']
        user.storage_data_personal = calculate_s3_size(id, key, bucket)
        user.personal_storage_canceled_date = None

        user.encrypt_s3_data(id, key, bucket)

        user.save()

        return

    def remove_s3_storage(self, user):
        date = datetime.now()

        user.s3_enabled = None
        user.s3_data = None
        user.storage_data_personal = None
        user.personal_storage_canceled_date = date
        user.save()
        return

    def download_personal_file_list(self, user):
        file_list = File.objects.filter(owner=user.id, personal_file=True)
        folder_list = Folder.objects.filter(
            owner=user.id, personal_folder=True)

        combined_data = {
            'file_list': list(file_list.values()),
            'folder_list': list(folder_list.values()),
        }

        return combined_data

    def upload_personal_file_list(self, user, data):
        personal_file_list = data.get('file_list', [])
        personal_folder_list = data.get('folder_list', [])
        fixed_file_list = []
        fixed_folder_list = []

        for current_obj in personal_file_list:
            current_file = File.objects.get(
                id=current_obj['_id'], owner=user.id)
            current_file.owner = user.id
            current_file.upload_date = datetime.fromtimestamp(
                current_obj['upload_date'])
            current_file.parent = str(current_obj['parent'])
            fixed_file_list.append(current_file)

        for current_obj in personal_folder_list:
            current_folder = Folder.objects.get(
                id=current_obj['_id'], owner=user.id)
            current_folder.owner = user.id
            current_folder.created_at = datetime.fromtimestamp(
                current_obj['created_at'])
            current_folder.updated_at = datetime.fromtimestamp(
                current_obj['updated_at'])
            fixed_folder_list.append(current_folder)

        File.objects.bulk_update(
            fixed_file_list, ['_id', 'upload_date', 'owner', 'parent'])
        Folder.objects.bulk_update(
            fixed_folder_list, ['owner', 'created_at', 'updated_at'])

    def remove_s3_metadata(self, user):
        File.objects.filter(owner=user.id, personal_file=True).delete()
        Folder.objects.filter(owner=user.id, personal_folder=True).delete()


class FolderService:
    def upload_folder(self, data):
        folder = Folder(**data)
        folder.save()
        if not folder:
            raise Exception("Upload Folder Error")
        return folder

    def get_folder_info(self, user_id, folder_id):
        current_folder = folderUtils.get_folder_info(folder_id, user_id)
        return current_folder

    def get_folder_sublist(self, user_id, folder_id):
        folder = folderUtils.get_folder_info(folder_id, user_id)
        subfolder_list = folder.parent_list
        folder_id_list = ["/"]
        folder_name_list = ["Home"]
        for current_sub_folder_id in subfolder_list:
            if current_sub_folder_id == "/":
                folder_id_list.append("/")
                folder_name_list.append("Home")
            else:
                current_folder = folderUtils.get_folder_info(
                    current_sub_folder_id, user_id)
                folder_id_list.append(current_folder._id)
                folder_name_list.append(current_folder.name)
        folder_id_list.append(folder_id)
        folder_name_list.append(folder.name)
        return {
            "folderIDList": folder_id_list,
            "folderNameList": folder_name_list
        }

    def get_folder_list(self, user, query):
        user_id = user.id
        search_query = query.get("search", "")
        parent = None if query.get(
            "parent", None) == "/" else query.get("parent", None)
        item_type = query.get("personal", None)
        sort_by = sort_by_switch_folder(query.get("sortby", "DEFAULT"))
        folder_search = query.get("folder_search")
        if not search_query:
            folder_list = folderUtils.get_folder_list_by_parent(
                user_id, parent, sort_by
            )
            return folder_list
        else:
            search_query = search_query
            folder_list = folderUtils.get_folder_list_by_search(
                user_id, search_query, sort_by, parent, folder_search, item_type
            )
            return folder_list

    def rename_folder(self, user_id, folder_id, title):
        try:
            folder = Folder.objects.get(id=folder_id, owner=user_id)
            folder.name = title
            folder.save()
            folder = json.loads(serializers.serialize('json', [folder]))
            return folder
        except Folder.DoesNotExist:
            return None

    def delete_all(self, user):
        all_folders = Folder.objects.filter(owner_id=user.id)
        folders_ids = all_folders.values('pk')
        s3_ids = File.objects.filter(parent_id__in=folders_ids).values('s3_id')
        for s3_id in s3_ids:
            delete_s3_object(user, s3_id)

    def get_subfolder_full_list(self, user, folder_id):
        user_id = user.id
        folder = folderUtils.get_folder_info(folder_id, user_id)
        sub_folders = self.get_folder_list(user, {"parent": folder_id})
        folder_list = []
        root_id = None
        current_id = folder.parent
        folder_list.append({
            "id": folder.id,
            "parent": current_id.id,
            "name": folder.name,
            "subFolders": json.loads(serializers.serialize('json', sub_folders))
        })
        while True:
            if root_id == current_id:
                break
            current_folder = self.get_folder_info(user_id, current_id.id)
            current_sub_folders = self.get_folder_list(
                user, {"parent": current_id.id})
            folder_list.insert(0, {
                "id": current_folder.id,
                "parent": current_folder.parent.id if current_folder.parent else current_folder.parent,
                "name": current_folder.name,
                "subFolders": json.loads(serializers.serialize('json', current_sub_folders))
            })
            current_id = current_folder.parent
        return folder_list

    def move_folder(self, user_id, folder_id, parent_id):
        parent_list = ["/"]
        if parent_id:
            parent_file = folderUtils.get_folder_info(parent_id, user_id)
            parent_list = parent_file.parent_list.split("/")
            parent_list.append(parent_file.name + "/")
        folder = folderUtils.move_folder(
            folder_id, user_id, parent_id, ''.join(parent_list))
        if not folder:
            raise Exception("Move Folder Not Found")
        folder_children = folderUtils.find_all_folders_by_parent(
            folder_id, user_id)
        for current_folder_child in folder_children:
            current_folder_child_parent_list = current_folder_child.parent_list
            index_of_folder_id = current_folder_child_parent_list.index(
                folder_id)
            current_folder_child_parent_list = current_folder_child_parent_list[
                index_of_folder_id:]
            current_folder_child_parent_list = parent_list + current_folder_child_parent_list
            current_folder_child.parent_list = current_folder_child_parent_list
            current_folder_child.save()
        file_children = fileUtils.get_file_list_by_parent(user_id, folder_id)
        for current_file_child in file_children:
            current_file_child_parent_list = current_file_child.parent_list
            current_file_child_parent_list = current_file_child_parent_list.split(
                ",")
            index_of_folder_id = current_file_child_parent_list.index(
                folder_id)
            current_file_child_parent_list = current_file_child_parent_list[index_of_folder_id:]
            current_file_child_parent_list = parent_list + current_file_child_parent_list
            fileUtils.move_file(current_file_child.id, user_id, current_file_child.parent, ",".join(
                current_file_child_parent_list))


class UserService:

    def login(self, user_data):
        try:
            email = user_data['email']
            password = user_data['password']

            user = User.objects.get(email=email)
            if not user.check_password(password):
                raise Exception("Change Passwords Do Not Match Error")

            refresh = RefreshToken.for_user(user)
            return user, str(refresh.access_token), str(refresh)

        except ObjectDoesNotExist:
            print(user_data['email'])
            raise Exception("Cannot Find User")

    def logout(self, request):
        try:
            print(request.user.auth_token)
        except ObjectDoesNotExist:
            raise Exception("Could Not Find User")

    def create(self, user_data):
        email = user_data['email']
        password = user_data['password']

        user = User(email=email, password=password, email_verified=False)
        user.set_password(password)
        user.save()
        refresh = RefreshToken.for_user(user)
        email_token = jwt.encode(
            {"_id": user.id}, "EMAIL-VER",  algorithm='HS256')

        if not email_token:
            raise Exception("Could Not Create Email Verification Token")

        if not user.email_verified:
            send_verification_email(user, email_token)
        return user, str(refresh.access_token), str(refresh)

    def change_password(self, user_id, old_password, new_password):
        try:
            user = User.objects.get(id=user_id)

            if not user.check_password(old_password):
                raise Exception("Change Passwords Do Not Match Error")

            user.set_password(new_password)
            user.save()
            refresh = RefreshToken.for_user(user)
            return str(refresh.access_token), str(refresh)
        except ObjectDoesNotExist:
            raise Exception("Could Not Find User")

    def get_user_detailed(self, user_id):
        try:
            user = User.objects.get(id=user_id)
            user.refresh_from_db()
            return user
        except ObjectDoesNotExist:
            raise Exception("Cannot find user")

    def verify_email(self, verify_token):
        try:
            decoded = jwt.decode(verify_token, 'EMAIL-VER',
                                 algorithms=['HS256'])
            user_id = decoded['_id']
            user = User.objects.get(id=user_id)
            user.email_verified = True
            user.save()
            return user
        except jwt.ExpiredSignatureError:
            raise Exception('Email Token has expired')
        except jwt.DecodeError:
            raise Exception('Email Token Verification Failed')
        except ObjectDoesNotExist:
            raise Exception("Could Not Find User")

    def resend_verify_email(self, user_id):
        try:
            user = User.objects.get(email=user_id)
            if not user.email_verified:
                email_token = jwt.encode(
                    {"_id": user.id}, "EMAIL-VER",  algorithm='HS256')

                if not email_token:
                    raise Exception(
                        "Could Not Create Email Verification Token")
                send_verification_email(user, email_token)
            else:
                raise Exception("Email Already Authorized")
        except ObjectDoesNotExist:
            raise Exception("Cannot find user")

    def send_password_reset(self, email):
        try:
            user = User.objects.get(email=email)
            password_reset_token = jwt.encode(
                {"_email": email}, "PASSWORD-RESET",  algorithm='HS256')
            if not password_reset_token:
                raise Exception("Could Not Create Password Reset Token")
            send_password_reset_email(user, password_reset_token)
        except ObjectDoesNotExist:
            raise Exception("User Not Found Password Reset Email")

    def reset_password(self, verify_token, new_password):
        try:
            decoded = jwt.decode(
                verify_token, 'PASSWORD-RESET', algorithms=['HS256'])
            user_email = decoded['_email']
            user = User.objects.get(email=user_email)
            user.set_password(new_password)
            user.save()
            return
        except jwt.ExpiredSignatureError:
            raise Exception('Reset Password Token has expired')
        except jwt.DecodeError:
            raise Exception("Reset Password Token Do Not Match")
        except ObjectDoesNotExist:
            raise Exception("Could Not Find User")


class MongoFileService:

    def remove_link(self, user_id, file_id):
        try:
            file = File.objects.get(id=file_id, owner_id=user_id)
            file.link = None
            file.link_type = None
            file.save()
        except File.DoesNotExist:
            raise Exception("Remove Link File Not Found Error")

    def get_quick_list(self, user):
        file_list = File.objects.filter(
            owner_id=user.id).order_by("-upload_date")[:10]
        file_list = json.loads(serializers.serialize('json', file_list))
        return file_list

    def get_public_download(self, temp_token):
        payload = None
        try:
            payload = jwt.decode(temp_token, "MAKE-PUBLIC",
                                 algorithms=['HS256'])
        except:
            payload = jwt.decode(temp_token, "ONE-TIME-PUBLIC",
                                 algorithms=['HS256'])
        user = User.objects.get(id=payload['id'])
        url = generate_s3_presigned_url(user, payload['s3_id'], 3600)
        return url

    def make_public(self, user_id, file_id):
        try:
            file = File.objects.get(id=file_id, owner_id=user_id)
            token = jwt.encode({"id": str(user_id), "file_id": file.id,
                               "s3_id": file.s3_id}, "MAKE-PUBLIC", algorithm='HS256')
            file.link = token
            file.link_type = "public"
            file.save()
            return token
        except File.DoesNotExist:
            raise Exception("Make Public File Not Found Error")

    def get_public_info(self, temp_token):
        try:
            file = File.objects.get(link=temp_token)
            data = json.loads(serializers.serialize('json', [file]))
            if file.link_type == "one":
                file.link_type = None
                file.link = None
                file.save()
            return data
        except File.DoesNotExist:
            raise Exception("Public Info Not Found")

    def make_one_time_public(self, user_id, file_id):
        try:
            file = File.objects.get(id=file_id, owner=user_id)
            token = jwt.encode(
                {"id": str(user_id), "file": file_id, 's3_id': file.s3_id}, "ONE-TIME-PUBLIC", algorithm='HS256')
            file.link = token
            file.link_type = "one"
            file.save()
            return token
        except File.DoesNotExist:
            raise Exception("Make One Time Public Not Found Error")

    def get_file_info(self, user_id, file_id):
        try:
            file = File.objects.get(id=file_id, owner=user_id)
            parent_id = file.parent.id if file.parent else "/"
            parent_name = "Home" if parent_id == "/" else "Unknown"
            if parent_id != "/":
                parent_folder = Folder.objects.filter(
                    owner=user_id, id=parent_id).first()
                if parent_folder:
                    parent_name = parent_folder.name
            file = json.loads(serializers.serialize('json', [file]))
            return {"currentFile": file, "parentName": parent_name}
        except File.DoesNotExist:
            raise Exception("Get File Info Not Found Error")

    def get_list(self, user, query):
        user_id = str(user.id)
        search_query = query.get("search", None)
        parent = None if query.get(
            "parent", None) == "/" else query.get("parent", None)
        limit = int(query.get("limit", 50))
        sort_by = sort_by_switch(query.get("sortby", None))
        start_at = query.get("startAt", 0)
        start_at_date = query.get("startAtDate", None)
        start_at_name = query.get("startAtName", None)
        query = Q()
        query &= Q(owner_id=user_id)
        if parent:
            query &= Q(parent_id=parent)
        else:
            query &= Q(parent=None)
        if start_at_date:
            query &= Q(upload_date__gte=start_at_date)
        if search_query:
            query &= Q(filename__icontains=search_query)
        if start_at_name:
            query &= Q(filename=start_at_name)

        file_list = File.objects.filter(query).order_by(sort_by)
        file_list = json.loads(serializers.serialize(
            'json', file_list))[start_at:limit]
        return file_list

    def delete_file(self, user, file_id):
        file = File.objects.get(id=file_id, owner=user.id)
        delete_s3_object(user, file.s3_id)
        file.delete()

    def download_file(self, user, file_id):
        s3_id = File.objects.get(id=file_id).s3_id
        url = generate_s3_presigned_url(user, s3_id, 3600)
        return url

    def get_download_token(self, user):
        pass

    def rename_file(self, user_id, file_id, title):
        try:
            file = File.objects.get(id=file_id, owner=user_id)
            file.filename = title
            file.save()
            data = json.loads(serializers.serialize('json', [file],))
            return data
        except File.DoesNotExist:
            raise Exception("Rename File Not Found Error")

    def remove_temp_token(self, user, temp_token, current_uuid):
        key = user.get_encryption_key()
        decoded = jwt.decode(
            temp_token, settings.PASSWORD_ACCESS, algorithms=['HS256'])
        public_key = decoded['iv']
        encrypted_token = user.encrypt_token(temp_token, key, public_key)
        user.remove_temp_token(encrypted_token)
        user.save()

    def get_suggested_list(self, user_id, search_query):
        search_query = search_query
        file_list = File.objects.filter(
            owner__id=user_id, filename__icontains=search_query)
        folder_list = Folder.objects.filter(
            owner__id=user_id, name__icontains=search_query)
        file_list = json.loads(serializers.serialize('json', file_list))
        folder_list = json.loads(serializers.serialize('json', folder_list))
        return {"fileList": file_list, "folderList": folder_list}

    def move_file(self, user_id, file_id, parent_id):
        try:
            parent_list = ["/"]
            if parent_id != None:
                parent_folder = Folder.objects.get(id=parent_id, owner=user_id)
                if parent_folder:
                    parent_list = parent_folder.parent_list
                    parent_list += parent_folder.name
                else:
                    raise Exception("Parent Folder Not Found Error")

            file = File.objects.get(id=file_id, owner=user_id)
            if parent_id:
                file.parent_id = parent_id
            if not parent_id and file.parent:
                file.parent = None
            file.parent_list = parent_list
            file.save()
            return file
        except ObjectDoesNotExist:
            raise Exception("Move File Not Found Error")
