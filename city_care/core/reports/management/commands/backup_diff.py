from __future__ import annotations

import os
import shlex
import shutil
import subprocess
from datetime import datetime, timedelta, timezone as dt_timezone
from pathlib import Path

import boto3
from botocore.client import Config
from django.conf import settings
from django.core.management import CommandError
from django.core.management.base import BaseCommand

from accounts.models import City, Citizen, Employee, Organization, State
from core.reports.management.commands.backup_full import _mysqldump_supports_ssl_mode
from core.reports.models import Attachment, Category, Department, Report, ReportTag, StatusHistory, Tag


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

        db = settings.DATABASES["default"]
        engine = db["ENGINE"]
        if not engine.endswith("mysql"):
            raise CommandError("Backup diferencial em SQL requer DB_ENGINE=mysql.")

        host = db.get("HOST", "localhost")
        port = str(db.get("PORT", "3306"))
        user = db.get("USER")
        password = db.get("PASSWORD")
        name = db.get("NAME")
        if not all([user, name]):
            raise CommandError("Config MySQL incompleta para backup diferencial.")

        ssl_mode = (
            os.getenv("MYSQL_SSL_MODE")
            or os.getenv("MYSQLDUMP_SSL_MODE")
            or db.get("OPTIONS", {}).get("ssl_mode")
        )
        extra_args_raw = os.getenv("MYSQLDUMP_EXTRA_ARGS", "")
        extra_args = shlex.split(extra_args_raw) if extra_args_raw.strip() else []
        mysqldump_path = (
            os.getenv("MYSQLDUMP_PATH")
            or shutil.which("mysqldump")
            or shutil.which("mariadb-dump")
            or "mysqldump"
        )

        tmp_dir = Path(settings.BASE_DIR) / "_tmp_backups"
        tmp_dir.mkdir(exist_ok=True)

        ts_name = now.strftime("%Y-%m-%d_%H%M%S")
        sql_path = tmp_dir / f"mysql_diff_{ts_name}.sql"

        timestamp_str = last_from.astimezone(dt_timezone.utc).replace(microsecond=0).strftime("%Y-%m-%d %H:%M:%S")

        table_targets: list[tuple[str, str | None, str | None]] = [
            (Employee._meta.db_table, "updated_at", None),
            (Citizen._meta.db_table, "updated_at", None),
            (State._meta.db_table, None, None),
            (City._meta.db_table, None, None),
            (Organization._meta.db_table, "updated_at", None),
            (Department._meta.db_table, "updated_at", None),
            (Category._meta.db_table, "updated_at", None),
            (Tag._meta.db_table, "updated_at", None),
            (Report._meta.db_table, "updated_at", None),
            (Attachment._meta.db_table, "created_at", None),
            (StatusHistory._meta.db_table, "created_at", None),
            (
                ReportTag._meta.db_table,
                None,
                f"report_id IN (SELECT id FROM {Report._meta.db_table} WHERE updated_at >= '{timestamp_str}')",
            ),
        ]

        header = (
            f"-- CityCare differential backup\n"
            f"-- Range: {last_from.isoformat()} -> {now.isoformat()}\n"
            f"-- Tables: {', '.join(t for t, _, _ in table_targets)}\n\n"
        )

        base_cmd = [
            mysqldump_path,
            "-h",
            host,
            "-P",
            port,
            "-u",
            user,
            f"-p{password}" if password else "",
            "--single-transaction",
            "--skip-lock-tables",
            "--no-create-db",
            "--skip-add-locks",
            "--skip-add-drop-table",
            "--skip-comments",
            "--no-create-info",
            "--replace",
        ]

        if ssl_mode:
            normalized_mode = ssl_mode.strip().upper()
            supports_ssl_mode = _mysqldump_supports_ssl_mode(mysqldump_path)
            if normalized_mode == "DISABLED":
                base_cmd.extend(["--skip-ssl", "--skip-ssl-verify-server-cert"])
            elif supports_ssl_mode:
                base_cmd.extend(["--ssl-mode", normalized_mode])
            else:
                self.stderr.write(
                    self.style.WARNING(
                        "MYSQL_SSL_MODE configurado, mas o mysqldump atual não suporta --ssl-mode. "
                        "Use MYSQLDUMP_EXTRA_ARGS para repassar flags compatíveis."
                    )
                )
        if extra_args:
            base_cmd.extend(extra_args)

        try:
            with open(sql_path, "wb") as f_out:
                f_out.write(header.encode("utf-8"))
                for table, field, custom_where in table_targets:
                    cmd = list(base_cmd)
                    where_clause: str | None = custom_where
                    if field:
                        where_clause = f"{field} >= '{timestamp_str}'"
                    if where_clause:
                        cmd.extend(["--where", where_clause])
                    cmd.extend([name, table])
                    cmd = [c for c in cmd if c]
                    subprocess.run(cmd, check=True, stdout=f_out)
                    f_out.write(b"\n")
        except FileNotFoundError as exc:
            raise CommandError(
                "mysqldump não encontrado no PATH. Instale o MySQL Client e/ou defina MYSQLDUMP_PATH."
            ) from exc
        except subprocess.CalledProcessError as exc:
            raise CommandError(f"mysqldump (diff) falhou: {exc}") from exc

        key = f"{prefix}/{ts_name}.sql"

        try:
            s3.upload_file(
                Filename=str(sql_path),
                Bucket=bucket,
                Key=key,
                ExtraArgs={"ContentType": "application/sql"},
            )
            s3.put_object(Bucket=bucket, Key=marker_key, Body=now.isoformat().encode("utf-8"))
        except Exception as exc:
            raise CommandError(f"Falha no upload/marker S3: {exc}") from exc

        self.stdout.write(self.style.SUCCESS(f"Backup diferencial enviado para s3://{bucket}/{key}"))
