import json
import os
from datetime import datetime, timezone
from decimal import Decimal
from typing import Any

import boto3
import psycopg2
from botocore.client import Config
from psycopg2.extras import RealDictCursor


DB_HOST = os.getenv("DB_HOST", "postgres")
DB_PORT = int(os.getenv("DB_PORT", "5432"))
DB_NAME = os.getenv("DB_NAME", "dataplatform")
DB_USER = os.getenv("DB_USER", "dataplatform")
DB_PASSWORD = os.getenv("DB_PASSWORD")

MINIO_ENDPOINT = os.getenv("MINIO_ENDPOINT", "minio-api:9000")
MINIO_ACCESS_KEY = os.getenv("MINIO_ACCESS_KEY")
MINIO_SECRET_KEY = os.getenv("MINIO_SECRET_KEY")
MINIO_PROCESSED_BUCKET = os.getenv("MINIO_PROCESSED_BUCKET", "processed")
MINIO_SECURE = os.getenv("MINIO_SECURE", "false").lower() == "true"


def decimal_to_float(value: Any) -> Any:
    if isinstance(value, Decimal):
        return float(value)
    return value


def get_db_connection():
    return psycopg2.connect(
        host=DB_HOST,
        port=DB_PORT,
        dbname=DB_NAME,
        user=DB_USER,
        password=DB_PASSWORD,
        cursor_factory=RealDictCursor,
    )


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


def calculate_summary(conn):
    query = """
        WITH metric_summary AS (
            SELECT
                service_name,
                ROUND(AVG(cpu_usage), 2) AS avg_cpu_usage,
                ROUND(AVG(memory_usage), 2) AS avg_memory_usage,
                ROUND(AVG(response_time_ms), 2) AS avg_response_time_ms,
                ROUND(AVG(error_rate), 2) AS avg_error_rate,
                SUM(request_count) AS total_requests
            FROM service_metrics
            GROUP BY service_name
        ),
        incident_summary AS (
            SELECT
                service_name,
                COUNT(*) AS incident_count
            FROM incidents
            GROUP BY service_name
        )
        SELECT
            m.service_name,
            m.avg_cpu_usage,
            m.avg_memory_usage,
            m.avg_response_time_ms,
            m.avg_error_rate,
            m.total_requests,
            COALESCE(i.incident_count, 0) AS incident_count,
            ROUND(
                100
                - (m.avg_error_rate * 5)
                - (m.avg_response_time_ms / 20)
                - (m.avg_cpu_usage / 10)
                - (COALESCE(i.incident_count, 0) * 0.5),
                2
            ) AS health_score
        FROM metric_summary m
        LEFT JOIN incident_summary i
            ON m.service_name = i.service_name
        ORDER BY health_score ASC;
    """

    with conn.cursor() as cur:
        cur.execute(query)
        return cur.fetchall()


def store_summary(conn, rows):
    with conn.cursor() as cur:
        cur.execute("DELETE FROM service_health_summary;")

        for row in rows:
            cur.execute(
                """
                INSERT INTO service_health_summary (
                    service_name,
                    avg_cpu_usage,
                    avg_memory_usage,
                    avg_response_time_ms,
                    avg_error_rate,
                    total_requests,
                    incident_count,
                    health_score,
                    calculated_at
                )
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, NOW());
                """,
                (
                    row["service_name"],
                    row["avg_cpu_usage"],
                    row["avg_memory_usage"],
                    row["avg_response_time_ms"],
                    row["avg_error_rate"],
                    row["total_requests"],
                    row["incident_count"],
                    row["health_score"],
                ),
            )

    conn.commit()


def upload_processed_summary(rows):
    now = datetime.now(timezone.utc)
    object_key = (
        f"service_health_summary/"
        f"{now.year:04d}/"
        f"{now.month:02d}/"
        f"{now.day:02d}/"
        f"{now.strftime('%Y%m%dT%H%M%SZ')}.json"
    )

    payload = {
        "dataset": "service_health_summary",
        "calculated_at": now.isoformat(),
        "records": [
            {key: decimal_to_float(value) for key, value in dict(row).items()}
            for row in rows
        ],
    }

    client = get_s3_client()
    client.put_object(
        Bucket=MINIO_PROCESSED_BUCKET,
        Key=object_key,
        Body=json.dumps(payload, indent=2).encode("utf-8"),
        ContentType="application/json",
    )

    return f"s3://{MINIO_PROCESSED_BUCKET}/{object_key}"


def main():
    print("Starting data processing job...")

    conn = get_db_connection()

    try:
        rows = calculate_summary(conn)
        print(f"Calculated {len(rows)} service health records.")

        store_summary(conn, rows)
        print("Stored service health summary in PostgreSQL.")

        object_path = upload_processed_summary(rows)
        print(f"Uploaded processed summary to {object_path}")

    finally:
        conn.close()

    print("Data processing job finished.")


if __name__ == "__main__":
    main()