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

setInterval(pollStatus, 1000);

loadFirmwareList();
startLogStream();
