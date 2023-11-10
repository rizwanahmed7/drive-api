from account.models import CustomUser  # Import the User model from your Django app
import boto3
from botocore.exceptions import NoCredentialsError
from django.conf import settings

import boto3
import botocore

def delete_s3_object(user, object_key):
    s3_data = user.decrypt_s3_data()
    ID = s3_data.get('id') or settings.AWS_ACCESS_KEY_ID
    KEY = s3_data.get('key') or settings.AWS_SECRET_ACCESS_KEY
    bucket_name = s3_data.get('bucket') or settings.AWS_STORAGE_BUCKET_NAME
    region = s3_data.get('regoin') or settings.AWS_S3_REGION_NAME
    session = boto3.Session(
        aws_access_key_id=ID,
        aws_secret_access_key=KEY,
        region_name=region  
        )
    s3 = session.client('s3')
    try:
        s3.delete_object(Bucket=bucket_name, Key=object_key)
        print(f'Successfully deleted object with key: {object_key}')
    except Exception as e:
        print(f'Error deleting object: {str(e)}')



def generate_s3_presigned_url(user, object_key, expires_in=3600*24):
    s3_data = user.decrypt_s3_data()
    ID = s3_data.get('id') or settings.AWS_ACCESS_KEY_ID
    KEY = s3_data.get('key') or settings.AWS_SECRET_ACCESS_KEY
    bucket_name = s3_data.get('bucket') or settings.AWS_STORAGE_BUCKET_NAME
    region = s3_data.get('regoin') or settings.AWS_S3_REGION_NAME
    session = boto3.Session(
        aws_access_key_id=ID,
        aws_secret_access_key=KEY,
        region_name=region  
        )
    s3 = session.client('s3', config=botocore.client.Config(signature_version='s3v4'))
    params = {
        'Bucket': bucket_name,
        'Key': object_key
    }
    url = s3.generate_presigned_url(
            ClientMethod="get_object", Params=params, ExpiresIn=expires_in
    )
    return url



def upload_file_to_s3(file, file_name, user):
    s3_data = user.decrypt_s3_data()
    ID = s3_data.get('id') or settings.AWS_ACCESS_KEY_ID
    KEY = s3_data.get('key') or settings.AWS_SECRET_ACCESS_KEY
    bucket_name = s3_data.get('bucket') or settings.AWS_STORAGE_BUCKET_NAME
    region = s3_data.get('regoin') or settings.AWS_S3_REGION_NAME
    session = boto3.Session(
        aws_access_key_id=ID,
        aws_secret_access_key=KEY,
        region_name='us-east-1'  
        )
    s3 = session.client('s3')
    try:
        # Upload the file to the specified S3 bucket and object name.
        s3.upload_fileobj(file, bucket_name, file_name)
    except Exception as e:
        # Handle any errors that occur during the upload.
        print(f"Error uploading file to S3: {str(e)}")
        return False

    return True

def subtract_from_storage_size(user_id: int, size: int, is_personal_file: bool):
    # Retrieve the user from the database
    user = CustomUser.objects.get(pk=user_id)  # You should replace 'pk' with the actual primary key field name

    if is_personal_file:
        if user.storage_data_personal:
            user.storage_data_personal['storage_size'] -= size
            if user.storage_data_personal['storage_size'] < 0:
                user.storage_data_personal['storage_size'] = 0
            user.storage_data_personal.save()
    else:
        if not user.storage_data or not user.storage_data['storage_size'] or not user.storage_data.storage_limit:
            user.storage_data = {
                'storage_size': 0,
                'storage_limit': 0,
            }

        user.storage_data['storage_size'] -= size

        if user.storage_data['storage_size'] < 0:
            user.storage_data['storage_size'] = 0

        user.storage_data.save()


async def remove_temp_token(user_id, temp_token):
    try:
        user = CustomUser.objects.get(pk=user_id)  # Replace 'pk' with the actual primary key field name
        user.temp_tokens = [token for token in user.temp_tokens if token['token'] != temp_token]
        user.save()
    except CustomUser.DoesNotExist:
        pass

def remove_chunks_s3(bucket_name, object_key):
    try:
        s3 = boto3.client('s3')
        s3.delete_object(Bucket=bucket_name, Key=object_key)
    except NoCredentialsError:
        print("AWS credentials not available")



## DB UTILS
from utils.file_utils import DbUtil as FileUtils
file_utils = FileUtils()

def remove_chunks(bucket_stream):
    upload_id = str(bucket_stream.id)

    try:
        if not upload_id:
            print("Invalid uploadID for removing chunks")
            return

        file_utils.remove_chunks_by_id(upload_id)

    except Exception as e:
        print(f"Could not remove chunks for canceled upload {upload_id}: {e}")


def get_prev_iv_s3(start, key, is_personal, user):
    try:
        if is_personal:
            s3_data = user.decrypt_s3_data()
            s3_storage = boto3.client(
                's3',
                aws_access_key_id=s3_data['id'],
                aws_secret_access_key=s3_data['key']
            )

            params = {
                'Bucket': s3_data['bucket'],
                'Key': key,
                'Range': f'bytes={start}-{start + 15}'
            }

            stream = s3_storage.get_object(Bucket=params['Bucket'], Key=params['Key'], Range=params['Range'])

            data = b''
            for chunk in stream['Body'].iter_chunks():
                data += chunk

            return data

        else:
            s3 = boto3.client('s3', region_name='your-region', aws_access_key_id='your-access-key',
                             aws_secret_access_key='your-secret-key')

            params = {
                'Bucket': 'your-bucket-name',
                'Key': key,
                'Range': f'bytes={start}-{start + 15}'
            }

            stream = s3.get_object(Bucket=params['Bucket'], Key=params['Key'], Range=params['Range'])

            data = b''
            for chunk in stream['Body'].iter_chunks():
                data += chunk

            return data

    except NoCredentialsError as e:
        # Handle authentication errors
        print(f"Could not authenticate with AWS S3: {e}")
    except Exception as e:
        # Handle other errors
        print(f"An error occurred while fetching data from S3: {e}")

    return None

def add_to_storage_size(user, size, is_personal_file):
    if is_personal_file:
        user.storage_data_personal['storage_size'] += size
        user.storage_data_personal.save()
    else:
        if not user.storage_data:
            user.storage_data = {"storage_size":0, "storage_limit":0}
        user.storage_size += size
        user.save()

