# Unraid Command Center

A lightweight, read-only dashboard for the Docker Engine on an Unraid server. It shows container and image counts, host details, and the status of each container. The dashboard refreshes automatically every 30 seconds.

## Deploy on Unraid

1. Install the Docker Compose Manager plugin if Compose is not already available.
2. Copy this project folder to your Unraid server (for example, `/boot/config/plugins/compose.manager/projects/unraid-command-center`) or clone it there.
3. In the Unraid terminal, find the numeric group ID for the Docker socket:

   ```sh
   stat -c '%g' /var/run/docker.sock
   ```

4. In the project folder, create a `.env` file containing that numeric ID:

   ```env
   DOCKER_GID=281
   ```

   Replace `281` with the value returned on your server. This grants the app's unprivileged user access to the Docker socket.
5. Start the project:

   ```sh
   docker compose up -d --build
   ```

6. Open `http://<UNRAID-SERVER-IP>:8000` in your browser. Check logs with `docker compose logs -f`.

To stop the app, run `docker compose down` from the project folder. To update it after changing files, run `docker compose up -d --build`.

## Local development and tests

Python 3.10 or later is required.

```sh
python -m venv .venv
# Windows: .venv\Scripts\Activate.ps1
# Linux/macOS: source .venv/bin/activate
python -m pip install -r requirements-dev.txt
uvicorn app.main:app --reload
```

The dashboard API reads Docker Engine information through `/var/run/docker.sock`. On a development machine without an accessible Docker socket, the homepage and health check still work; the dashboard API responds with `503 Service Unavailable`.

Run the tests with:

```sh
python -m pytest
```

## Security

The dashboard exposes Docker host and container metadata and intentionally provides no container controls. Keep port `8000` on a trusted network; do not expose this service directly to the public internet. Access to the Docker socket is highly privileged even though the application only makes read-only Docker API requests.
