from django.urls import path
from . import views

urlpatterns = [
    path('login', views.login, name='login'),
    path('get-token', views.get_token, name='login'),
    path('create', views.create_user, name='create_user'),
    path('change-password', views.change_password, name='change_password'),
    path('user-detailed', views.get_user_detailed, name='get_user_detailed'),
    path('resend-verify-email', views.resend_verify_email, name='resend_verify_email'),
    path('verify-email/<str:token>', views.verify_email, name='verify_email'),
    path('send-password-reset', views.send_password_reset, name='send_password_reset'),
    path('reset-password', views.reset_password, name='reset_password'),
    path('refresh-storage-size', views.refresh_storage_size, name='refresh_storage_size'),
    path('user', views.get_user, name='get_user'),
    path('add-name', views.add_name, name='add_name'),
    path('add-s3-storage', views.add_s3_storage, name='add_s3_storage'),
    path('remove-s3-storage', views.remove_s3_storage, name='remove_s3_storage'),
    path('remove-s3-metadata', views.remove_s3_metadata, name='remove_s3_metadata'),
    path('logout', views.logout, name='logout'),
    path('download-personal-file-list', views.download_personal_file_list, name='download_personal_file_list'),
    path('upload-personal-file-list', views.upload_personal_file_list, name='upload_personal_file_list'),
]