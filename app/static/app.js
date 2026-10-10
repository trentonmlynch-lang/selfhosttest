const refreshButton = document.querySelector("#refresh-button");
const errorMessage = document.querySelector("#error-message");

function setText(selector, value) {
  document.querySelector(selector).textContent = value;
}

function showError(message) {
  errorMessage.textContent = message;
  errorMessage.hidden = false;
  setText("#sidebar-status", "Connection issue");
  document.querySelector("#sidebar-status-dot").classList.remove("online");
  document.querySelector("#container-list").innerHTML =
    '<tr><td class="table-message" colspan="3">Unable to load containers. Check the Docker Engine connection.</td></tr>';
  setText("#container-summary", "Unavailable");
}

function renderContainers(containers) {
  const containerList = document.querySelector("#container-list");
  if (containers.length === 0) {
    containerList.innerHTML =
      '<tr><td class="table-message" colspan="3">No containers found on this host.</td></tr>';
    return;
  }

  containerList.replaceChildren();
  for (const container of containers) {
    const row = document.createElement("tr");
    const nameCell = document.createElement("td");
    const name = document.createElement("span");
    const indicator = document.createElement("i");
    name.className = "container-name";
    if (container.state === "running") indicator.className = "running";
    name.textContent = container.name;
    name.prepend(indicator);
    nameCell.append(name);

    const imageCell = document.createElement("td");
    imageCell.title = container.image;
    imageCell.textContent = container.image;

    const statusCell = document.createElement("td");
    const status = document.createElement("span");
    status.className = `state-pill${container.state === "running" ? " running" : ""}`;
    const statusDot = document.createElement("i");
    const statusLabel = document.createElement("span");
    statusLabel.textContent = container.status;
    status.append(statusDot, statusLabel);
    statusCell.append(status);

    row.append(nameCell, imageCell, statusCell);
    containerList.append(row);
  }
}

async function loadDashboard() {
  refreshButton.disabled = true;
  refreshButton.querySelector("svg").classList.add("spin");
  try {
    const response = await fetch("/api/dashboard", { headers: { Accept: "application/json" } });
    if (!response.ok) {
      const body = await response.json();
      throw new Error(body.detail || `Request failed (${response.status})`);
    }
    const data = await response.json();
    const { engine, containers } = data;

    setText("#running-count", engine.running);
    setText("#stopped-count", engine.stopped);
    setText("#total-count", engine.containers);
    setText("#image-count", engine.images);
    setText("#nav-container-count", engine.containers);
    setText("#host-name", engine.name);
    setText("#detail-host-name", engine.name);
    setText("#operating-system", engine.operating_system);
    setText("#engine-version", `Docker Engine ${engine.server_version}`);
    setText("#detail-engine-version", engine.server_version);
    setText("#container-summary", `${engine.running} running`);
    setText("#sidebar-status", "Connected");
    document.querySelector("#sidebar-status-dot").classList.add("online");
    setText("#last-updated", `Updated ${new Date().toLocaleTimeString([], { hour: "numeric", minute: "2-digit" })}`);
    errorMessage.hidden = true;
    renderContainers(containers);
  } catch (error) {
    showError(error.message || "Unable to connect to Docker Engine.");
  } finally {
    refreshButton.disabled = false;
    refreshButton.querySelector("svg").classList.remove("spin");
  }
}

refreshButton.addEventListener("click", loadDashboard);
loadDashboard();
window.setInterval(loadDashboard, 30_000);
