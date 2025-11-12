from __future__ import annotations

import gzip
import os
import shlex
import shutil
import subprocess
from datetime import datetime, timezone as dt_timezone
from pathlib import Path

import boto3
from botocore.client import Config
from django.core.management import CommandError
from django.conf import settings
from django.core.management.base import BaseCommand
from functools import lru_cache


@lru_cache(maxsize=None)
def _mysqldump_supports_ssl_mode(bin_path: str) -> bool:
    try:
        result = subprocess.run(
            [bin_path, "--help"],
            capture_output=True,
            text=True,
            check=False,
        )
    except Exception:
        return False
    return "--ssl-mode" in result.stdout


class Command(BaseCommand):
    help = "Realiza backup completo do banco de dados e envia para Supabase S3."

    def handle(self, *args, **options):  # type: ignore[override]
        now = datetime.now(dt_timezone.utc)
        ts_name = now.strftime("%Y-%m-%d_%H%M%S")

        endpoint = settings.BACKUP_S3_ENDPOINT_URL
        access_key = settings.BACKUP_S3_ACCESS_KEY_ID
        secret_key = settings.BACKUP_S3_SECRET_ACCESS_KEY
        bucket = settings.BACKUP_S3_BUCKET
        region = settings.BACKUP_S3_REGION or "us-east-1"
        prefix = settings.BACKUP_COMPLETE_PREFIX

        if not (endpoint and access_key and secret_key and bucket):
            raise CommandError("Config S3 de backup incompleta. Verifique endpoint/keys/bucket.")

        tmp_dir = Path(settings.BASE_DIR) / "_tmp_backups"
        tmp_dir.mkdir(exist_ok=True)

        db = settings.DATABASES["default"]
        engine = db["ENGINE"]

        out_file: Path
        content_type = "application/gzip"

        if engine.endswith("sqlite3"):
            db_path = Path(db["NAME"]).resolve()
            raw_path = tmp_dir / f"sqlite_full_{ts_name}.sqlite3"
            shutil.copy2(db_path, raw_path)
            gz_path = raw_path.with_suffix(raw_path.suffix + ".gz")
            with open(raw_path, "rb") as f_in, gzip.open(gz_path, "wb", compresslevel=6) as f_out:
                shutil.copyfileobj(f_in, f_out)
            out_file = gz_path
        elif engine.endswith("mysql"):
            host = db.get("HOST", "localhost")
            port = str(db.get("PORT", "3306"))
            user = db.get("USER")
            password = db.get("PASSWORD")
            name = db.get("NAME")
            ssl_mode = (
                os.getenv("MYSQL_SSL_MODE")
                or os.getenv("MYSQLDUMP_SSL_MODE")
                or db.get("OPTIONS", {}).get("ssl_mode")
            )
            extra_args_raw = os.getenv("MYSQLDUMP_EXTRA_ARGS", "")
            extra_args = shlex.split(extra_args_raw) if extra_args_raw.strip() else []
            if not all([user, name]):
                self.stderr.write(self.style.ERROR("Config MySQL incompleta para backup."))
                return
            sql_path = tmp_dir / f"mysql_full_{ts_name}.sql"
            mysqldump_path = (
                os.getenv("MYSQLDUMP_PATH")
                or shutil.which("mysqldump")
                or shutil.which("mariadb-dump")
                or "mysqldump"
            )
            cmd = [
                mysqldump_path,
                "-h",
                host,
                "-P",
                port,
                "-u",
                user,
                f"-p{password}" if password else "",
                "--single-transaction",
                "--routines",
                "--events",
                "--triggers",
                name,
            ]
            if ssl_mode:
                normalized_mode = ssl_mode.strip().upper()
                supports_ssl_mode = _mysqldump_supports_ssl_mode(mysqldump_path)
                if normalized_mode == "DISABLED":
                    cmd.extend(["--skip-ssl", "--skip-ssl-verify-server-cert"])
                elif supports_ssl_mode:
                    cmd.extend(["--ssl-mode", normalized_mode])
                else:
                    self.stderr.write(
                        self.style.WARNING(
                            "MYSQL_SSL_MODE configurado, mas o mysqldump atual não suporta --ssl-mode. "
                            "Use MYSQLDUMP_EXTRA_ARGS para repassar flags compatíveis (ex.: --ssl-ca, --skip-ssl)."
                        )
                    )
            if extra_args:
                cmd.extend(extra_args)
            cmd = [c for c in cmd if c != ""]
            try:
                with open(sql_path, "wb") as f_out:
                    subprocess.run(cmd, check=True, stdout=f_out)
            except FileNotFoundError as exc:
                raise CommandError(
                    "mysqldump não encontrado no PATH. Instale o MySQL Client e/ou defina MYSQLDUMP_PATH."
                ) from exc
            except subprocess.CalledProcessError as exc:
                raise CommandError(f"mysqldump falhou: {exc}") from exc
            out_file = sql_path
            content_type = "application/sql"
        else:
            raise CommandError(f"Engine não suportado: {engine}")

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
            key = f"{prefix}/{ts_name}{out_file.suffix}"
            s3.upload_file(
                Filename=str(out_file),
                Bucket=bucket,
                Key=key,
                ExtraArgs={"ContentType": content_type},
            )
        except Exception as exc:
            raise CommandError(f"Falha no upload S3: {exc}") from exc

        self.stdout.write(self.style.SUCCESS(f"Backup completo enviado para s3://{bucket}/{key}"))
