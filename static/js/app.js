let timelineChart = null;

function setStatusBadge(connected) {
  const badge = document.getElementById("statusBadge");
  badge.textContent = connected ? "LIVE" : "OFFLINE";
  badge.className = connected
    ? "badge rounded-pill text-bg-success px-3 py-2"
    : "badge rounded-pill text-bg-danger px-3 py-2";
}

function renderTimeline(timeline) {
  const canvasId = "timelineCanvas";
  const chartBox = document.getElementById("timelineChart");
  chartBox.innerHTML = `<canvas id="${canvasId}"></canvas>`;

  const ctx = document.getElementById(canvasId);

  const labels = timeline.map(item => item.time);
  const values = timeline.map(item => item.count);

  if (timelineChart) {
    timelineChart.destroy();
  }

  timelineChart = new Chart(ctx, {
    type: "line",
    data: {
      labels,
      datasets: [{
        label: "Events",
        data: values,
        borderWidth: 2,
        tension: 0.35,
        fill: true
      }]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      plugins: {
        legend: {
          labels: { color: "#c9d1d9" }
        }
      },
      scales: {
        x: {
          ticks: { color: "#8b949e" },
          grid: { color: "#30363d" }
        },
        y: {
          ticks: { color: "#8b949e" },
          grid: { color: "#30363d" }
        }
      }
    }
  });
}

function renderTopIps(topIps) {
  const container = document.getElementById("topIpsList");
  container.innerHTML = "";

  if (!topIps.length) {
    container.innerHTML = `
      <div class="list-group-item text-secondary">No source IP data available.</div>
    `;
    return;
  }

  topIps.forEach(item => {
    const row = document.createElement("div");
    row.className = "list-group-item d-flex justify-content-between align-items-center";
    row.innerHTML = `
      <span class="badge ip-badge">${item.ip}</span>
      <span class="fw-semibold">${item.count}</span>
    `;
    container.appendChild(row);
  });
}

function renderAlerts(alerts) {
  const tbody = document.getElementById("alertsTableBody");
  tbody.innerHTML = "";

  if (!alerts.length) {
    tbody.innerHTML = `
      <tr>
        <td colspan="5" class="text-center text-secondary">No alerts found.</td>
      </tr>
    `;
    return;
  }

  alerts.forEach(alert => {
    const tr = document.createElement("tr");
    const time = alert.timestamp ? alert.timestamp.slice(0, 19).replace("T", " ") : "—";

    tr.innerHTML = `
      <td class="font-monospace">${time}</td>
      <td><span class="badge text-bg-secondary">${alert.severity_label}</span></td>
      <td class="font-monospace text-info">${alert.source_ip}</td>
      <td class="font-monospace">${alert.destination_port}</td>
      <td>${alert.rule_name}</td>
    `;
    tbody.appendChild(tr);
  });
}

async function loadDashboard() {
  try {
    const response = await fetch("/api/dashboard");
    const result = await response.json();

    const data = result.data || {};

    setStatusBadge(Boolean(data.connected));

    document.getElementById("totalAlerts").textContent = data.total_alerts ?? 0;
    document.getElementById("criticalCount").textContent = data.critical ?? 0;
    document.getElementById("highCount").textContent = data.high ?? 0;
    document.getElementById("mediumCount").textContent = data.medium ?? 0;

    renderTimeline(data.timeline || []);
    renderTopIps(data.top_ips || []);
    renderAlerts(data.recent_alerts || []);

    document.getElementById("footerInfo").textContent =
      `ES ${data.es_version || "-"} | Index: ${data.active_index_pattern || "-"} | ` +
      `Indices: ${data.index_count || 0} | Update: ${data.last_update || "-"} | ` +
      `${data.status || "Unknown"}`;
  } catch (error) {
    setStatusBadge(false);
    document.getElementById("footerInfo").textContent = `Failed to load dashboard: ${error}`;
  }
}

loadDashboard();
setInterval(loadDashboard, 15000);