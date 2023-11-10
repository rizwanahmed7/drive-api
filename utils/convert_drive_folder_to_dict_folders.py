from .convert_drive_folder_to_mongo_folder import convert_drive_folder_to_mongo_folder

def convert_drive_folders_to_mongo_folders(drive_objs, owner_id):
    converted_folders = []

    for current_folder in drive_objs:
        converted_folders.append(convert_drive_folder_to_mongo_folder(current_folder, owner_id))

    return converted_folders