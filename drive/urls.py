from django.urls import path
from . import views  # Import your Django views here

urlpatterns = [
    path('file-service/upload', views.upload_file, name='upload_file'),
    path('file-service/list', views.get_list, name='get_list'),
    path('file-service/remove', views.delete_file, name='delete_file'),
    path('file-service/rename', views.rename_file, name='rename_file'),
    path('file-service/info/<str:id>', views.get_file_info, name='get_file_info'),
    path('file-service/suggested-list', views.get_suggested_list, name='get_suggested_list'),
    path('file-service/download/<str:id>', views.download_file, name='download_file'),
    path('file-service/make-public/<str:id>', views.make_public, name='make_public'),
    path('file-service/public/info/<str:tempToken>', views.get_public_info, name='get_public_info'),
    path('file-service/public/download/<str:tempToken>', views.get_public_download, name='get_public_download'),
    path('file-service/quick-list', views.get_quick_list, name='get_quick_list'),
    path('file-service/make-one/<str:id>', views.make_one_time_public, name='make_one_time_public'),
    path('file-service/remove-link/<str:id>', views.remove_link, name='remove_link'),
    path('folder-service/upload', views.upload_folder, name='upload_folder'),
    path('folder-service/rename', views.rename_folder, name='rename_folder'),
    path('folder-service/remove', views.delete_folder, name='delete_folder'),
    path('folder-service/remove-all', views.delete_all, name='delete_all'),
    path('folder-service/list', views.get_folder_list, name='get_folder_list'),
    path('file-service/send-share-email', views.send_email_share, name='send_email_share'),
    path('folder-service/subfolder-list', views.get_subfolder_list, name='get_subfolder_list'),
    path('folder-service/subfolder-list-full', views.get_subfolder_full_list, name='get_subfolder_full_list'),
    path('folder-service/info/<str:id>', views.get_info, name='get_info'),
    path('file-service/move', views.move_file, name='move_file'),
    path('folder-service/move', views.move_folder, name='move_folder'),
]