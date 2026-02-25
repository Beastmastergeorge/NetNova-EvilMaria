const toggleButton = document.getElementById("toggle-speech");
const alertsList = document.getElementById("alerts-list");

let speechEnabled = false;
let announcedEventIds = new Set();

function speak(text) {
  if (!speechEnabled || !("speechSynthesis" in window)) {
    return;
  }
  const message = new SpeechSynthesisUtterance(text);
  message.rate = 1;
  message.pitch = 0.95;
  message.lang = "en-US";
  window.speechSynthesis.speak(message);
}

function updateMetrics(metrics) {
  const customerNode = document.getElementById("stat-customers");
  const mrrNode = document.getElementById("stat-mrr");
  const unpaidNode = document.getElementById("stat-unpaid");
  const criticalNode = document.getElementById("critical-count");

  if (!customerNode || !mrrNode || !unpaidNode || !criticalNode) {
    return;
  }

  customerNode.textContent = metrics.customer_count;
  mrrNode.textContent = `$${Number(metrics.mrr).toFixed(2)}`;
  unpaidNode.textContent = `$${Number(metrics.unpaid).toFixed(2)}`;
  criticalNode.textContent = metrics.critical_count;
}

function announceCriticalAlertsFromDom() {
  const alertItems = document.querySelectorAll("#alerts-list li[data-id]");
  alertItems.forEach((item) => {
    const eventId = Number(item.dataset.id);
    const isAcknowledged = item.classList.contains("acknowledged");
    const severity = item.dataset.severity;
    const message = item.dataset.message;

    if (!isAcknowledged && severity === "critical" && !announcedEventIds.has(eventId)) {
      speak(`EVIL MARIA critical alert. ${message}`);
      announcedEventIds.add(eventId);
    }
  });
}

async function pollApi() {
  try {
    const [metricsResponse, eventsResponse] = await Promise.all([
      fetch("/api/metrics", { headers: { Accept: "application/json" } }),
      fetch("/api/events?unacknowledged_only=true", { headers: { Accept: "application/json" } }),
    ]);

    if (metricsResponse.ok) {
      const metrics = await metricsResponse.json();
      updateMetrics(metrics);
    }

    if (eventsResponse.ok) {
      const events = await eventsResponse.json();
      const hasNewCritical = events.some((event) => event.severity === "critical" && !announcedEventIds.has(event.id));
      if (hasNewCritical) {
        window.location.reload();
      }
async function pollUnacknowledgedEvents() {
  try {
    const response = await fetch("/api/events?unacknowledged_only=true", { headers: { Accept: "application/json" } });
    if (!response.ok) {
      return;
    }
    const events = await response.json();

    const hasNewCritical = events.some((event) => event.severity === "critical" && !announcedEventIds.has(event.id));
    if (hasNewCritical) {
      window.location.reload();
    }
  } catch (error) {
    console.debug("EVIL MARIA poll failed", error);
  }
}

if (alertsList) {
  announceCriticalAlertsFromDom();
  setInterval(pollApi, 15000);
  setInterval(pollUnacknowledgedEvents, 15000);
}

if (toggleButton) {
  toggleButton.addEventListener("click", () => {
    speechEnabled = !speechEnabled;
    toggleButton.textContent = speechEnabled
      ? "Speech notifications enabled"
      : "Enable speech notifications";

    if (speechEnabled) {
      speak("EVIL MARIA speech notification enabled.");
      announceCriticalAlertsFromDom();
    } else if ("speechSynthesis" in window) {
      window.speechSynthesis.cancel();
    }
  });
}
