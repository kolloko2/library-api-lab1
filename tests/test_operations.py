import os
import sqlite3
import subprocess
import sys


def test_migrations_preserve_data_and_backup(tmp_path):
    db = tmp_path / "source.db"
    backup = tmp_path / "backup.db"
    env = dict(os.environ, DATABASE_URL=f"sqlite:///{db}")
    subprocess.run([sys.executable, "-m", "alembic", "upgrade", "001"], env=env, check=True)
    connection = sqlite3.connect(db)
    connection.execute("INSERT INTO authors (id,name) VALUES (1,'Preserved author')")
    connection.commit()
    connection.close()
    subprocess.run([sys.executable, "-m", "alembic", "upgrade", "head"], env=env, check=True)
    subprocess.run([sys.executable, "scripts/database.py", "backup", str(backup)], env=env, check=True)
    connection = sqlite3.connect(db)
    connection.execute("DELETE FROM authors")
    connection.commit()
    connection.close()
    subprocess.run([sys.executable, "scripts/database.py", "restore", str(backup)], env=env, check=True)
    connection = sqlite3.connect(db)
    assert connection.execute("SELECT name FROM authors").fetchone()[0] == "Preserved author"
    assert connection.execute("SELECT version_num FROM alembic_version").fetchone()[0] == "004"
    connection.close()


def test_version_request_id_and_metrics(client):
    response = client.get("/version")
    assert response.status_code == 200
    assert response.json()["version"]
    assert response.headers["X-Request-ID"]
    metrics = client.get("/metrics")
    assert metrics.status_code == 200
    assert "library_requests_total" in metrics.text
    assert "library_database_up 1.0" in metrics.text


def test_metrics_remain_available_when_database_fails(client):
    from unittest.mock import Mock

    from sqlalchemy.exc import OperationalError

    from app.database import get_db
    from app.main import app

    broken = Mock()
    broken.scalar.side_effect = OperationalError("SELECT", {}, RuntimeError("database offline"))
    healthy_override = app.dependency_overrides[get_db]
    app.dependency_overrides[get_db] = lambda: broken
    try:
        metrics = client.get("/metrics")
        assert metrics.status_code == 200
        assert "library_database_up 0.0" in metrics.text
        assert "library_active_loans NaN" in metrics.text
        broken.rollback.assert_called_once()
    finally:
        app.dependency_overrides[get_db] = healthy_override
    recovered = client.get("/metrics")
    assert "library_database_up 1.0" in recovered.text
