"""
WebSocket routing for real-time updates.
"""
from django.urls import re_path
from . import consumers

websocket_urlpatterns = [
    re_path(r'ws/monitoring/$', consumers.MonitoringConsumer.as_asgi()),
    re_path(r'ws/webcam/(?P<registration_number>[^/]+)/$', consumers.WebcamConsumer.as_asgi()),
    re_path(r'ws/webcam-view/(?P<registration_number>[^/]+)/$', consumers.WebcamViewerConsumer.as_asgi()),
    re_path(r'ws/screen/(?P<registration_number>[^/]+)/$', consumers.ScreenConsumer.as_asgi()),
    re_path(r'ws/screen-view/(?P<registration_number>[^/]+)/$', consumers.ScreenViewerConsumer.as_asgi()),
    re_path(r'ws/browser/(?P<registration_number>[^/]+)/$', consumers.BrowserConsumer.as_asgi()),
    re_path(r'ws/browser-view/(?P<registration_number>[^/]+)/$', consumers.BrowserViewerConsumer.as_asgi()),
]
