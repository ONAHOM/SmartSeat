from django.urls import path
from . import views

app_name = 'user'

urlpatterns = [
    path('settings/', views.UserSettingsView.as_view(), name='settings'),
]
