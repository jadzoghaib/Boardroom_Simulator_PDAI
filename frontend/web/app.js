const API_BASE = window.location.origin;

const state = {
  threadId: crypto.randomUUID(),
  setup: null,
  meetingStatus: "idle",
  selectedCelebrity: null,
  selectedProfessor: null,
  partnersForDetail: {},
};

let introRequestSeq = 0;

const el = {
  classmateSelect: document.getElementById("classmateSelect"),
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
  // New partner selector elements
  celebrityPartnerBtn: document.getElementById("celebrityPartnerBtn"),
  professorPartnerBtn: document.getElementById("professorPartnerBtn"),
  celebrityPartnerDisplay: document.getElementById("celebrityPartnerDisplay"),
  professorPartnerDisplay: document.getElementById("professorPartnerDisplay"),
  celebrityPartnerModal: document.getElementById("celebrityPartnerModal"),
  professorPartnerModal: document.getElementById("professorPartnerModal"),
  celebrityDetailModal: document.getElementById("celebrityDetailModal"),
  professorDetailModal: document.getElementById("professorDetailModal"),
  celebrityPartnerGrid: document.getElementById("celebrityPartnerGrid"),
  professorPartnerGrid: document.getElementById("professorPartnerGrid"),
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
  if (t.includes("[Tech Visionary VC]") || t.includes("[Finance Returns VC]") || t.includes("[Commercial Growth VC]")) item.classList.add("vc");
  if (t.includes("[Data Analyst]")) item.classList.add("auditor");

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
  const celebrityName = setup.partner_team?.celebrity?.name || "N/A";
  const professorName = setup.partner_team?.professor?.name || "N/A";
  el.metaLine.textContent = `Founder: ${setup.classmate?.name || "N/A"} | Celeb: ${celebrityName} | Prof: ${professorName} | Country: ${setup.country?.country || "N/A"} (${setup.country?.year || "N/A"})`;

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
  const [classmateRes, celebrityRes, professorRes, countryRes] = await Promise.all([
    fetchJson("/api/setup/classmates"),
    fetchJson("/api/setup/celebrity-partners"),
    fetchJson("/api/setup/professor-partners"),
    fetchJson("/api/setup/countries"),
  ]);

  fillSelect(el.classmateSelect, classmateRes.classmates || []);
  
  // Populate partner grids
  const celebrities = celebrityRes.celebrity_partners || [];
  const professors = professorRes.professor_partners || [];
  
  populatePartnerCards("celebrity", celebrities);
  populatePartnerCards("professor", professors);

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
  if (!state.selectedCelebrity || !state.selectedProfessor) {
    alert("Please select both a Celebrity Co-Founder and an Academic Specialist.");
    return;
  }

  const payload = {
    classmate_name: el.classmateSelect.value,
    celebrity_partner_name: state.selectedCelebrity,
    professor_partner_name: state.selectedProfessor,
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
  pushLogLine(`[Founder Setup] ${setup.classmate?.name} launched with ${setup.partner_team?.name || "partner team"}.`);
  if ((setup.partner_team?.unlocked_synergies || []).length > 0) {
    pushLogLine(`[Synergy] Unlocked: ${setup.partner_team.unlocked_synergies.join(", ")}`);
  }
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
    partner_name: state.setup.partner_team?.name || "Partner Team",
    partner_style: state.setup.partner_team?.style || "",
    synergy_bonus: state.setup.partner_team?.synergy_bonus || 0.0,
  };

  const data = await fetchJson("/api/boardroom_turn", {
    method: "POST",
    body: JSON.stringify(payload),
  });

  resetLog();
  (data.messages || []).forEach(pushLogLine);
  state.meetingStatus = data.status || "paused";
  if (typeof data.updated_budget === "number") state.setup.budget = data.updated_budget;
  if (typeof data.updated_burn_rate === "number") state.setup.burn_rate = data.updated_burn_rate;
  if (typeof data.updated_revenue === "number") state.setup.revenue = data.updated_revenue;
  applySetupToUI(state.setup);
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
    partner_name: state.setup.partner_team?.name || "Partner Team",
    partner_style: state.setup.partner_team?.style || "",
    synergy_bonus: state.setup.partner_team?.synergy_bonus || 0.0,
  };

  const data = await fetchJson("/api/boardroom_turn", {
    method: "POST",
    body: JSON.stringify(payload),
  });

  resetLog();
  (data.messages || []).forEach(pushLogLine);
  state.meetingStatus = data.status || "done";
  if (typeof data.updated_budget === "number") state.setup.budget = data.updated_budget;
  if (typeof data.updated_burn_rate === "number") state.setup.burn_rate = data.updated_burn_rate;
  if (typeof data.updated_revenue === "number") state.setup.revenue = data.updated_revenue;
  applySetupToUI(state.setup);
  el.statusVal.textContent = state.meetingStatus;
  el.resumeBtn.disabled = state.meetingStatus !== "paused";
}

function hardReset() {
  state.setup = null;
  state.threadId = crypto.randomUUID();
  state.meetingStatus = "idle";
  state.selectedCelebrity = null;
  state.selectedProfessor = null;

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

  el.celebrityPartnerDisplay.textContent = "Select partner...";
  el.professorPartnerDisplay.textContent = "Select partner...";

  resetLog();
  setStep(1);
}

async function init() {
  hardReset();
  await loadSetupData();
}

// ===== PARTNER CARD FUNCTIONS =====

function getTopStats(stats, limit = 3) {
  const entries = Object.entries(stats).sort((a, b) => b[1] - a[1]);
  return entries.slice(0, limit).map(([key, val]) => ({ key, val }));
}

