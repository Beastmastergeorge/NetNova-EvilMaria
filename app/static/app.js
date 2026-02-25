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
