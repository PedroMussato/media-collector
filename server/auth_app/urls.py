from django.urls import path
from .views import(
    register,
    login,
    logout,
    request_password_reset,
    reset_password,
    redefine_password,
    profile,
)

urlpatterns = [
    path('register/', register, name='register'),
    path('login/', login, name='login'),
    path('logout/', logout, name='logout'),
    path('request_password_reset/', request_password_reset, name='request_password_reset'),
    path('reset_password/<str:token>/', reset_password, name='reset_password'),
    path('redefine_password/', redefine_password, name='redefine_password'),
    path('profile/', profile, name='profile'),
]