import os
import random
from datetime import datetime, timezone

import requests


API_BASE_URL = os.getenv("API_BASE_URL", "http://data-api:8000")

SERVICES = [
    {
        "service_name": "checkout-api",
        "team": "commerce",
        "environment": "prod",
        "criticality": "high",
    },
    {
        "service_name": "payment-api",
        "team": "commerce",
        "environment": "prod",
        "criticality": "critical",
    },
    {
        "service_name": "inventory-service",
        "team": "supply-chain",
        "environment": "prod",
        "criticality": "medium",
    },
    {
        "service_name": "user-service",
        "team": "identity",
        "environment": "prod",
        "criticality": "high",
    },
    {
        "service_name": "notification-service",
        "team": "platform",
        "environment": "prod",
        "criticality": "low",
    },
]


def post(path: str, payload: dict) -> None:
    url = f"{API_BASE_URL}{path}"
    response = requests.post(url, json=payload, timeout=10)
    response.raise_for_status()


def create_or_update_services() -> None:
    for service in SERVICES:
        post("/services", service)


def generate_metric(service_name: str) -> dict:
    error_rate = round(random.uniform(0.0, 5.0), 2)

    # Simulate worse behavior for payment-api sometimes
    if service_name == "payment-api" and random.random() < 0.25:
        error_rate = round(random.uniform(5.0, 15.0), 2)

    return {
        "service_name": service_name,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "cpu_usage": round(random.uniform(10.0, 90.0), 2),
        "memory_usage": round(random.uniform(20.0, 95.0), 2),
        "response_time_ms": random.randint(50, 900),
        "request_count": random.randint(100, 5000),
        "error_rate": error_rate,
    }


def generate_incident(service_name: str) -> dict:
    severities = ["low", "medium", "high", "critical"]
    incident_types = [
        "high_latency",
        "increased_error_rate",
        "pod_restart",
        "database_timeout",
        "dependency_failure",
    ]

    return {
        "service_name": service_name,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "severity": random.choice(severities),
        "incident_type": random.choice(incident_types),
        "duration_minutes": random.randint(3, 60),
        "resolved": random.choice([True, True, True, False]),
    }


def main() -> None:
    print("Starting data generation...")
    create_or_update_services()

    for service in SERVICES:
        service_name = service["service_name"]

        metric = generate_metric(service_name)
        post("/metrics", metric)
        print(f"Metric sent for {service_name}")

        # Not every run should create incidents
        if random.random() < 0.25:
            incident = generate_incident(service_name)
            post("/incidents", incident)
            print(f"Incident sent for {service_name}")

    print("Data generation finished.")


if __name__ == "__main__":
    main()