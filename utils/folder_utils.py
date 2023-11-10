from drive.models import Folder  

class DbUtil:

    def get_folder_search_list(self, user_id, search_query):
        folder_list = Folder.objects.filter(owner=user_id, name__iregex=search_query)[:10]
        return folder_list

    def get_folder_info(self, folder_id, user_id):
        try:
            folder = Folder.objects.get(id=folder_id, owner=user_id)
            return folder
        except Folder.DoesNotExist:
            return None

    def get_folder_list_by_parent(self, user_id, parent, sort_by=None, item_type=None):
        query = {'owner_id': user_id, 'parent_id': parent}

        if item_type == 'personal':
            query['personal_folder'] = True
        elif item_type == 'nonpersonal':
            query['personal_folder'] = False

        folder_list = Folder.objects.filter(**query).order_by(sort_by)
        return folder_list

    def get_folder_list_by_search(self, user_id, search_query, sort_by, parent,folder_search, item_type):
        query = {'name__iregex': search_query, 'owner_id': user_id}

        if parent and (parent != '/' or folder_search):
            query['parent_id'] = parent

        if item_type == 'personal':
            query['personal_folder'] = True
        elif item_type == 'nonpersonal':
            query['personal_folder'] = False

        folder_list = Folder.objects.filter(**query).order_by(sort_by)
        return folder_list

    def move_folder(self, folder_id, user_id, parent, parent_list):
        try:
            folder = Folder.objects.get(id=folder_id, owner=user_id)
            folder.parent_id = parent
            folder.parent_list = parent_list
            folder.save()
            return folder
        except Folder.DoesNotExist:
            return None


    def find_all_folders_by_parent(self, parent_id, user_id):
        folder_list = Folder.objects.filter(parent_list=parent_id, owner=user_id)
        return folder_list
