from unittest.mock import Mock, patch

from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


def test_home_serves_dashboard() -> None:
    response = client.get("/")

    assert response.status_code == 200
    assert "Unraid Command Center" in response.text
    assert "/static/app.js" in response.text
    assert "/static/styles.css" in response.text


def test_static_dashboard_assets_are_served() -> None:
    script = client.get("/static/app.js")
    stylesheet = client.get("/static/styles.css")

    assert script.status_code == 200
    assert "loadDashboard" in script.text
    assert stylesheet.status_code == 200
    assert "--bg: #0a0d12" in stylesheet.text


def test_health_reports_ok() -> None:
    response = client.get("/api/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_dashboard_returns_engine_and_container_summaries() -> None:
    docker_client = Mock()
    docker_client.info.return_value = {
        "Name": "tower",
        "ServerVersion": "27.5.1",
        "OperatingSystem": "Unraid",
        "Containers": 2,
        "ContainersRunning": 1,
        "ContainersStopped": 1,
        "Images": 8,
    }
    container = Mock()
    container.short_id = "abc123"
    container.name = "media-server"
    container.status = "Up 2 hours"
    container.attrs = {
        "Config": {"Image": "example/media:latest"},
        "State": {"Status": "running"},
        "Created": "2026-01-01T00:00:00Z",
    }
    docker_client.containers.list.return_value = [container]

    with patch("app.main.docker.from_env", return_value=docker_client):
        response = client.get("/api/dashboard")

    assert response.status_code == 200
    assert response.json() == {
        "engine": {
            "name": "tower",
            "server_version": "27.5.1",
            "operating_system": "Unraid",
            "containers": 2,
            "running": 1,
            "stopped": 1,
            "images": 8,
        },
        "containers": [
            {
                "id": "abc123",
                "name": "media-server",
                "image": "example/media:latest",
                "status": "Up 2 hours",
                "state": "running",
                "created": "2026-01-01T00:00:00Z",
            }
        ],
    }
    docker_client.close.assert_called_once_with()


def test_dashboard_reports_unavailable_docker_engine() -> None:
    with patch("app.main.docker.from_env", side_effect=OSError("socket unavailable")):
        response = client.get("/api/dashboard")

    assert response.status_code == 503
    assert "Docker Engine is unavailable" in response.json()["detail"]
