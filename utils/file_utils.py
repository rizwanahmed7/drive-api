from django.http import HttpResponse, JsonResponse
from drive.models import File
from account.models import CustomUser as User  # Replace 'your_app' with your app name
from django.db.models import Q

class DbUtil:

    def get_public_file(self, file_id):
        try:
            file = File.objects.get(id=file_id)
            return file
        except File.DoesNotExist:
            return None

    def remove_one_time_public_link(self, file_id):
        try:
            file = File.objects.get(id=file_id)
            file.link_type = ""
            file.link = ""
            file.save()
            return file
        except File.DoesNotExist:
            return None

    def remove_link(self, file_id, user_id):
        try:
            file = File.objects.get(id=file_id, owner=user_id)
            file.link_type = ""
            file.link = ""
            file.save()
            return file
        except File.DoesNotExist:
            return None

    def make_public(self, file_id, user_id, token):
        try:
            file = File.objects.get(id=file_id, owner=user_id)
            file.link_type = "public"
            file.link = token
            file.save()
            return file
        except File.DoesNotExist:
            return None

    def get_public_info(self, file_id, temp_token):
        try:
            file = File.objects.get(id=file_id, link=temp_token)
            return file
        except File.DoesNotExist:
            return None

    def make_one_time_public(self, file_id, user_id, token):
        try:
            file = File.objects.get(id=file_id, owner=user_id)
            file.link_type = "one"
            file.link = token
            file.save()
            return JsonResponse({'message': 'One-time public link set successfully', 'data': file.to_dict()})
        except File.DoesNotExist:
            return HttpResponse('File not found or not owned by the user', status=404)
    
    def get_file_info(self, file_id, user_id):
        try:
            file = File.objects.get(id=file_id, owner=user_id)
            return JsonResponse({'message': 'File info retrieved successfully', 'data': file.to_dict()})
        except File.DoesNotExist:
            return HttpResponse('File not found or not owned by the user', status=404)

    def get_quick_list(self, user_id, s3_enabled):
        query = Q(owner=user_id)
        if not s3_enabled:
            query &= Q(personalFile=None)

        file_list = File.objects.filter(query).order_by('-uploadDate')[:10]
        file_list_data = [file.to_dict() for file in file_list]
        return JsonResponse({'message': 'Quick list retrieved successfully', 'data': file_list_data})


    from django.db.models import F

    def get_list(self, query_obj, sort_by, limit):
        file_list = File.objects.filter(query_obj).order_by(sort_by)[:limit]
        file_list_data = [file.to_dict() for file in file_list]
        return JsonResponse({'message': 'List retrieved successfully', 'data': file_list_data})


    def remove_temp_token(self, user_id, temp_token):
        try:
            user = User.objects.get(id=user_id)
            user.temp_tokens = [token for token in user.temp_tokens if token['token'] != temp_token]
            user.save()
            return JsonResponse({'message': 'Temp token removed successfully', 'data': user.to_dict()})
        except User.DoesNotExist:
            return HttpResponse('User not found', status=404)


    from django.db.models import Q

    def get_file_search_list(self, user_id, search_query):
        query = Q(owner=user_id) & Q(filename__regex=search_query)
        file_list = File.objects.filter(query)[:10]
        file_list_data = [file.to_dict() for file in file_list]
        return JsonResponse({'message': 'File search list retrieved successfully', 'data': file_list_data})

    def rename_file(self, file_id, user_id, title):
        try:
            file = File.objects.get(id=file_id, owner=user_id)
            file.filename = title
            file.save()
            return JsonResponse({'message': 'File renamed successfully', 'data': file.to_dict()})
        except File.DoesNotExist:
            return HttpResponse('File not found or not owned by the user', status=404)

    def move_file(self, file_id, user_id, parent, parent_list):
        try:
            file = File.objects.get(id=file_id, owner=user_id)
            file.parent = parent
            file.parentList = parent_list
            file.save()
            return JsonResponse({'message': 'File moved successfully', 'data': file.to_dict()})
        except File.DoesNotExist:
            return HttpResponse('File not found or not owned by the user', status=404)

    def get_file_list_by_parent(self, user_id, parent_list_string):
        file_list = File.objects.filter(owner_id=user_id, parent_list__iregex=parent_list_string)
        return file_list

    def get_file_list_by_owner(self, user_id):
        file_list = File.objects.filter(owner_id=user_id)
        file_list_data = [file.to_dict() for file in file_list]
        return JsonResponse({'message': 'File list by owner retrieved successfully', 'data': file_list_data})

    def remove_chunks_by_id(self, file_id):
        File.objects.get(id=file_id).delete()
        return JsonResponse({'message': 'Chunks removed successfully'})
