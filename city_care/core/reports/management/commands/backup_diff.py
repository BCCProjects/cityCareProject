from __future__ import annotations

import gzip
import io
import json
from datetime import datetime, timedelta, timezone as dt_timezone

import boto3
from botocore.client import Config
from django.conf import settings
from django.core.management import CommandError
from django.core.management.base import BaseCommand
from django.core.serializers.json import DjangoJSONEncoder

from accounts.models import City, Citizen, Employee, Organization, State
from core.reports.models import (
    Attachment,
    Category,
    Department,
    Report,
    ReportTag,
    StatusHistory,
    Tag,
)


class Command(BaseCommand):
    help = "Gera e envia backup diferencial (JSON) com registros alterados desde o ultimo marcador."

    def handle(self, *args, **options):  # type: ignore[override]
        endpoint = settings.BACKUP_S3_ENDPOINT_URL
        access_key = settings.BACKUP_S3_ACCESS_KEY_ID
        secret_key = settings.BACKUP_S3_SECRET_ACCESS_KEY
        bucket = settings.BACKUP_S3_BUCKET
        region = settings.BACKUP_S3_REGION or "us-east-1"
        prefix = settings.BACKUP_DIFFERENTIAL_PREFIX
        marker_key = f"{prefix}/_last_marker.txt"

        if not (endpoint and access_key and secret_key and bucket):
            raise CommandError("Config S3 de backup incompleta. Verifique endpoint/keys/bucket.")

        try:
            s3 = boto3.client(
                "s3",
                aws_access_key_id=access_key,
                aws_secret_access_key=secret_key,
                endpoint_url=endpoint,
                region_name=region,
                config=Config(
                    signature_version=(settings.AWS_S3_SIGNATURE_VERSION or "s3v4"),
                    s3={"addressing_style": (settings.AWS_S3_ADDRESSING_STYLE or "path")},
                ),
            )
        except Exception as exc:
            raise CommandError(f"Falha ao inicializar cliente S3: {exc}") from exc

        last_from: datetime | None = None
        try:
            obj = s3.get_object(Bucket=bucket, Key=marker_key)
            content = obj["Body"].read().decode("utf-8").strip()
            last_from = datetime.fromisoformat(content)
        except Exception:
            last_from = datetime.now(dt_timezone.utc) - timedelta(days=1)

        now = datetime.now(dt_timezone.utc)

        def qset(model, field_name: str):
            return list(model.objects.filter(**{f"{field_name}__gte": last_from}).values())

        payload = {
            "generated_at": now.isoformat(),
            "from": last_from.isoformat(),
            "to": now.isoformat(),
            "models": {
                "accounts.Employee": qset(Employee, "updated_at"),
                "accounts.Citizen": qset(Citizen, "updated_at"),
                "accounts.State": qset(State, "id"),
                "accounts.City": qset(City, "id"),
                "accounts.Organization": qset(Organization, "updated_at"),
                "core.Department": qset(Department, "updated_at"),
                "core.Category": qset(Category, "updated_at"),
                "core.Tag": qset(Tag, "updated_at"),
                "core.Report": qset(Report, "updated_at"),
                "core.Attachment": qset(Attachment, "created_at"),
                "core.StatusHistory": qset(StatusHistory, "created_at"),
                "core.ReportTag": list(
                    ReportTag.objects.filter(
                        report_id__in=Report.objects.filter(updated_at__gte=last_from).values_list("id", flat=True)
                    ).values()
                ),
            },
        }

        raw = json.dumps(payload, ensure_ascii=False, separators=(",", ":"), cls=DjangoJSONEncoder).encode("utf-8")
        buf = io.BytesIO()
        with gzip.GzipFile(fileobj=buf, mode="wb", compresslevel=6) as gz:
            gz.write(raw)
        buf.seek(0)

        ts_name = now.strftime("%Y-%m-%d_%H%M%S")
        key = f"{prefix}/{ts_name}.json.gz"

        try:
            s3.upload_fileobj(
                Fileobj=buf,
                Bucket=bucket,
                Key=key,
                ExtraArgs={"ContentType": "application/gzip"},
            )
            s3.put_object(Bucket=bucket, Key=marker_key, Body=now.isoformat().encode("utf-8"))
        except Exception as exc:
            raise CommandError(f"Falha no upload/marker S3: {exc}") from exc

        self.stdout.write(self.style.SUCCESS(f"Backup diferencial enviado para s3://{bucket}/{key}"))
