const monitorButton = document.getElementById("run-monitor");
const alertsList = document.getElementById("alerts-list");
const voiceToggle = document.getElementById("voice-toggle");
let lastSpokenAlertId = null;

function speakAlert(text) {
  if (!voiceToggle || !voiceToggle.checked || !window.speechSynthesis) {
    return;
  }

  const utterance = new SpeechSynthesisUtterance(`EVIL MARIA alert. ${text}`);
  utterance.rate = 1;
  utterance.pitch = 0.9;
  window.speechSynthesis.speak(utterance);
}

async function refreshAlerts() {
  const response = await fetch("/api/alerts/latest");
  if (!response.ok) return;

  const alerts = await response.json();
  alertsList.innerHTML = "";

  if (!alerts.length) {
    const item = document.createElement("li");
    item.textContent = "No active alerts.";
    alertsList.appendChild(item);
    return;
  }

  alerts.forEach((alert) => {
    const item = document.createElement("li");
    item.innerHTML = `<strong>[${alert.severity.toUpperCase()}]</strong> ${alert.message} <small>(${alert.created_at})</small>`;
    alertsList.appendChild(item);
  });

  const latest = alerts[0];
  if (latest && latest.id !== lastSpokenAlertId && ["warning", "critical"].includes(latest.severity)) {
    speakAlert(latest.message);
    lastSpokenAlertId = latest.id;
  }
}

if (monitorButton) {
  monitorButton.addEventListener("click", async () => {
    monitorButton.disabled = true;
    monitorButton.textContent = "Monitoring...";
    try {
      await fetch("/api/monitor/run", { method: "POST" });
      await refreshAlerts();
    } finally {
      monitorButton.disabled = false;
      monitorButton.textContent = "Run Health Cycle";
    }
  });
}

refreshAlerts();
setInterval(refreshAlerts, 20000);
