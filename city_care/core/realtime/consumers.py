from __future__ import annotations

from typing import Iterable

from channels.generic.websocket import AsyncJsonWebsocketConsumer

from accounts.models import Citizen, Employee


class ReportUpdatesConsumer(AsyncJsonWebsocketConsumer):
    group_names: list[str]

    async def connect(self):
        user = self.scope.get("user")
        if not getattr(user, "is_authenticated", False):
            await self.close(code=4401)
            return

        groups = list(self._groups_for_user(user))
        if not groups:
            await self.close(code=4403)
            return

        self.group_names = groups
        for group in groups:
            await self.channel_layer.group_add(group, self.channel_name)
        await self.accept()
        await self.send_json({"type": "connection.ready"})

    async def disconnect(self, close_code):
        for group in getattr(self, "group_names", []):
            await self.channel_layer.group_discard(group, self.channel_name)

    async def receive_json(self, content, **kwargs):
        if content.get("type") == "ping":
            await self.send_json({"type": "pong"})

    async def report_event(self, event):
        await self.send_json(event["data"])

    def _groups_for_user(self, user) -> Iterable[str]:
        if isinstance(user, Citizen):
            return [f"citizen_{user.id}"]
        if isinstance(user, Employee):
            groups = []
            if user.organization_id:
                groups.append(f"organization_{user.organization_id}")
            if getattr(user, "is_superuser", False):
                groups.append("admin_global")
            return groups
        return []

