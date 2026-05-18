import json
import os
import uuid
from datetime import datetime, timezone
from typing import Any

import boto3
from botocore.client import Config


MINIO_ENDPOINT = os.getenv("MINIO_ENDPOINT", "minio-api:9000")
MINIO_ACCESS_KEY = os.getenv("MINIO_ACCESS_KEY")
MINIO_SECRET_KEY = os.getenv("MINIO_SECRET_KEY")
MINIO_RAW_BUCKET = os.getenv("MINIO_RAW_BUCKET", "raw")
MINIO_SECURE = os.getenv("MINIO_SECURE", "false").lower() == "true"


def get_s3_client():
    endpoint_url = f"{'https' if MINIO_SECURE else 'http'}://{MINIO_ENDPOINT}"

    return boto3.client(
        "s3",
        endpoint_url=endpoint_url,
        aws_access_key_id=MINIO_ACCESS_KEY,
        aws_secret_access_key=MINIO_SECRET_KEY,
        config=Config(signature_version="s3v4"),
        region_name="us-east-1",
    )


def upload_raw_event(event_type: str, payload: dict[str, Any]) -> str:
    """
    Uploads raw JSON event payloads to MinIO.

    Example object key:
    raw/metrics/2026/05/18/20260518T120000Z-uuid.json
    """

    now = datetime.now(timezone.utc)
    event_id = str(uuid.uuid4())

    object_key = (
        f"{event_type}/"
        f"{now.year:04d}/"
        f"{now.month:02d}/"
        f"{now.day:02d}/"
        f"{now.strftime('%Y%m%dT%H%M%SZ')}-{event_id}.json"
    )

    body = json.dumps(
        {
            "event_type": event_type,
            "ingested_at": now.isoformat(),
            "payload": payload,
        },
        ensure_ascii=False,
        indent=2,
    ).encode("utf-8")

    client = get_s3_client()
    client.put_object(
        Bucket=MINIO_RAW_BUCKET,
        Key=object_key,
        Body=body,
        ContentType="application/json",
    )

    return f"s3://{MINIO_RAW_BUCKET}/{object_key}"