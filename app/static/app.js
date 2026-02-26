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

const tabButtons = document.querySelectorAll('.tab-button[data-tab-target]');
const tabPanels = document.querySelectorAll('.tab-panel');
const packageForm = document.getElementById('package-template-form');
const packageGrid = document.getElementById('package-template-grid');

function activateTab(targetId) {
  tabButtons.forEach((button) => {
    button.classList.toggle('is-active', button.dataset.tabTarget === targetId);
  });
  tabPanels.forEach((panel) => {
    panel.classList.toggle('is-active', panel.id === targetId);
  });
}

function applyTemplateToCustomerForm(name, rate, dueDay) {
  const planInput = document.querySelector('[data-package-plan]');
  const rateInput = document.querySelector('[data-package-rate]');
  const dueDayInput = document.querySelector('[data-package-due-day]');

  if (planInput) {
    planInput.value = name;
  }
  if (rateInput) {
    rateInput.value = rate;
  }
  if (dueDayInput) {
    dueDayInput.value = dueDay;
  }

  activateTab('tab-customer');
}

if (tabButtons.length > 0) {
  tabButtons.forEach((button) => {
    button.addEventListener('click', () => activateTab(button.dataset.tabTarget));
  });
}

if (packageGrid) {
  packageGrid.addEventListener('click', (event) => {
    const target = event.target;
    if (!(target instanceof HTMLElement) || !target.classList.contains('apply-package')) {
      return;
    }

    applyTemplateToCustomerForm(
      target.dataset.packageName,
      target.dataset.packageRate,
      target.dataset.packageDueDay,
    );
  });
}

if (packageForm && packageGrid) {
  packageForm.addEventListener('submit', (event) => {
    event.preventDefault();
    const data = new FormData(packageForm);
    const name = String(data.get('package_name') || '').trim();
    const rate = String(data.get('package_rate') || '').trim();
    const dueDay = String(data.get('package_due_day') || '').trim();

    if (!name || !rate || !dueDay) {
      return;
    }

    const card = document.createElement('article');
    card.className = 'package-card';
    card.innerHTML = `
      <span class="package-tag">Custom</span>
      <h4>${name}</h4>
      <p>KES ${Number(rate).toLocaleString()} / month · Due day ${dueDay}</p>
      <button
        type="button"
        class="apply-package"
        data-package-name="${name}"
        data-package-rate="${rate}"
        data-package-due-day="${dueDay}"
      >Apply to customer form</button>
    `;
    packageGrid.appendChild(card);
    packageForm.reset();
  });
}
