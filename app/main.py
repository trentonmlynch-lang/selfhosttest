import logging
from pathlib import Path
from typing import Any

import docker
from docker.errors import DockerException
from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel


logger = logging.getLogger(__name__)
BASE_DIR = Path(__file__).resolve().parent

app = FastAPI(title="Unraid Command Center")
app.mount("/static", StaticFiles(directory=BASE_DIR / "static"), name="static")


class ContainerSummary(BaseModel):
    id: str
    name: str
    image: str
    status: str
    state: str
    created: str


class EngineSummary(BaseModel):
    name: str
    server_version: str
    operating_system: str
    containers: int
    running: int
    stopped: int
    images: int


class DashboardData(BaseModel):
    engine: EngineSummary
    containers: list[ContainerSummary]


@app.get("/", include_in_schema=False)
def home() -> FileResponse:
    return FileResponse(BASE_DIR / "static" / "index.html")


@app.get("/api/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/api/dashboard", response_model=DashboardData)
def dashboard() -> DashboardData:
    client = None
    try:
        client = docker.from_env()
        info: dict[str, Any] = client.info()
        containers = client.containers.list(all=True)
    except (DockerException, OSError) as exc:
        logger.exception("Unable to read Docker Engine dashboard data")
        raise HTTPException(
            status_code=503,
            detail="Docker Engine is unavailable. Check that the Docker socket is mounted and accessible.",
        ) from exc
    finally:
        if client is not None:
            client.close()

    container_summaries = [
        ContainerSummary(
            id=container.short_id,
            name=container.name,
            image=container.attrs.get("Config", {}).get("Image", container.image.short_id),
            status=container.status,
            state=container.attrs.get("State", {}).get("Status", container.status),
            created=container.attrs.get("Created", ""),
        )
        for container in containers
    ]
    running = int(info.get("ContainersRunning", 0))
    stopped = int(info.get("ContainersStopped", 0))

    return DashboardData(
        engine=EngineSummary(
            name=info.get("Name", "Docker Engine"),
            server_version=info.get("ServerVersion", "Unknown"),
            operating_system=info.get("OperatingSystem", "Unknown"),
            containers=int(info.get("Containers", len(containers))),
            running=running,
            stopped=stopped,
            images=int(info.get("Images", 0)),
        ),
        containers=container_summaries,
    )
