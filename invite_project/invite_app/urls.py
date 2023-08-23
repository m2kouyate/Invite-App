from django.urls import path
from . import views

urlpatterns = [
    path('', views.login_view, name='login_view'),
    path('profile/', views.profile_view, name='profile_view'),
    path('code_verification/', views.verify_code_view, name='code_verification'),
    path('api/auth/send_code/', views.send_code, name='send_code'),
    path('api/auth/verify_code/', views.verify_code, name='verify_code'),
    path('api/profile/', views.user_profile, name='user_profile'),
    path('api/invite/activate/', views.activate_invite_code, name='activate_invite_code'),
]
