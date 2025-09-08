from django.urls import path
from django.contrib.auth import views as auth_views
from . import views

app_name = 'authentication'

urlpatterns = [
    path('register/', views.CustomRegistrationView.as_view(), name='register'),
    path('login/', views.CustomLoginView.as_view(), name='login'),
    path('logout/', auth_views.LogoutView.as_view(), name='logout'),
    path('profile/', views.profile_view, name='profile'),
]
