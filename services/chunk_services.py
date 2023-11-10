from django.core.exceptions import PermissionDenied
from hashlib import sha256
from drive.models import Thumbnail
import os as AES
from io import BytesIO


class ChunkServices:
    def get_thumbnail(user, id):
        password = user.getEncryptionKey()
        
        if not password:
            raise PermissionDenied("Invalid Encryption Key")
        try:
            thumbnail = Thumbnail.objects.get(id=id)
        except Thumbnail.DoesNotExist:
            raise PermissionDenied('Thumbnail not found')
        if thumbnail.owner != str(user.id):
            raise PermissionDenied('Thumbnail Unauthorized Error')
        iv = thumbnail.IV
        cipher_key = sha256(password.encode('utf-8')).digest()
        decipher = AES.new(cipher_key, AES.MODE_CBC, iv)
        try:
            with open(thumbnail.path, 'rb') as file:
                encrypted_data = file.read()
                decrypted_data = decipher.decrypt(encrypted_data)

            buffer_data = BytesIO(decrypted_data)
            return buffer_data
        except FileNotFoundError:
            raise PermissionDenied('Thumbnail file not found')
        except Exception as e:
            raise PermissionDenied(f'Error while decrypting thumbnail: {str(e)}')
