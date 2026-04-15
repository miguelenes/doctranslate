"""Locust load scenarios for the DocTranslater HTTP API (nightly / local).

Run after starting the API, for example::

    DOCTRANSLATE_API_DATA_ROOT=/tmp/api-data \\
    DOCTRANSLATE_API_AUTH_MODE=disabled \\
    uv run uvicorn doctranslate.http_api.app:app --host 127.0.0.1 --port 8999

    uv run locust -f benchmarks/load/locustfile.py --headless -u 4 -r 1 -t 20s \\
      --host http://127.0.0.1:8999
"""

from __future__ import annotations

import os

from locust import HttpUser
from locust import between
from locust import task


class ApiUser(HttpUser):
    wait_time = between(0.5, 2.0)

    @task(3)
    def health(self) -> None:
        self.client.get("/health")

    @task(1)
    def metrics(self) -> None:
        self.client.get("/metrics")

    @task(1)
    def openapi(self) -> None:
        self.client.get("/openapi.json")

    @task(1)
    def inspect_minimal(self) -> None:
        pdf = os.environ.get("PERF_INSPECT_PDF", "")
        if not pdf:
            return
        self.client.post("/v1/inspect", json={"paths": [pdf]})
