from datetime import datetime

def convert_drive_folder_to_mongo_folder(drive_obj, owner_id):
    converted_obj = {
        "_id": drive_obj['id'],
        "name": drive_obj['name'],
        "createdAt": datetime.fromisoformat(drive_obj['createdTime']),
        "owner": owner_id,
        "parent": drive_obj['parents'][-1],
        "parentList": drive_obj['parents'],
        "updatedAt": datetime.fromisoformat(drive_obj['createdTime']),
        "drive": True,
        "googleDoc": drive_obj['mimeType'] == "application/vnd.google-apps.document"
    }

    return converted_obj