function populatePartnerCards(type, partners) {
  const gridEl = type === "celebrity" ? el.celebrityPartnerGrid : el.professorPartnerGrid;
  gridEl.innerHTML = "";

  partners.forEach((partner) => {
    const card = document.createElement("div");
    card.className = "partner-card";
    card.innerHTML = `
      <div class="flex flex-col items-center gap-3 text-center">
        <img src="${partner.avatar_url}" alt="${partner.name}" class="partner-avatar w-24 h-24 rounded-lg object-cover shadow-md">
        <div class="flex-1 min-w-0 w-full">
          <h3 class="font-bold text-slate-900 text-base leading-tight mb-1">${partner.name}</h3>
          <p class="text-xs text-slate-600 font-semibold mb-1">${partner.core_ability}</p>
          <p class="text-xs text-slate-500">${partner.domain}</p>
        </div>
      </div>
    `;
    
    card.addEventListener("click", () => {
      showPartnerDetail(type, partner);
    });
    
    gridEl.appendChild(card);
  });
}

function showPartnerModal(type) {
  if (type === "celebrity") {
    el.celebrityPartnerModal.classList.remove("hidden");
    el.celebrityPartnerModal.classList.add("flex");
  } else {
    el.professorPartnerModal.classList.remove("hidden");
    el.professorPartnerModal.classList.add("flex");
  }
}

function closePartnerModal(type) {
  if (type === "celebrity") {
    el.celebrityPartnerModal.classList.add("hidden");
    el.celebrityPartnerModal.classList.remove("flex");
  } else {
    el.professorPartnerModal.classList.add("hidden");
    el.professorPartnerModal.classList.remove("flex");
  }
}

function closeDetailModal(type) {
  if (type === "celebrity") {
    el.celebrityDetailModal.classList.add("hidden");
    el.celebrityDetailModal.classList.remove("flex");
  } else {
    el.professorDetailModal.classList.add("hidden");
    el.professorDetailModal.classList.remove("flex");
  }
}

function showPartnerDetail(type, partner) {
  state.partnersForDetail = { ...state.partnersForDetail, [type]: partner };

  const detailModal = type === "celebrity" ? el.celebrityDetailModal : el.professorDetailModal;
  const nameEl = type === "celebrity" ? document.getElementById("detailName") : document.getElementById("detailNameProf");
  const avatarEl = type === "celebrity" ? document.getElementById("detailAvatar") : document.getElementById("detailAvatarProf");
  const abilityEl = type === "celebrity" ? document.getElementById("detailAbility") : document.getElementById("detailAbilityProf");
  const domainEl = type === "celebrity" ? document.getElementById("detailDomain") : document.getElementById("detailDomainProf");
  const descEl = type === "celebrity" ? document.getElementById("detailDescription") : document.getElementById("detailDescriptionProf");
  const statsEl = type === "celebrity" ? document.getElementById("detailStats") : document.getElementById("detailStatsProf");
  const strengthsEl = type === "celebrity" ? document.getElementById("detailStrengths") : document.getElementById("detailStrengthsProf");

  nameEl.textContent = partner.name;
  avatarEl.src = partner.avatar_url;
  abilityEl.textContent = partner.core_ability;
  domainEl.textContent = partner.domain;
  descEl.textContent = partner.description;

  // Populate stats
  statsEl.innerHTML = "";
  const topStats = getTopStats(partner.stats, 4);
  topStats.forEach(({ key, val }) => {
    const statBox = document.createElement("div");
    statBox.className = "stat-box";
    statBox.innerHTML = `
      <div class="stat-box-value">${val}</div>
      <div class="stat-box-label">${key}</div>
    `;
    statsEl.appendChild(statBox);
  });

  // Populate strengths (top 3 stats with descriptions)
  strengthsEl.innerHTML = "";
  topStats.slice(0, 3).forEach(({ key, val }) => {
    const strengthItem = document.createElement("div");
    strengthItem.className = "strength-item";
    const statName = key.charAt(0).toUpperCase() + key.slice(1);
    strengthItem.textContent = `${statName}: ${val}/10 - ${getStrengthDescription(key)}`;
    strengthsEl.appendChild(strengthItem);
  });

  // Close the partner modal and show detail
  closePartnerModal(type);
  detailModal.classList.remove("hidden");
  detailModal.classList.add("flex");
}

function getStrengthDescription(stat) {
  const descriptions = {
    growth: "Strong ability to scale and grow user base",
    brand: "Excellent at building brand value and reputation",
    product: "Mastery in product development and UX",
    tech: "Deep technical expertise and innovation",
    ops: "Exceptional operational execution and efficiency",
    finance: "Strong financial acumen and capital management",
    innovation: "Generates breakthrough ideas and solutions",
    execution: "Delivers results consistently and reliably",
  };
  return descriptions[stat] || "Specialized expertise";
}

function selectCelebrityPartner() {
  const partner = state.partnersForDetail.celebrity;
  if (partner) {
    state.selectedCelebrity = partner.name;
    el.celebrityPartnerDisplay.textContent = partner.name;
    closeDetailModal("celebrity");
  }
}

function selectProfessorPartner() {
  const partner = state.partnersForDetail.professor;
  if (partner) {
    state.selectedProfessor = partner.name;
    el.professorPartnerDisplay.textContent = partner.name;
    closeDetailModal("professor");
  }
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
el.celebrityPartnerBtn.addEventListener("click", () => showPartnerModal("celebrity"));
el.professorPartnerBtn.addEventListener("click", () => showPartnerModal("professor"));
el.helpBtn.addEventListener("click", () => {
  document.getElementById("helpModal").classList.remove("hidden");
  document.getElementById("helpModal").classList.add("flex");
});

init().catch((e) => alert(e.message));
