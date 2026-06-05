from django.urls import path
from . import views
app_name = 'student'
urlpatterns = [
    path(
        '<int:class_id>/add_student/',
        views.StudentCreateView.as_view(),
        name='create'
    ),
    path(
        'classroom/<int:class_id>/import-students/',
        views.StudentCreateFromFileView.as_view(),
        name='import_file'
    ),
    path(
        '<int:pk>/',
        views.StudentDetailView.as_view(),
        name='detail'
    ),
    path(
        '<int:pk>/edit/',
        views.StudentUpdateView.as_view(),
        name='edit'),
    path(
        '<int:pk>/delete/',
        views.StudentDeleteView.as_view(),
        name='delete'),
    path('import/download-template/', views.download_student_import_template, name='download_template'),
]
