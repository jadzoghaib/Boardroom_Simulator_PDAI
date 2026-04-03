const API_BASE = window.location.origin;

const state = {
  threadId: crypto.randomUUID(),
  setup: null,
  meetingStatus: "idle",
};

let introRequestSeq = 0;

const el = {
  classmateSelect: document.getElementById("classmateSelect"),
  partnerSelect: document.getElementById("partnerSelect"),
  countrySelect: document.getElementById("countrySelect"),
  sectorSelect: document.getElementById("sectorSelect"),
  founderIntro: document.getElementById("founderIntro"),
  founderIntroSource: document.getElementById("founderIntroSource"),
  founderIntroLink: document.getElementById("founderIntroLink"),
  founderBackground: document.getElementById("founderBackground"),
  cofounderBackground: document.getElementById("cofounderBackground"),
  generateSetupBtn: document.getElementById("generateSetupBtn"),
  marketBtn: document.getElementById("marketBtn"),
  startBoardBtn: document.getElementById("startBoardBtn"),
  resumeBtn: document.getElementById("resumeBtn"),
  pitchText: document.getElementById("pitchText"),
  refreshDataBtn: document.getElementById("refreshDataBtn"),
  resetBtn: document.getElementById("resetBtn"),
  budgetVal: document.getElementById("budgetVal"),
  burnVal: document.getElementById("burnVal"),
  revenueVal: document.getElementById("revenueVal"),
  xpVal: document.getElementById("xpVal"),
  metaLine: document.getElementById("metaLine"),
  probVal: document.getElementById("probVal"),
  runwayVal: document.getElementById("runwayVal"),
  statusVal: document.getElementById("statusVal"),
  log: document.getElementById("log"),
  helpBtn: document.getElementById("helpBtn"),
};

function money(v) {
  return `$${Number(v || 0).toLocaleString()}`;
}

function setStep(n) {
  document.querySelectorAll(".step").forEach((s) => {
    const isActive = Number(s.dataset.step) === n;
    s.classList.toggle("is-active", isActive);
  });
}

function pushLogLine(text) {
  const item = document.createElement("div");
  item.className = "log-item";

  const t = String(text || "");
  if (t.includes("[Founder")) item.classList.add("founder");
  if (t.includes("[Skeptical VC]")) item.classList.add("vc");
  if (t.includes("[Pragmatic Mentor]")) item.classList.add("mentor");
  if (t.includes("[Auditor]")) item.classList.add("auditor");

  item.textContent = t;
  el.log.appendChild(item);
  el.log.scrollTop = el.log.scrollHeight;
}

function resetLog() {
  el.log.innerHTML = "";
}

function applySetupToUI(setup) {
  el.budgetVal.textContent = money(setup.budget);
  el.burnVal.textContent = money(setup.burn_rate);
  el.revenueVal.textContent = money(setup.revenue);
  el.xpVal.textContent = `${setup.founder_experience} years`;
  el.metaLine.textContent = `Founder: ${setup.classmate?.name || "N/A"} | Partner: ${setup.partner?.name || "N/A"} | Country: ${setup.country?.country || "N/A"} (${setup.country?.year || "N/A"})`;

  el.marketBtn.disabled = false;
  el.startBoardBtn.disabled = false;
  el.resumeBtn.disabled = true;
  el.statusVal.textContent = "ready";
  setStep(2);
}

async function fetchJson(path, options = {}) {
  const response = await fetch(`${API_BASE}${path}`, {
    headers: { "Content-Type": "application/json" },
    ...options,
  });

  if (!response.ok) {
    const body = await response.text();
    throw new Error(`HTTP ${response.status}: ${body}`);
  }

  return response.json();
}

function fillSelect(selectEl, options, labelKey = "name", valueKey = "name") {
  selectEl.innerHTML = "";
  options.forEach((opt) => {
    const option = document.createElement("option");
    option.value = opt[valueKey];
    option.textContent = opt[labelKey];
    selectEl.appendChild(option);
  });
}

function setFounderIntro(content, source = "Profile", linkedinUrl = "") {
  el.founderIntro.textContent = content;
  el.founderIntroSource.textContent = source;

  if (linkedinUrl) {
    el.founderIntroLink.href = linkedinUrl;
    el.founderIntroLink.classList.remove("hidden");
  } else {
    el.founderIntroLink.href = "#";
    el.founderIntroLink.classList.add("hidden");
  }
}

async function updateFounderIntro(name) {
  const currentRequest = ++introRequestSeq;

  if (!name || name === "Loading...") {
    setFounderIntro("Select a founder to see a short intro based on their public profile.", "Profile", "");
    return;
  }

  setFounderIntro("Loading founder intro from the public profile...", "Loading", "");

  try {
    const data = await fetchJson(`/api/setup/classmate-intro?name=${encodeURIComponent(name)}`);
    if (currentRequest !== introRequestSeq) return;
    setFounderIntro(data.intro || `No intro returned for ${name}.`, data.source || "Profile", data.linkedin_url || "");
  } catch (error) {
    if (currentRequest !== introRequestSeq) return;
    setFounderIntro(`Could not load a profile intro for ${name}.`, "Unavailable", "");
  }
}

