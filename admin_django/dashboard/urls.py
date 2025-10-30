"""
URLs for Dashboard.
"""
from django.urls import path
from . import views

app_name = 'dashboard'

urlpatterns = [
    path('', views.dashboard_home, name='home'),
    path('student/<uuid:student_id>/', views.student_detail, name='student_detail'),
    path('alerts/', views.alerts_list, name='alerts_list'),
    path('events/', views.events_list, name='events_list'),
    path('live/', views.live_monitor, name='live_monitor'),
]

