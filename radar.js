let logArea = document.getElementById("log");
let radarCanvas = document.getElementById("radarCanvas");
let ctx = radarCanvas.getContext("2d");
let targets = [];
let map, markerLayer;

// Initialize map
window.onload = () => {
  map = L.map("map").setView([20.5937, 78.9629], 5);
  L.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png", {
    attribution: "© OpenStreetMap"
  }).addTo(map);
  markerLayer = L.layerGroup().addTo(map);
  log("System Initialized ✅");
};

// --- Logging function ---
function log(msg) {
  let time = new Date().toLocaleTimeString();
  logArea.innerHTML += `[${time}] ${msg}<br>`;
  logArea.scrollTop = logArea.scrollHeight;
}

// --- Simulated Scan ---
function scan() {
  log("Scanning environment...");
  targets = [];
  markerLayer.clearLayers();

  for (let i = 0; i < 8 + Math.floor(Math.random() * 3); i++) {
    let target = {
      id: i + 1,
      distance: (Math.random() * 200).toFixed(1),
      velocity: (Math.random() * 400).toFixed(1),
      lat: 20 + Math.random() * 10,
      lng: 78 + Math.random() * 10
    };
    targets.push(target);
    L.marker([target.lat, target.lng]).addTo(markerLayer)
      .bindPopup(`Target #${target.id}<br>Vel: ${target.velocity} m/s<br>Dist: ${target.distance} km`);
  }

  updateTable();
  animateRadar();
  updateSystemStatus();
  log(`${targets.length} targets detected.`);
}

// --- Animate radar sweep ---
function animateRadar() {
  let angle = 0;
  let radius = 230;

  let sweep = setInterval(() => {
    ctx.fillStyle = "#000";
    ctx.fillRect(0, 0, radarCanvas.width, radarCanvas.height);

    ctx.strokeStyle = "lime";
    ctx.lineWidth = 2;
    ctx.beginPath();
    ctx.arc(250, 250, radius, 0, 2 * Math.PI);
    ctx.stroke();

    ctx.save();
    ctx.translate(250, 250);
    ctx.rotate(angle * Math.PI / 180);
    ctx.strokeStyle = "lime";
    ctx.beginPath();
    ctx.moveTo(0, 0);
    ctx.lineTo(radius, 0);
    ctx.stroke();
    ctx.restore();

    angle += 3;
    if (angle >= 360) clearInterval(sweep);
  }, 30);
}

// --- Report download ---
function generateReport() {
  if (targets.length === 0) {
    log("No targets to report.");
    return;
  }

  let csv = "ID,Distance(km),Velocity(m/s)\n";
  targets.forEach(t => csv += `${t.id},${t.distance},${t.velocity}\n`);

  let blob = new Blob([csv], { type: "text/csv" });
  let a = document.createElement("a");
  a.href = URL.createObjectURL(blob);
  a.download = "radar_report.csv";
  a.click();

  log("Report downloaded as radar_report.csv");
}

// --- Analyze function ---
function analyze() {
  if (targets.length === 0) {
    log("No data to analyze.");
    return;
  }
  let maxSpeed = Math.max(...targets.map(t => t.velocity));
  let closest = Math.min(...targets.map(t => t.distance));
  log(`Analysis complete: Fastest ${maxSpeed} m/s, Closest ${closest} km.`);
}

// --- Update system status ---
function updateSystemStatus() {
  document.getElementById("activeTargets").textContent = targets.length;
  document.getElementById("wind").textContent = (10 + Math.random() * 20).toFixed(1) + " km/h";
  document.getElementById("weather").textContent = ["Clear", "Cloudy", "Rainy"][Math.floor(Math.random() * 3)];
  document.getElementById("cpuLoad").textContent = (30 + Math.random() * 60).toFixed(1) + "%";
  document.getElementById("temperature").textContent = (25 + Math.random() * 10).toFixed(1) + "°C";
}

// --- Table Update ---
function updateTable() {
  let tbody = document.getElementById("targetTable");
  tbody.innerHTML = "";
  targets.forEach(t => {
    tbody.innerHTML += `<tr><td>${t.id}</td><td>${t.distance}</td><td>${t.velocity}</td></tr>`;
  });
}

// --- Command Executor ---
function executeCommand() {
  let cmd = document.getElementById("commandInput").value.toLowerCase();
  if (cmd === "scan") scan();
  else if (cmd === "report") generateReport();
  else if (cmd === "analyze") analyze();
  else if (cmd === "clear") clearLogs();
  else showHelp();
}

// --- Help ---
function showHelp() {
  alert(`Available commands:\nscan - detect targets\nreport - download target data\nanalyze - run analytics\nclear - reset logs\nhelp - show this message`);
}

// --- Clear ---
function clearLogs() {
  logArea.innerHTML = "";
  ctx.clearRect(0, 0, radarCanvas.width, radarCanvas.height);
  markerLayer.clearLayers();
  targets = [];
  log("System reset.");
}

