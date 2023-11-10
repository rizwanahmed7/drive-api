from django.db import models
from account.models import CustomUser
from django.core.files.storage import default_storage


class Thumbnail(models.Model):
    name = models.CharField(max_length=255, null=True)
    owner = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
    data = models.BinaryField(null=True)
    path = models.CharField(max_length=255, null=True)
    IV = models.BinaryField(null=True)
    s3ID = models.CharField(max_length=255, null=True)
    personal_file = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name
    

class Folder(models.Model):
    name = models.CharField(max_length=255, null=True)
    parent = models.ForeignKey('self', on_delete=models.CASCADE, null=True)
    owner = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
    parent_list = models.JSONField(null=True)
    personal_folder = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name

    
class File(models.Model):
    length = models.PositiveIntegerField()
    chunk_size = models.PositiveIntegerField(null=True)
    upload_date = models.DateTimeField()
    filename = models.CharField(max_length=255)
    owner = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
    parent = models.ForeignKey(Folder,on_delete=models.CASCADE, null=True)
    parent_list = models.CharField(max_length=255)
    has_thumbnail = models.BooleanField()
    is_video = models.BooleanField(default=False)
    is_image = models.BooleanField(default=False)
    thumbnail_id = models.ForeignKey(Thumbnail, on_delete=models.CASCADE, null=True)
    size = models.PositiveIntegerField()
    IV = models.BinaryField()
    link_type = models.CharField(max_length=255, null=True)
    link = models.CharField(max_length=255, null=True)
    s3_id = models.CharField(max_length=255, null=True)
    personal_file = models.BooleanField(default=True)
    file_path = models.CharField(max_length=1000) 


    def __str__(self):
        return self.filename
    
    def remove_chunks(self):
        try:
            # Remove file chunks from the storage backend
            if self.filename:
                default_storage.delete(self.filename)
        except Exception as e:
            print("Could not remove chunks for file:", e)