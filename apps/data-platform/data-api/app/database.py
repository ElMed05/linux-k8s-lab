import os
import psycopg2
from psycopg2.extras import RealDictCursor


def get_connection():
    return psycopg2.connect(
        host=os.getenv("DB_HOST", "postgres"),
        port=os.getenv("DB_PORT", "5432"),
        dbname=os.getenv("DB_NAME", "dataplatform"),
        user=os.getenv("DB_USER", "dataplatform"),
        password=os.getenv("DB_PASSWORD", "dataplatform"),
        cursor_factory=RealDictCursor,
    )


def init_db():
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
        CREATE TABLE IF NOT EXISTS services (
            id SERIAL PRIMARY KEY,
            service_name VARCHAR(100) UNIQUE NOT NULL,
            team VARCHAR(100) NOT NULL,
            environment VARCHAR(50) NOT NULL,
            criticality VARCHAR(50) NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS service_metrics (
            id SERIAL PRIMARY KEY,
            service_name VARCHAR(100) NOT NULL,
            timestamp TIMESTAMP NOT NULL,
            cpu_usage NUMERIC(5,2) NOT NULL,
            memory_usage NUMERIC(5,2) NOT NULL,
            response_time_ms INTEGER NOT NULL,
            request_count INTEGER NOT NULL,
            error_rate NUMERIC(5,2) NOT NULL
        );
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS incidents (
            id SERIAL PRIMARY KEY,
            service_name VARCHAR(100) NOT NULL,
            timestamp TIMESTAMP NOT NULL,
            severity VARCHAR(50) NOT NULL,
            incident_type VARCHAR(100) NOT NULL,
            duration_minutes INTEGER NOT NULL,
            resolved BOOLEAN NOT NULL
        );
    """)

    conn.commit()
    cur.close()
    conn.close()