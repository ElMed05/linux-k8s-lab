from fastapi import FastAPI, HTTPException
from app.database import get_connection, init_db
from app.models import ServiceCreate, MetricCreate, IncidentCreate

app = FastAPI(
    title="Data Platform API",
    description="Ingestion API for service operations and platform intelligence data.",
    version="0.1.0",
)


@app.on_event("startup")
def startup():
    init_db()


@app.get("/health")
def health():
    return {"status": "healthy", "service": "data-api"}


@app.post("/services")
def create_service(payload: ServiceCreate):
    conn = get_connection()
    cur = conn.cursor()

    try:
        cur.execute(
            """
            INSERT INTO services (service_name, team, environment, criticality)
            VALUES (%s, %s, %s, %s)
            ON CONFLICT (service_name) DO UPDATE SET
                team = EXCLUDED.team,
                environment = EXCLUDED.environment,
                criticality = EXCLUDED.criticality
            RETURNING *;
            """,
            (
                payload.service_name,
                payload.team,
                payload.environment,
                payload.criticality,
            ),
        )
        service = cur.fetchone()
        conn.commit()
        return service
    finally:
        cur.close()
        conn.close()


@app.get("/services")
def list_services():
    conn = get_connection()
    cur = conn.cursor()

    try:
        cur.execute("SELECT * FROM services ORDER BY service_name;")
        return cur.fetchall()
    finally:
        cur.close()
        conn.close()


@app.post("/metrics")
def create_metric(payload: MetricCreate):
    conn = get_connection()
    cur = conn.cursor()

    try:
        cur.execute(
            """
            INSERT INTO service_metrics (
                service_name,
                timestamp,
                cpu_usage,
                memory_usage,
                response_time_ms,
                request_count,
                error_rate
            )
            VALUES (%s, %s, %s, %s, %s, %s, %s)
            RETURNING *;
            """,
            (
                payload.service_name,
                payload.timestamp,
                payload.cpu_usage,
                payload.memory_usage,
                payload.response_time_ms,
                payload.request_count,
                payload.error_rate,
            ),
        )
        metric = cur.fetchone()
        conn.commit()
        return metric
    finally:
        cur.close()
        conn.close()


@app.post("/incidents")
def create_incident(payload: IncidentCreate):
    conn = get_connection()
    cur = conn.cursor()

    try:
        cur.execute(
            """
            INSERT INTO incidents (
                service_name,
                timestamp,
                severity,
                incident_type,
                duration_minutes,
                resolved
            )
            VALUES (%s, %s, %s, %s, %s, %s)
            RETURNING *;
            """,
            (
                payload.service_name,
                payload.timestamp,
                payload.severity,
                payload.incident_type,
                payload.duration_minutes,
                payload.resolved,
            ),
        )
        incident = cur.fetchone()
        conn.commit()
        return incident
    finally:
        cur.close()
        conn.close()


@app.get("/metrics/summary")
def metrics_summary():
    conn = get_connection()
    cur = conn.cursor()

    try:
        cur.execute(
            """
            SELECT
                service_name,
                ROUND(AVG(cpu_usage), 2) AS avg_cpu_usage,
                ROUND(AVG(memory_usage), 2) AS avg_memory_usage,
                ROUND(AVG(response_time_ms), 2) AS avg_response_time_ms,
                ROUND(AVG(error_rate), 2) AS avg_error_rate,
                SUM(request_count) AS total_requests,
                COUNT(*) AS metric_count
            FROM service_metrics
            GROUP BY service_name
            ORDER BY avg_error_rate DESC;
            """
        )
        return cur.fetchall()
    finally:
        cur.close()
        conn.close()


@app.get("/incidents/summary")
def incidents_summary():
    conn = get_connection()
    cur = conn.cursor()

    try:
        cur.execute(
            """
            SELECT
                service_name,
                severity,
                COUNT(*) AS incident_count,
                ROUND(AVG(duration_minutes), 2) AS avg_duration_minutes
            FROM incidents
            GROUP BY service_name, severity
            ORDER BY incident_count DESC;
            """
        )
        return cur.fetchall()
    finally:
        cur.close()
        conn.close()