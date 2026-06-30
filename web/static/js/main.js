let monthChart = null;
let versionChart = null;

function loadStats() {
    fetch("/stats")
        .then(r => r.json())
        .then(data => {
            // Month stats (text)
            const m = data.current_month;
            document.getElementById("monthStatsBox").innerHTML =
                `Month: ${m.month.toUpperCase()}<br>
                 Success (PO): ${m.po}<br>
                 Failures (NE): ${m.ne}`;

            // Per-version stats (text)
            const vs = data.versions;
            let html = "<table><tr><th>Version</th><th>PO</th><th>NE</th></tr>";
            const versionLabels = [];
            const versionPO = [];
            const versionNE = [];

            for (const v in vs) {
                html += `<tr>
                            <td>${v}</td>
                            <td>${vs[v].po}</td>
                            <td>${vs[v].ne}</td>
                         </tr>`;
                versionLabels.push(v);
                versionPO.push(vs[v].po);
                versionNE.push(vs[v].ne);
            }
            html += "</table>";
            document.getElementById("versionStatsBox").innerHTML = html;

            // Month chart (PO vs NE)
            const monthCtx = document.getElementById("monthChart").getContext("2d");
            const monthData = {
                labels: ["PO", "NE"],
                datasets: [{
                    label: `Month ${m.month.toUpperCase()}`,
                    data: [parseInt(m.po), parseInt(m.ne)],
                    backgroundColor: ["#4caf50", "#f44336"]
                }]
            };

            if (monthChart) {
                monthChart.data = monthData;
                monthChart.update();
            } else {
                monthChart = new Chart(monthCtx, {
                    type: "bar",
                    data: monthData,
                    options: {
                        responsive: true,
                        plugins: {
                            legend: { display: false }
                        }
                    }
                });
            }

            // Version chart (per-version PO/NE)
            const versionCtx = document.getElementById("versionChart").getContext("2d");
            const versionData = {
                labels: versionLabels,
                datasets: [
                    {
                        label: "PO",
                        data: versionPO.map(x => parseInt(x)),
                        backgroundColor: "#4caf50"
                    },
                    {
                        label: "NE",
                        data: versionNE.map(x => parseInt(x)),
                        backgroundColor: "#f44336"
                    }
                ]
            };

            if (versionChart) {
                versionChart.data = versionData;
                versionChart.update();
            } else {
                versionChart = new Chart(versionCtx, {
                    type: "bar",
                    data: versionData,
                    options: {
                        responsive: true,
                        plugins: {
                            legend: { position: "top" }
                        }
                    }
                });
            }
        });
}


function loadFirmwareList() {
    fetch("/firmware_list")
        .then(r => r.json())
        .then(list => {
            const sel = document.getElementById("firmwareSelect");
            sel.innerHTML = "";
            list.forEach(v => {
                const opt = document.createElement("option");
                opt.value = v;
                opt.textContent = v;
                sel.appendChild(opt);
            });
        });
}
function addEventTimestamp(type, ts) {
    const box = document.getElementById("eventTimestamps");
    const entry = document.createElement("div");
    entry.textContent = `${type}:${ts}`;
    box.appendChild(entry);
}

if (msg.startsWith("PO:")) {
    const ts = parseFloat(msg.split(":")[1]);
    addEventTimestamp("PO", ts);
}

if (msg.startsWith("NE:")) {
    const ts = parseFloat(msg.split(":")[1]);
    addEventTimestamp("NE", ts);
}


function setFirmware() {
    const fw = document.getElementById("firmwareSelect").value;
    fetch(`/set_firmware/${fw}`)
        .then(r => r.json())
        .then(res => {
            alert("Firmware set to " + res.version);
        });
}

function syncRepo() {
    fetch("/sync_repo")
        .then(() => alert("Repository synced"));
}

function startLogStream() {
    const logBox = document.getElementById("logBox");
    const evt = new EventSource("/stream");

    evt.onmessage = function(e) {
        logBox.innerHTML += e.data + "<br>";
        logBox.scrollTop = logBox.scrollHeight;
    };
}

function pollStatus() {
    fetch("/live")
        .then(r => r.json())
        .then(logs => {
            const statusBox = document.getElementById("statusBox");
            if (logs.length === 0) {
                statusBox.textContent = "Waiting for device...";
            } else {
                statusBox.textContent = logs[logs.length - 1];
            }
        });
}

function loadActiveFirmware() {
    fetch("/active_firmware")
        .then(r => r.json())
        .then(data => {
            document.getElementById("activeFirmwareBox").textContent =
                "Current firmware: " + data.active;
        });
}

function loadStats() {
    fetch("/stats")
        .then(r => r.json())
        .then(data => {
            // Month stats
            const m = data.current_month;
            document.getElementById("monthStatsBox").innerHTML =
                `Month: ${m.month.toUpperCase()}<br>
                 Success (PO): ${m.po}<br>
                 Failures (NE): ${m.ne}`;

            // Per-version stats
            const vs = data.versions;
            let html = "<table><tr><th>Version</th><th>PO</th><th>NE</th></tr>";
            for (const v in vs) {
                html += `<tr>
                            <td>${v}</td>
                            <td>${vs[v].po}</td>
                            <td>${vs[v].ne}</td>
                         </tr>`;
            }
            html += "</table>";
            document.getElementById("versionStatsBox").innerHTML = html;
        });
}

setInterval(pollStatus, 1000);
setInterval(loadActiveFirmware, 1000);
setInterval(loadStats, 2000);

loadFirmwareList();
startLogStream();
