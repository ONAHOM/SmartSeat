from django.urls import path
from . import views

app_name = 'olympiads'

urlpatterns = [
    # Олимпиады
    path('', views.OlympicEventListView.as_view(), name='event_list'),
    path('add/', views.OlympicEventCreateView.as_view(), name='event_create'),
    path('<int:pk>/', views.OlympicEventDetailView.as_view(), name='event_detail'),
    path('<int:pk>/edit/', views.OlympicEventUpdateView.as_view(), name='event_update'),
    path('<int:pk>/del/', views.OlympicEventDeleteView.as_view(), name='event_delete'),
    path('<int:event_id>/import/olympians/', views.OlympicImportView.as_view(), name='import_olympians'),
    path('<int:event_id>/import/classrooms/', views.OlympicClassroomImportView.as_view(), name='import_classrooms'),

    # Аудитории (привязаны к id олимпиады)
    path('<int:event_id>/room/add/', views.OlympicClassroomCreateView.as_view(), name='classroom_create'),
    path('room/<int:pk>/', views.OlympicClassroomDetailView.as_view(), name='classroom_detail'),
    path('room/<int:pk>/edit/', views.OlympicClassroomUpdateView.as_view(), name='classroom_update'),
    path('room/<int:pk>/del/', views.OlympicClassroomDeleteView.as_view(), name='classroom_delete'),

    # Участники (привязаны к id комнаты)
    path('room/<int:classroom_id>/user/add/', views.OlympianCreateView.as_view(), name='olympian_create'),
    path('user/<int:pk>/edit/', views.OlympianUpdateView.as_view(), name='olympian_update'),
    path('user/<int:pk>/del/', views.OlympianDeleteView.as_view(), name='olympian_delete'),

    # Сервисный триггер двухэтапного расчета
    path('<int:event_id>/calc/', views.CalculateGlobalOlympicSeatingView.as_view(), name='calculate_global_seating'),
]
