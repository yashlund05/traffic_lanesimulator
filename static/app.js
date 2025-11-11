const lanesContainer = document.getElementById("lanes");
const laneSelect = document.getElementById("lane-select");
const vehicleType = document.getElementById("veh-type");
const logList = document.getElementById("log-list");
const explainBox = document.getElementById("explain-box");

const btnEnq = document.getElementById("btn-enq");
const btnDeq = document.getElementById("btn-deq");
const btnStart = document.getElementById("btn-start");
const btnStop = document.getElementById("btn-stop");
const btnReset = document.getElementById("btn-reset");
const greenTimeInput = document.getElementById("green-time");

let lanes = ["North", "East", "South", "West"];
let state = {
  current_signal: null,
  prev_signal: null,
  queue: [],
};

function addLog(msg) {
  const div = document.createElement("div");
  div.className = "log";
  div.textContent = `[${new Date().toLocaleTimeString()}] ${msg}`;
  logList.prepend(div);
}

function initUI() {
  laneSelect.innerHTML = "";
  lanesContainer.innerHTML = "";

  lanes.forEach((lane) => {
    const opt = document.createElement("option");
    opt.value = lane;
    opt.textContent = lane;
    laneSelect.appendChild(opt);

    const laneDiv = document.createElement("div");
    laneDiv.className = "lane";
    laneDiv.id = `lane-${lane}`;

    const title = document.createElement("h3");
    title.textContent = `${lane} Lane`;
    laneDiv.appendChild(title);

    const lights = document.createElement("div");
    lights.className = "lights";
    lights.innerHTML = `
      <div class="light red" id="light-${lane}-red"></div>
      <div class="light yellow" id="light-${lane}-yellow"></div>
      <div class="light green" id="light-${lane}-green"></div>
    `;
    laneDiv.appendChild(lights);

    const sigLabel = document.createElement("div");
    sigLabel.className = "sig-label";
    sigLabel.textContent = "Signal";
    laneDiv.appendChild(sigLabel);

    const queueDiv = document.createElement("div");
    queueDiv.className = "queue";
    queueDiv.id = `queue-${lane}`;
    laneDiv.appendChild(queueDiv);

    lanesContainer.appendChild(laneDiv);
  });
}

async function fetchStatus() {
  const res = await fetch("/api/status");
  const data = await res.json();
  state.queue = data.queue;
  state.current_signal = data.current_signal;
  state.prev_signal = data.prev_signal;
  renderQueues();
  updateLights();
}

async function fetchExplain() {
  const res = await fetch("/api/explain");
  const data = await res.json();
  explainBox.textContent = data.description;
}

function updateLights() {
  lanes.forEach((lane) => {
    ["red", "yellow", "green"].forEach((c) =>
      document.getElementById(`light-${lane}-${c}`).classList.remove("on")
    );

    if (state.current_signal === lane)
      document.getElementById(`light-${lane}-green`).classList.add("on");
    else if (state.prev_signal === lane)
      document.getElementById(`light-${lane}-yellow`).classList.add("on");
    else
      document.getElementById(`light-${lane}-red`).classList.add("on");
  });
}

function renderQueues() {
  lanes.forEach((lane) => {
    const qDiv = document.getElementById(`queue-${lane}`);
    qDiv.innerHTML = "";

    const vehicles = state.queue.filter((v) => v.startsWith(lane));
    vehicles.forEach((v, i) => {
      const veh = document.createElement("div");
      veh.className = "vehicle";
      veh.textContent = v.split("-")[1];
      qDiv.appendChild(veh);

      if (state.current_signal === lane && i === 0) {
        veh.classList.add("moving");
        setTimeout(() => veh.remove(), 900);
      }
    });
  });
}

async function enqueueVehicle() {
  const lane = laneSelect.value;
  const type = vehicleType.value;
  const vehicle = `${lane}-${type}-${Math.floor(Math.random() * 1000)}`;
  const res = await fetch("/api/enqueue", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ vehicle, lane }),
  });
  const data = await res.json();
  addLog(data.message);
  await fetchStatus();
}

async function dequeueVehicle() {
  const res = await fetch("/api/dequeue", { method: "POST" });
  const data = await res.json();
  addLog(data.message);
  await fetchStatus();
}

async function startAuto() {
  const signal_time = greenTimeInput.value;
  const res = await fetch("/api/start_auto", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ signal_time }),
  });
  const data = await res.json();
  addLog(data.message);
}

async function stopAuto() {
  const res = await fetch("/api/stop_auto", { method: "POST" });
  const data = await res.json();
  addLog(data.message);
}

async function resetSystem() {
  const res = await fetch("/api/reset", { method: "POST" });
  const data = await res.json();
  addLog(data.message);
  await fetchStatus();
}

btnEnq.addEventListener("click", enqueueVehicle);
btnDeq.addEventListener("click", dequeueVehicle);
btnStart.addEventListener("click", startAuto);
btnStop.addEventListener("click", stopAuto);
btnReset.addEventListener("click", resetSystem);

setInterval(fetchStatus, 1000);

initUI();
fetchStatus();
fetchExplain();
