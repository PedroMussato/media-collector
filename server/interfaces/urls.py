from django.urls import path
from .views import home, create_band, band, create_album, album, create_music, music, delete_music, delete_album, delete_band, generate_conf_file_main, generate_conf_file_band, generate_conf_file_album

urlpatterns = [
    path('', home, name='home'),
    path('create_band/', create_band, name='create_band'),
    path('band/<str:uuid>/', band, name='band'),
    path('create_album/<str:uuid>/', create_album, name='create_album'),
    path('album/<str:uuid>/', album, name='album'),
    path('create_music/<str:uuid>/', create_music, name='create_music'),
    path('music/<str:uuid>/', music, name='music'),
    path('delete_music/<str:uuid>/', delete_music, name='delete_music'),
    path('delete_album/<str:uuid>/', delete_album, name='delete_album'),
    path('delete_band/<str:uuid>/', delete_band, name='deletedelete_band_album'),
    path('generate_conf_file_main/', generate_conf_file_main, name='generate_conf_file_main'),
    path('generate_conf_file_band/<str:uuid>/', generate_conf_file_band, name='generate_conf_file_band'),
    path('generate_conf_file_album/<str:uuid>/', generate_conf_file_album, name='generate_conf_file_album'),
]




