from django.db import models
from django.contrib.auth.models import AbstractBaseUser
from django.contrib.auth.models import PermissionsMixin
from django.contrib.auth.base_user import BaseUserManager
import jwt
import Cryptodome
import hashlib
from datetime import datetime
from datetime import timedelta
from rest_framework_simplejwt.tokens import RefreshToken
import secrets
from Cryptodome.Cipher import AES
from Cryptodome.Protocol.KDF import PBKDF2
import hashlib


class UserManager(BaseUserManager):
    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError('The Email field must be set')
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)

        if extra_fields.get('is_staff') is not True:
            raise ValueError('Superuser must have is_staff=True.')
        if extra_fields.get('is_superuser') is not True:
            raise ValueError('Superuser must have is_superuser=True.')

        return self.create_user(email, password, **extra_fields)

class CustomUser(AbstractBaseUser, PermissionsMixin):
    email = models.EmailField(unique=True)
    name = models.CharField(max_length=255, null=True)
    password = models.CharField(max_length=255)
    tokens = models.JSONField(default=list)
    temp_tokens = models.JSONField(default=list)
    private_key = models.CharField(max_length=255, null=True)
    public_key = models.CharField(max_length=255, null=True)
    email_verified = models.BooleanField(null=True)
    email_token = models.CharField(max_length=255, null=True)
    password_reset_token = models.CharField(max_length=255, null=True)
    s3_enabled = models.BooleanField(null=True)
    s3_data = models.JSONField(null=True)
    personal_storage_canceled_date = models.IntegerField(null=True)
    storage_data = models.JSONField(null=True)
    storage_data_personal = models.JSONField(null=True)
    active_subscription = models.BooleanField(null=True)
    plan_id = models.CharField(max_length=255, null=True)
    storage_size = models.PositiveIntegerField(default=0)
    last_subscription_check_time = models.IntegerField(null=True)
    last_subscription_status = models.BooleanField(null=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    objects = UserManager()

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = []

    def __str__(self):
        return self.email

    def encrypt_token(self, token, key, iv):
        iv = bytes.fromhex(iv)

        token_cipher_key = hashlib.pbkdf2_hmac('sha256', key.encode(), b'salt', 100000)
        cipher = Cryptodome.Cipher(Cryptodome.algorithms.AES(token_cipher_key), Cryptodome.modes.CFB(iv), iv)
        encryptor = cipher.encryptor()
        encrypted_text = encryptor.update(token.encode()) + encryptor.finalize()

        return encrypted_text.hex()

    def decrypt_token(self, encrypted_token, key, iv):
        encrypted_token = bytes.fromhex(encrypted_token)
        iv = bytes.fromhex(iv)

        token_cipher_key = hashlib.pbkdf2_hmac('sha256', key.encode(), b'salt', 100000)
        cipher = Cryptodome.Cipher(Cryptodome.algorithms.AES(token_cipher_key), Cryptodome.modes.CFB(iv), iv)
        decryptor = cipher.decryptor()
        decrypted_text = decryptor.update(encrypted_token) + decryptor.finalize()

        return decrypted_text.decode()


    def generate_encryption_keys(self):
        random_key = secrets.token_bytes(32)
        iv = secrets.token_bytes(16)
        user_cipher_key = PBKDF2(self.password.encode(), b'salt', dkLen=32, count=100000, prf=lambda p, s: hashlib.pbkdf2_hmac('sha256', p, s, 100000))
        cipher = AES.new(user_cipher_key, AES.MODE_CFB, iv=iv)
        encrypted_text = cipher.encrypt(random_key)
        master_cipher_key = PBKDF2(env.key.encode(), b'salt', dkLen=32, count=100000, prf=lambda p, s: hashlib.pbkdf2_hmac('sha256', p, s, 100000))
        cipher = AES.new(master_cipher_key, AES.MODE_CFB, iv=iv)
        master_encrypted_text = cipher.encrypt(encrypted_text)
        self.private_key = master_encrypted_text.hex()
        self.public_key = iv.hex()

        self.save()

    def get_encryption_key(self):
        try:
            iv = bytes.fromhex(self.public_key)
            user_cipher_key = Cryptodome.pbkdf2_hmac('sha256', self.password.encode(), b'salt', 100000)
            master_cipher_key = Cryptodome.pbkdf2_hmac('sha256', env.key.encode(), b'salt', 100000)

            master_encrypted_text = bytes.fromhex(self.private_key)
            cipher = Cryptodome.Cipher(Cryptodome.algorithms.AES(master_cipher_key), Cryptodome.modes.CFB(iv), iv)
            master_decrypted = cipher.decryptor().update(master_encrypted_text) + cipher.decryptor().finalize()

            cipher = Cryptodome.Cipher(Cryptodome.algorithms.AES(user_cipher_key), Cryptodome.modes.CFB(iv), iv)
            decrypted = cipher.decryptor().update(master_decrypted) + cipher.decryptor().finalize()

            return decrypted
        except Exception as e:
            print("Get Encryption Key Error", e)
            return None

    def change_encryption_key(self, random_key):
        iv = Cryptodome.token_bytes(16)
        user_cipher_key = Cryptodome.pbkdf2_hmac('sha256', self.password.encode(), b'salt', 100000)
        cipher = Cryptodome.Cipher(Cryptodome.algorithms.AES(user_cipher_key), Cryptodome.modes.CFB(iv), iv)
        encrypted_text = cipher.encryptor().update(random_key) + cipher.encryptor().finalize()

        master_cipher_key = Cryptodome.pbkdf2_hmac('sha256', env.key.encode(), b'salt', 100000)
        cipher = Cryptodome.Cipher(Cryptodome.algorithms.AES(master_cipher_key), Cryptodome.modes.CFB(iv), iv)
        master_encrypted_text = cipher.encryptor().update(encrypted_text) + cipher.encryptor().finalize()

        self.private_key = master_encrypted_text.hex()
        self.public_key = iv.hex()

        self.save()

    def generate_temp_auth_token(self):
        iv = Cryptodome.token_bytes(16)
        token = jwt.encode({'_id': str(self.id), 'iv': iv.decode()}, env.password_access, algorithm='HS256', expires_in='3000s')

        encryption_key = self.get_encryption_key()
        encrypted_token = self.encrypt_token(token, encryption_key, iv.hex())

        self.temp_tokens.append({'token': encrypted_token})
        self.save()

        return token
    
    def generate_auth_token(self,uuid):
        iv = secrets.token_bytes(16)
        user_obj = {
            "_id": str(self.pk),
            "emailVerified": self.email_verified, 
            "email": self.email,
            "s3Enabled": self.s3_enabled,
        }
        expires_in_maxAgeAccess = datetime.utcnow() + timedelta(minutes=30)
        access_token = jwt.encode({"user": user_obj, "exp":expires_in_maxAgeAccess.timestamp()}, "AUTH-TOKEN", algorithm='HS256')
        time = datetime.utcnow().timestamp()
        expires_in_maxAgeRefresh = datetime.utcnow() + timedelta(days=7)
        refresh_token = jwt.encode({"_id": str(self.pk), "exp":expires_in_maxAgeRefresh.timestamp(), "time": time}, "AUTH-TOKEN", algorithm='HS256')
        encryption_key = self.get_encryption_key()
        encrypted_token = self.encrypt_token(refresh_token, encryption_key, iv)
        self.tokens.append({"token": encrypted_token, "uuid": uuid, "time": time})
        self.save()
        return access_token, refresh_token

    def encrypt_s3_data(self, ID, key, bucket):
        
        user_obj = {
            "user_id": self.pk,
            "s3_id": ID,
            "s3_key": key,
            "s3_bucket": bucket,
        }

        encrypted_s3_data = jwt.encode({"user": user_obj}, "S3-DATA-KEY", algorithm='HS256')

        self.s3_data = encrypted_s3_data
        self.s3_enabled = True

        self.save()

    def decrypt_s3_data(self):
        try:
            decrypted_s3_data = jwt.decode({"user": self.s3_data}, "S3-DATA-KEY", algorithm='HS256')
            s3_data = {
                'id': decrypted_s3_data['s3_id'], 
                'key': decrypted_s3_data['s3_key'], 
                'bucket': decrypted_s3_data['s3_bucket']
                }
            return s3_data
        except:
            return {}

    def generate_temp_auth_token_video(self, cookie):
        iv = Cryptodome.token_bytes(16)
        token = jwt.encode({'_id': str(self.id), 'cookie': cookie, 'iv': iv.decode()}, env.password_access, algorithm='HS256', expires_in='5h')

        encryption_key = self.get_encryption_key()
        encrypted_token = self.encrypt_token(token, encryption_key, iv.hex())

        self.temp_tokens.append({'token': encrypted_token})
        self.save()

        return token