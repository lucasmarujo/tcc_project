"""
URLs for Monitoring API.
"""
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    MonitoringEventViewSet,
    AlertViewSet,
    report_event,
    create_alert,
    heartbeat
)

router = DefaultRouter()
router.register(r'events', MonitoringEventViewSet, basename='event')
router.register(r'alerts', AlertViewSet, basename='alert')

urlpatterns = [
    path('', include(router.urls)),
    path('report/', report_event, name='report_event'),
    path('alert/', create_alert, name='create_alert'),
    path('heartbeat/', heartbeat, name='heartbeat'),
]

