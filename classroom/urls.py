from django.urls import path
from . import views

app_name = 'classroom'

urlpatterns = [
    path('', views.ClassroomCreateView.as_view(), name='create'),
    path('list/', views.ClassroomListView.as_view(), name='list'),
    path(
        '<int:pk>/delete/',
        views.ClassroomDeleteView.as_view(),
        name='delete'
    ),
    path('<int:pk>/edit/', views.ClassroomUpdateView.as_view(), name='edit'),
    path('<int:pk>/', views.ClassroomDetailView.as_view(), name='detail'),
]
