from django.urls import path
from . import views

app_name = 'calculate'
urlpatterns = [
    path(
        '<int:classroom_id>/',
        views.calculate_seating,
        name='seating')
]
