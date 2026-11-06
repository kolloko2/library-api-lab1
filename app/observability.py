import json
import logging
import time
import uuid

from prometheus_client import CONTENT_TYPE_LATEST, Counter, Histogram, Gauge, generate_latest
from sqlalchemy import select, func
from sqlalchemy.exc import SQLAlchemyError
from app.database import get_db
from fastapi import Depends
from app.models import Loan
from starlette.responses import Response

REQUESTS = Counter("library_requests_total", "HTTP requests", ["method", "route", "status"])
LATENCY = Histogram("library_request_seconds", "HTTP latency", ["route"])
LOG = logging.getLogger("library.requests")
LOG.setLevel(logging.INFO)
if not LOG.handlers:
    LOG.addHandler(logging.StreamHandler())
LOG.propagate = False
ACTIVE_LOANS = Gauge("library_active_loans", "Current active book loans")
DATABASE_UP = Gauge("library_database_up", "Database query succeeded on the latest scrape")


def install_observability(app):
    @app.middleware("http")
    async def observe(request, call_next):
        request_id = str(uuid.uuid4())
        started = time.monotonic()
        status = 500
        try:
            response = await call_next(request)
            status = response.status_code
            response.headers["X-Request-ID"] = request_id
            return response
        finally:
            route = getattr(request.scope.get("route"), "path", "unmatched")
            elapsed = time.monotonic() - started
            REQUESTS.labels(request.method, route, str(status)).inc()
            LATENCY.labels(route).observe(elapsed)
            LOG.log(
                logging.ERROR if status >= 500 else logging.INFO,
                json.dumps(
                    {
                        "time": time.time(),
                        "level": "ERROR" if status >= 500 else "INFO",
                        "event": "http_request",
                        "route": route,
                        "status": status,
                        "duration_seconds": elapsed,
                        "request_id": request_id,
                    }
                ),
            )

    @app.get("/metrics", include_in_schema=False)
    def metrics(db=Depends(get_db)):
        try:
            active = db.scalar(select(func.count(Loan.id)).where(Loan.returned_at.is_(None)))
        except SQLAlchemyError:
            db.rollback()
            DATABASE_UP.set(0)
            ACTIVE_LOANS.set(float("nan"))
        else:
            DATABASE_UP.set(1)
            ACTIVE_LOANS.set(active)
        return Response(generate_latest(), headers={"Content-Type": CONTENT_TYPE_LATEST})
