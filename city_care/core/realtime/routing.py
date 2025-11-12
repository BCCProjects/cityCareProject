from __future__ import annotations

from django.urls import path

from .consumers import ReportUpdatesConsumer

websocket_urlpatterns = [
    path("ws/reports/", ReportUpdatesConsumer.as_asgi()),
]