async function loadSetupData() {
  const [classmateRes, partnerRes, countryRes] = await Promise.all([
    fetchJson("/api/setup/classmates"),
    fetchJson("/api/setup/partners"),
    fetchJson("/api/setup/countries"),
  ]);

  fillSelect(el.classmateSelect, classmateRes.classmates || []);
  fillSelect(el.partnerSelect, partnerRes.partners || []);

  el.countrySelect.innerHTML = "";
  (countryRes.countries || []).forEach((country) => {
    const option = document.createElement("option");
    option.value = country;
    option.textContent = country;
    el.countrySelect.appendChild(option);
  });

  if ((countryRes.countries || []).includes("Singapore")) {
    el.countrySelect.value = "Singapore";
  }

  if (el.classmateSelect.value) {
    await updateFounderIntro(el.classmateSelect.value);
  }
}

async function generateSetup() {
  const payload = {
    classmate_name: el.classmateSelect.value,
    partner_name: el.partnerSelect.value,
    country: el.countrySelect.value,
    preferred_sector: el.sectorSelect.value,
    founder_background: el.founderBackground.value,
    cofounder_background: el.cofounderBackground.value,
  };

  const setup = await fetchJson("/api/setup/founder", {
    method: "POST",
    body: JSON.stringify(payload),
  });

  state.setup = setup;
  state.threadId = crypto.randomUUID();
  state.meetingStatus = "idle";
  resetLog();
  pushLogLine(`[Founder Setup] ${setup.classmate?.name} launched with ${setup.partner?.name}.`);
  applySetupToUI(setup);
}

async function runMarketPhysics() {
  if (!state.setup) return;
  const payload = {
    thread_id: state.threadId,
    budget: state.setup.budget,
    burn_rate: state.setup.burn_rate,
    revenue: state.setup.revenue,
    founder_experience: state.setup.founder_experience,
    sector: state.setup.sector,
    pitch: "",
    action: "start",
  };

  const data = await fetchJson("/api/predict", {
    method: "POST",
    body: JSON.stringify(payload),
  });

  el.probVal.textContent = `${(Number(data.success_probability || 0) * 100).toFixed(1)}%`;
  el.runwayVal.textContent = `${data.runway_months || 0} months`;
  setStep(2);
}

async function startBoardMeeting() {
  if (!state.setup) return;

  const payload = {
    thread_id: state.threadId,
    budget: state.setup.budget,
    burn_rate: state.setup.burn_rate,
    revenue: state.setup.revenue,
    founder_experience: state.setup.founder_experience,
    sector: state.setup.sector,
    pitch: el.pitchText.value,
    action: "start",
  };

  const data = await fetchJson("/api/boardroom_turn", {
    method: "POST",
    body: JSON.stringify(payload),
  });

  resetLog();
  (data.messages || []).forEach(pushLogLine);
  state.meetingStatus = data.status || "paused";
  el.statusVal.textContent = state.meetingStatus;
  el.resumeBtn.disabled = state.meetingStatus !== "paused";
  setStep(3);
}

async function resumeBoardMeeting() {
  if (!state.setup || state.meetingStatus !== "paused") return;

  const payload = {
    thread_id: state.threadId,
    budget: state.setup.budget,
    burn_rate: state.setup.burn_rate,
    revenue: state.setup.revenue,
    founder_experience: state.setup.founder_experience,
    sector: state.setup.sector,
    pitch: el.pitchText.value,
    action: "resume",
  };

  const data = await fetchJson("/api/boardroom_turn", {
    method: "POST",
    body: JSON.stringify(payload),
  });

  resetLog();
  (data.messages || []).forEach(pushLogLine);
  state.meetingStatus = data.status || "done";
  el.statusVal.textContent = state.meetingStatus;
  el.resumeBtn.disabled = state.meetingStatus !== "paused";
}

function hardReset() {
  state.setup = null;
  state.threadId = crypto.randomUUID();
  state.meetingStatus = "idle";

  el.budgetVal.textContent = "$0";
  el.burnVal.textContent = "$0";
  el.revenueVal.textContent = "$0";
  el.xpVal.textContent = "0 years";
  el.metaLine.textContent = "No setup generated yet.";
  el.probVal.textContent = "-";
  el.runwayVal.textContent = "-";
  el.statusVal.textContent = "idle";

  el.marketBtn.disabled = true;
  el.startBoardBtn.disabled = true;
  el.resumeBtn.disabled = true;

  resetLog();
  setStep(1);
}

async function init() {
  hardReset();
  await loadSetupData();
}

el.generateSetupBtn.addEventListener("click", () => generateSetup().catch((e) => alert(e.message)));
el.marketBtn.addEventListener("click", () => runMarketPhysics().catch((e) => alert(e.message)));
el.startBoardBtn.addEventListener("click", () => startBoardMeeting().catch((e) => alert(e.message)));
el.resumeBtn.addEventListener("click", () => resumeBoardMeeting().catch((e) => alert(e.message)));
el.refreshDataBtn.addEventListener("click", () => loadSetupData().catch((e) => alert(e.message)));
el.resetBtn.addEventListener("click", hardReset);
el.classmateSelect.addEventListener("change", () => updateFounderIntro(el.classmateSelect.value));
el.helpBtn.addEventListener("click", () => {
  document.getElementById("helpModal").classList.remove("hidden");
  document.getElementById("helpModal").classList.add("flex");
});

init().catch((e) => alert(e.message));
