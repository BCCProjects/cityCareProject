from __future__ import annotations

import os

from channels.routing import ProtocolTypeRouter, URLRouter
from django.conf import settings
from django.contrib.staticfiles.handlers import ASGIStaticFilesHandler
from django.core.asgi import get_asgi_application

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "city_care.settings")

django_asgi_app = get_asgi_application()
if settings.DEBUG:
    django_asgi_app = ASGIStaticFilesHandler(django_asgi_app)

try:
    from core.realtime.auth import JWTAuthMiddlewareStack
    from core.realtime.routing import websocket_urlpatterns
except Exception:  # pragma: no cover - defensive fallback during collectstatic/migrations
    JWTAuthMiddlewareStack = lambda inner: inner  # type: ignore
    websocket_urlpatterns = []

application = ProtocolTypeRouter({
    "http": django_asgi_app,
    "websocket": JWTAuthMiddlewareStack(URLRouter(websocket_urlpatterns)),
})
