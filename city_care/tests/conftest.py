from __future__ import annotations

import os

import django
import pytest
from django.core.files.storage import FileSystemStorage

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "city_care.settings")
django.setup()

from core.reports.models import Attachment  # noqa: E402
from tests.utils import get_forced_city, reset_forced_city  # noqa: E402


@pytest.fixture(autouse=True)
def _disable_realtime_broadcast(monkeypatch):
    """
    Prevent tests from attempting to connect to Redis via channels_redis.
    """

    def _noop(*_args, **_kwargs):
        return None

    monkeypatch.setattr("core.realtime.publisher._broadcast", _noop)


@pytest.fixture(autouse=True)
def _force_city_resolution(monkeypatch):
    reset_forced_city()

    def _resolver(*_args, **_kwargs):
        return get_forced_city()

    monkeypatch.setattr("core.services.report_service.resolve_city_from_coordinates", _resolver)
    yield
    reset_forced_city()


@pytest.fixture(autouse=True)
def _local_attachment_storage(settings, tmp_path_factory):
    settings.USE_SUPABASE_ATTACHMENTS = False
    storage = FileSystemStorage(location=tmp_path_factory.mktemp("attachments"))
    field = Attachment._meta.get_field("file")
    original_storage = field.storage
    field.storage = storage
    yield
    field.storage = original_storage
