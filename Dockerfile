FROM python:3.13.18-slim-bookworm
WORKDIR /app
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1
COPY requirements-runtime.txt .
RUN pip install --no-cache-dir -r requirements-runtime.txt && useradd --uid 10001 --create-home library
COPY app app
COPY migrations migrations
COPY alembic.ini .
USER 10001
EXPOSE 8000
HEALTHCHECK --interval=15s --timeout=5s --retries=4 CMD python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8000/health',timeout=3)"
CMD ["python", "-m", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
