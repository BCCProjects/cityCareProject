from __future__ import annotations

from django.utils.deconstruct import deconstructible
from django.conf import settings
from storages.backends.s3boto3 import S3Boto3Storage


@deconstructible
class AttachmentStorage(S3Boto3Storage):
    location = getattr(settings, "SUPABASE_ATTACHMENT_PREFIX", "reportImages")
    default_acl = "public-read"
    file_overwrite = False

