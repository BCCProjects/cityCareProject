from __future__ import annotations

import pytest
from django.core.files.storage import FileSystemStorage

from core.reports.models import Attachment
from tests.utils import get_forced_city, reset_forced_city


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
