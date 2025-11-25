from __future__ import annotations

import pytest


@pytest.fixture(autouse=True)
def _disable_realtime_broadcast_core(monkeypatch):
    """
    Prevent core.reports.tests from attempting to connect to Redis via channels_redis.
    """

    def _noop(*_args, **_kwargs):
        return None

    monkeypatch.setattr("core.realtime.publisher._broadcast", _noop)

