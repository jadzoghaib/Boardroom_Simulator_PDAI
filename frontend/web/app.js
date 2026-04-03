/**
 * Boardroom Sim — 8-Quarter Startup Simulation
 * Frontend Game Engine (Vanilla JS)
 */

const API = window.location.origin;

const game = {
  // ── State ──
  gameId: null,
  state: null,
  selectedCelebrity: null,
  selectedProfessor: null,
  celebrities: [],
  professors: [],

  // ═══════════════════════════════════════════════════════
  // SETUP
  // ═══════════════════════════════════════════════════════

  async init() {
    await Promise.all([
      this.loadClassmates(),
      this.loadCountries(),
      this.loadCelebrities(),
      this.loadProfessors(),
    ]);
  },

  async loadClassmates() {
    try {
      const res = await fetch(`${API}/api/setup/classmates`);
      const data = await res.json();
      const sel = document.getElementById('classmateSelect');
      sel.innerHTML = '<option value="">Select a classmate...</option>';
      (data.classmates || []).forEach(c => {
        sel.innerHTML += `<option value="${c.name}">${c.name}</option>`;
      });
      sel.addEventListener('change', () => this.onClassmateChange(sel.value));
    } catch (e) { console.error('Failed to load classmates:', e); }
  },

  async loadCountries() {
    try {
      const res = await fetch(`${API}/api/setup/countries`);
      const data = await res.json();
      const sel = document.getElementById('countrySelect');
      sel.innerHTML = '<option value="">Select a country...</option>';
      (data.countries || []).forEach(c => {
        const name = typeof c === 'string' ? c : c.country;
        sel.innerHTML += `<option value="${name}">${name}</option>`;
      });
    } catch (e) { console.error('Failed to load countries:', e); }
  },

  async loadCelebrities() {
    try {
      const res = await fetch(`${API}/api/setup/celebrity-partners`);
      const data = await res.json();
      this.celebrities = data.celebrity_partners || [];
    } catch (e) { console.error('Failed to load celebrities:', e); }
  },

  async loadProfessors() {
    try {
      const res = await fetch(`${API}/api/setup/professor-partners`);
      const data = await res.json();
      this.professors = data.professor_partners || [];
    } catch (e) { console.error('Failed to load professors:', e); }
  },

  async onClassmateChange(name) {
    const intro = document.getElementById('classmateIntro');
    if (!name) { intro.textContent = ''; return; }
    intro.textContent = 'Loading profile...';
    try {
      const res = await fetch(`${API}/api/setup/classmate-intro?name=${encodeURIComponent(name)}`);
      const data = await res.json();
      intro.textContent = data.intro || '';
    } catch (e) { intro.textContent = 'Could not load profile.'; }
  },

  goToStep1() {
    document.getElementById('setupStep1').classList.remove('hidden');
    document.getElementById('setupStep2').classList.add('hidden');
  },

  goToStep2() {
    const classmate = document.getElementById('classmateSelect').value;
    if (!classmate) { alert('Please select a classmate first.'); return; }

    document.getElementById('setupStep1').classList.add('hidden');
    document.getElementById('setupStep2').classList.remove('hidden');

    this.renderPartnerGrid('celebrityGrid', this.celebrities, 'celebrity');
    this.renderPartnerGrid('professorGrid', this.professors, 'professor');
  },

  renderPartnerGrid(containerId, partners, type) {
    const container = document.getElementById(containerId);
    container.innerHTML = '';
    partners.forEach(p => {
      const card = document.createElement('div');
      card.className = 'partner-card';
      card.dataset.name = p.name;
      card.innerHTML = `
        <div class="partner-card-name">${p.name}</div>
        <div class="partner-card-domain">${p.domain} • ${p.core_ability}</div>
        <div class="text-xs text-slate-500 mt-1">Cost: ${p.cost}/10</div>
      `;
      card.addEventListener('click', () => this.selectPartner(type, p.name, card, containerId));
      container.appendChild(card);
    });
  },

  selectPartner(type, name, card, containerId) {
    // Deselect all in this grid
    document.querySelectorAll(`#${containerId} .partner-card`).forEach(c => c.classList.remove('selected'));
    card.classList.add('selected');

    if (type === 'celebrity') this.selectedCelebrity = name;
    else this.selectedProfessor = name;

    // Enable start button if both selected
    const btn = document.getElementById('startGameBtn');
    btn.disabled = !(this.selectedCelebrity && this.selectedProfessor);

    // Show synergy preview
    this.updateSynergyPreview();
  },

  updateSynergyPreview() {
    const panel = document.getElementById('synergyPreview');
    const details = document.getElementById('synergyDetails');
    if (!this.selectedCelebrity || !this.selectedProfessor) {
      panel.classList.add('hidden');
      return;
    }
    panel.classList.remove('hidden');
    details.innerHTML = `<span class="text-white">${this.selectedCelebrity} + ${this.selectedProfessor}</span>`;
  },

  async startGame() {
    const btn = document.getElementById('startGameBtn');
    btn.disabled = true;
    btn.textContent = 'Launching...';

    const body = {
      classmate_name: document.getElementById('classmateSelect').value,
      country: document.getElementById('countrySelect').value,
      preferred_sector: document.getElementById('sectorSelect').value,
      celebrity_partner_name: this.selectedCelebrity,
      professor_partner_name: this.selectedProfessor,
    };

    try {
      const res = await fetch(`${API}/api/setup/founder`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(body),
      });
      const data = await res.json();
      this.gameId = data.game_id;
      this.state = data.state;

      document.getElementById('setupScreen').classList.add('hidden');
      document.getElementById('gameBoard').classList.remove('hidden');
      this.render();
    } catch (e) {
      alert('Failed to start game: ' + e.message);
      btn.disabled = false;
      btn.textContent = '🚀 Launch Your Startup';
    }
  },

  // ═══════════════════════════════════════════════════════
  // GAME ACTIONS
  // ═══════════════════════════════════════════════════════

  async chooseEvent(eventId, choiceIndex) {
    try {
      const res = await fetch(`${API}/api/game/${this.gameId}/choose_event`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ event_id: eventId, choice_index: choiceIndex }),
      });
      const data = await res.json();

      // Show reaction toast
      if (data.reaction) this.showToast(data.reaction);

      // Update local state
      await this.refreshState();
    } catch (e) { console.error('Choose event failed:', e); }
  },

  async skipEvents() {
    try {
      await fetch(`${API}/api/game/${this.gameId}/skip_events`, { method: 'POST' });
      await this.refreshState();
    } catch (e) { console.error('Skip events failed:', e); }
  },

  async endQuarter() {
    try {
      const res = await fetch(`${API}/api/game/${this.gameId}/end_quarter`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
      });
      const data = await res.json();
      this.state = data.state;

      if (data.state.game_over) {
        this.showGameOver();
      } else {
        this.showQuarterSummary(data.summary);
      }
      this.render();
    } catch (e) { console.error('End quarter failed:', e); }
  },

  async boardReview() {
    try {
      const res = await fetch(`${API}/api/game/${this.gameId}/board_review`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
      });
      const data = await res.json();
      this.state = data.state;

      // Show board review message
      if (data.board_review) {
        this.showToast(`🏛️ ${data.board_review.message}`);
      }
      this.render();
    } catch (e) { console.error('Board review failed:', e); }
  },

  async sendChat() {
    const input = document.getElementById('chatInput');
    const message = input.value.trim();
    if (!message) return;
    input.value = '';

    // Add user message to UI immediately
    this.addChatBubble('user', 'You', message);

    try {
      const res = await fetch(`${API}/api/game/${this.gameId}/chat`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ message }),
      });
      const data = await res.json();
      (data.messages || []).forEach(msg => {
        this.addChatBubble(msg.role, msg.speaker, msg.content);
      });
    } catch (e) {
      this.addChatBubble('system', 'System', 'Failed to get advisor response.');
    }
  },

  async refreshState() {
    try {
      const res = await fetch(`${API}/api/game/${this.gameId}/state`);
      const data = await res.json();
      this.state = data.state;
      this.render();

      if (data.state.game_over) this.showGameOver();
    } catch (e) { console.error('Refresh state failed:', e); }
  },

  // ═══════════════════════════════════════════════════════
  // HIRING
  // ═══════════════════════════════════════════════════════

  async openHiringModal() {
    try {
      const res = await fetch(`${API}/api/game/${this.gameId}/candidates`);
      const data = await res.json();
      this.renderHiringCandidates(data.candidates || [], data.filled_roles || []);
      document.getElementById('hiringModal').classList.remove('hidden');
      document.getElementById('hiringModal').classList.add('flex');
    } catch (e) { console.error('Load candidates failed:', e); }
  },

  closeHiringModal() {
    document.getElementById('hiringModal').classList.add('hidden');
    document.getElementById('hiringModal').classList.remove('flex');
  },

  renderHiringCandidates(candidates, filledRoles) {
    const container = document.getElementById('hiringCandidates');
    const roles = ['CTO', 'CMO', 'CFO', 'COO'];

    container.innerHTML = roles.map(role => {
      const roleCandidates = candidates.filter(c => c.role === role);
      const filled = filledRoles.includes(role);

      return `
        <div class="mb-4">
          <h3 class="text-sm font-bold text-slate-300 mb-2">${role} ${filled ? '<span class="text-game-green">(Filled)</span>' : ''}</h3>
          <div class="grid grid-cols-3 gap-2">
            ${roleCandidates.map(c => `
              <div class="hiring-card">
                <div class="font-bold text-sm">${c.name}</div>
                <div class="text-xs text-slate-400">${c.title}</div>
                <div class="text-xs text-slate-500 mt-1">${c.bio}</div>
                <div class="flex justify-between text-xs mt-2">
                  <span class="text-game-red">$${c.salary.toLocaleString()}/mo</span>
                  <span class="text-game-yellow">+${c.ap_bonus} AP</span>
                </div>
                <div class="text-xs text-slate-500 mt-1">Equity: ${c.equity_ask}%</div>
                <button onclick="game.hireCandidate('${c.id}')" class="w-full mt-2 bg-game-accent hover:bg-blue-600 text-xs py-1.5 rounded font-bold ${c.slot_filled ? 'opacity-30 cursor-not-allowed' : ''}" ${c.slot_filled ? 'disabled' : ''}>
                  Hire
                </button>
              </div>
            `).join('')}
          </div>
        </div>
      `;
    }).join('');
  },

  async hireCandidate(candidateId) {
    try {
      const res = await fetch(`${API}/api/game/${this.gameId}/hire`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ candidate_id: candidateId }),
      });
      const data = await res.json();
      if (data.hired) this.showToast(`Hired ${data.hired} as ${data.role}!`);
      this.closeHiringModal();
      await this.refreshState();
    } catch (e) { console.error('Hire failed:', e); }
  },

  async fireStaff(staffId) {
    if (!confirm('Are you sure you want to fire this executive?')) return;
    try {
      await fetch(`${API}/api/game/${this.gameId}/fire`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ staff_id: staffId }),
      });
      await this.refreshState();
    } catch (e) { console.error('Fire failed:', e); }
  },

  // ═══════════════════════════════════════════════════════
  // FUNDING
  // ═══════════════════════════════════════════════════════

  async openFundingModal() {
    try {
      const res = await fetch(`${API}/api/game/${this.gameId}/funding`);
      const data = await res.json();
      this.renderFundingOffer(data);
      document.getElementById('fundingModal').classList.remove('hidden');
      document.getElementById('fundingModal').classList.add('flex');
    } catch (e) { console.error('Load funding failed:', e); }
  },

  closeFundingModal() {
    document.getElementById('fundingModal').classList.add('hidden');
    document.getElementById('fundingModal').classList.remove('flex');
  },

  renderFundingOffer(data) {
    const container = document.getElementById('fundingContent');
    const offer = data.offer;

    if (!offer) {
      container.innerHTML = '<p class="text-slate-400">You are already at the maximum funding stage.</p>';
      return;
    }

    if (!offer.available) {
      container.innerHTML = `
        <div class="text-center">
          <div class="text-3xl mb-2">🔒</div>
          <div class="text-slate-400">Next: <strong>${offer.label}</strong></div>
          <div class="text-sm text-game-red mt-2">${offer.reason}</div>
        </div>
      `;
      return;
    }

    container.innerHTML = `
      <div class="text-center space-y-3">
        <div class="text-3xl">💰</div>
        <div class="text-xl font-bold">${offer.label}</div>
        <div class="text-game-green text-2xl font-black">$${offer.amount.toLocaleString()}</div>
        <div class="text-sm text-slate-400">For <span class="text-game-red font-bold">${offer.equity}% equity</span></div>
        <div class="text-xs text-slate-500">Post-money valuation: $${offer.post_money_valuation.toLocaleString()}</div>
        <button onclick="game.acceptFunding()" class="w-full bg-game-green hover:bg-green-600 text-white font-bold py-3 rounded-lg mt-4">Accept Funding</button>
      </div>
    `;
  },

  async acceptFunding() {
    try {
      const res = await fetch(`${API}/api/game/${this.gameId}/raise_funding`, { method: 'POST' });
      const data = await res.json();
      this.showToast(`💰 Raised funding! New stage: ${data.new_stage}`);
      this.closeFundingModal();
      await this.refreshState();
    } catch (e) { console.error('Raise funding failed:', e); }
  },

  // ═══════════════════════════════════════════════════════
  // RENDERING
  // ═══════════════════════════════════════════════════════

  render() {
    if (!this.state) return;
    const s = this.state;

    // Header
    document.getElementById('quarterBadge').textContent = `Q${s.current_quarter}/8`;
    document.getElementById('phaseBadge').textContent = s.phase.charAt(0).toUpperCase() + s.phase.slice(1).replace('_', ' ');
    document.getElementById('headerCash').textContent = this.fmtMoney(s.cash);
    document.getElementById('headerRunway').textContent = s.runway_months >= 99 ? '∞' : `${s.runway_months}mo`;
    document.getElementById('headerValuation').textContent = this.fmtMoney(s.valuation);
    document.getElementById('headerAP').textContent = `${s.ap_available}/${s.ap_base + s.ap_bonus}`;

    // Market badge
    const marketBadge = document.getElementById('marketBadge');
    marketBadge.textContent = s.market_condition.replace(/_/g, ' ');

    // Financials
    document.getElementById('finCash').textContent = this.fmtMoney(s.cash);
    document.getElementById('finBurn').textContent = this.fmtMoney(s.burn_rate) + '/mo';
    document.getElementById('finRevenue').textContent = this.fmtMoney(s.revenue) + '/mo';
    document.getElementById('finRunway').textContent = s.runway_months >= 99 ? 'Profitable ∞' : `${s.runway_months} months`;
    document.getElementById('finValuation').textContent = this.fmtMoney(s.valuation);
    document.getElementById('finStage').textContent = s.funding_stage.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase());
    document.getElementById('finEquity').textContent = `${s.equity_given.toFixed(1)}%`;

    // Color coding
    document.getElementById('finCash').className = `font-bold ${s.cash > 100000 ? 'text-game-green' : s.cash > 50000 ? 'text-game-yellow' : 'text-game-red'}`;
    document.getElementById('headerRunway').className = `font-bold ${s.runway_months >= 12 ? 'text-game-green' : s.runway_months >= 6 ? 'text-game-yellow' : 'text-game-red'}`;

    // Phase buttons
    const isEvents = s.phase === 'events' || s.phase === 'advise';
    const isQuarterEnd = s.phase === 'quarter_end';
    const isBoardReview = s.phase === 'board_review';

    document.getElementById('skipEventsBtn').classList.toggle('hidden', !isEvents || !s.current_events?.length);
    document.getElementById('endQuarterBtn').classList.toggle('hidden', !isQuarterEnd);
    document.getElementById('boardReviewBtn').classList.toggle('hidden', !isBoardReview);

    // Events
    this.renderEvents(s);

    // Stats
    this.renderStats(s.stats);

    // Milestones
    this.renderMilestones(s.milestones);

    // Rivals
    this.renderRivals(s.rivals);

    // Staff
    this.renderStaff(s.staff);

    // Partners
    document.getElementById('partnerCeleb').textContent = s.celebrity?.name || '—';
    document.getElementById('partnerProf').textContent = s.professor?.name || '—';
    const synergyBadges = document.getElementById('synergyBadges');
    synergyBadges.innerHTML = (s.synergy_names || []).map(n =>
      `<span class="text-xs bg-purple-500/20 text-purple-400 px-2 py-0.5 rounded-full">${n}</span>`
    ).join('');

    // Probability
    const prob = Math.round((s.success_probability || 0.5) * 100);
    const probCircle = document.getElementById('probCircle');
    probCircle.textContent = `${prob}%`;
    probCircle.className = `w-12 h-12 rounded-full border-4 flex items-center justify-center text-sm font-bold ${
      prob >= 60 ? 'border-game-green text-game-green' : prob >= 40 ? 'border-game-yellow text-game-yellow' : 'border-game-red text-game-red'
    }`;
  },

  renderEvents(s) {
    const container = document.getElementById('eventCards');
    const noMsg = document.getElementById('noEventsMsg');
    const events = s.current_events || [];

    if (events.length === 0 || s.phase === 'quarter_end' || s.phase === 'board_review') {
      container.innerHTML = '';
      noMsg.classList.remove('hidden');
      return;
    }

    noMsg.classList.add('hidden');

    // Only show the pending event (first in list)
    const ev = s.pending_event || events[0];
    if (!ev) { container.innerHTML = ''; return; }

    container.innerHTML = `
      <div class="event-card animate-fade-in">
        <div class="event-card-header">
          <div class="event-card-dept">${ev.department}${ev.is_shock ? ' • SHOCK' : ''}</div>
          <div class="event-card-title">${ev.title}</div>
          <div class="event-card-desc">${ev.description}</div>
          <div class="text-xs text-slate-500 mt-2">Events remaining: ${events.length}</div>
        </div>
        <div class="event-card-choices">
          ${(ev.choices || []).map((c, i) => `
            <button class="choice-btn" onclick="game.chooseEvent('${ev.id}', ${i})" ${s.ap_available < c.ap_cost ? 'disabled' : ''}>
              <span>${c.text}</span>
              <span class="ap-cost">${c.ap_cost} AP</span>
            </button>
          `).join('')}
          <button class="choice-btn" onclick="game.askAdvisors('${ev.title}')" style="border-color: #7c3aed;">
            <span>💬 Ask Advisors</span>
            <span class="ap-cost" style="color: #a855f7;">FREE</span>
          </button>
        </div>
      </div>
    `;
  },

  renderStats(stats) {
    const container = document.getElementById('statBars');
    const maxStat = 30;

    container.innerHTML = Object.entries(stats || {}).map(([key, val]) => {
      const pct = Math.min(100, (val / maxStat) * 100);
      return `
        <div class="stat-bar-container">
          <div class="stat-bar-label">${key}</div>
          <div class="stat-bar-track">
            <div class="stat-bar-fill ${key}" style="width: ${pct}%"></div>
          </div>
          <div class="stat-bar-value">${val}</div>
        </div>
      `;
    }).join('');
  },

  renderMilestones(milestones) {
    const container = document.getElementById('milestoneList');
    if (!milestones || milestones.length === 0) {
      container.innerHTML = '<div class="text-xs text-slate-500">No milestones</div>';
      return;
    }

    container.innerHTML = milestones.map(m => `
      <div class="milestone-item ${m.completed ? 'completed' : ''}">
        <div class="milestone-icon ${m.completed ? 'completed' : 'pending'}">${m.completed ? '✓' : m.tier[0].toUpperCase()}</div>
        <div>
          <div class="text-xs font-bold ${m.completed ? 'text-game-green' : 'text-slate-300'}">${m.name}</div>
          <div class="text-xs text-slate-500">${m.description}</div>
          ${m.completed ? `<div class="text-xs text-game-green mt-1">Completed Q${m.completed_quarter}</div>` : ''}
        </div>
      </div>
    `).join('');
  },

  renderRivals(rivals) {
    const container = document.getElementById('rivalList');
    if (!rivals || rivals.length === 0) {
      container.innerHTML = '<div class="text-xs text-slate-500">No rivals</div>';
      return;
    }

    container.innerHTML = rivals.map(r => `
      <div class="rival-item">
        <div>
          <div class="font-bold text-xs">${r.name}</div>
          <div class="text-xs text-slate-500">${r.ceo}</div>
        </div>
        <div class="flex items-center gap-2">
          <span class="text-xs font-bold">${r.score}pts</span>
          <span class="rival-momentum ${r.momentum}">${r.momentum}</span>
        </div>
      </div>
    `).join('');
  },

  renderStaff(staff) {
    const container = document.getElementById('staffList');
    if (!staff || staff.length === 0) {
      container.innerHTML = '<div class="text-slate-500 italic text-xs">No executives hired yet</div>';
      return;
    }

    container.innerHTML = staff.map(s => `
      <div class="flex items-center justify-between bg-game-card rounded-lg p-2">
        <div>
          <div class="font-bold text-xs">${s.name}</div>
          <div class="text-xs text-slate-500">${s.role} • $${s.salary.toLocaleString()}/mo</div>
        </div>
        <button onclick="game.fireStaff('${s.id}')" class="text-game-red text-xs hover:text-red-400">Fire</button>
      </div>
    `).join('');
  },

  // ═══════════════════════════════════════════════════════
  // CHAT
  // ═══════════════════════════════════════════════════════

  askAdvisors(eventTitle) {
    const input = document.getElementById('chatInput');
    input.value = `What should I do about "${eventTitle}"?`;
    input.focus();
  },

  addChatBubble(role, speaker, content) {
    const container = document.getElementById('chatMessages');
    // Remove placeholder text
    const placeholder = container.querySelector('.italic');
    if (placeholder) placeholder.remove();

    const bubble = document.createElement('div');
    bubble.className = `chat-bubble ${role} animate-fade-in`;
    bubble.innerHTML = `<div class="speaker">${speaker}</div><div>${content}</div>`;
    container.appendChild(bubble);
    container.scrollTop = container.scrollHeight;
  },

  // ═══════════════════════════════════════════════════════
  // MODALS
  // ═══════════════════════════════════════════════════════

  showQuarterSummary(summary) {
    const modal = document.getElementById('quarterSummaryModal');
    document.getElementById('summaryTitle').textContent = `Quarter ${summary.quarter} Summary`;

    const content = document.getElementById('summaryContent');
    content.innerHTML = `
      <div class="text-lg font-bold">${summary.headline}</div>
      <div class="flex items-center gap-2 text-sm">
        <span>${summary.market_emoji}</span>
        <span>Market: <strong>${summary.market_condition}</strong></span>
      </div>
      <div class="grid grid-cols-2 gap-3 text-sm">
        <div class="bg-game-card rounded-lg p-3">
          <div class="text-slate-400">Cash</div>
          <div class="font-bold ${summary.cash > 0 ? 'text-game-green' : 'text-game-red'}">${this.fmtMoney(summary.cash)}</div>
        </div>
        <div class="bg-game-card rounded-lg p-3">
          <div class="text-slate-400">Valuation</div>
          <div class="font-bold text-game-purple">${this.fmtMoney(summary.valuation)}</div>
        </div>
        <div class="bg-game-card rounded-lg p-3">
          <div class="text-slate-400">Revenue</div>
          <div class="font-bold">${this.fmtMoney(summary.revenue)}/mo</div>
        </div>
        <div class="bg-game-card rounded-lg p-3">
          <div class="text-slate-400">Runway</div>
          <div class="font-bold">${summary.runway_months >= 99 ? '∞' : summary.runway_months + ' months'}</div>
        </div>
      </div>
      <div class="text-sm">
        <div class="font-bold text-slate-300 mb-1">Milestones: ${summary.milestones_completed}/${summary.milestones_total}</div>
      </div>
      ${summary.shock ? `
        <div class="bg-game-red/10 border border-game-red/30 rounded-lg p-3 text-sm">
          <div class="font-bold text-game-red">⚡ ${summary.shock.name}</div>
          <div class="text-slate-400">${summary.shock.description}</div>
        </div>
      ` : ''}
      <div class="space-y-1">
        <div class="text-xs font-bold text-slate-400 uppercase">Rival Activity</div>
        ${(summary.rival_news || []).map(r => `
          <div class="text-xs text-slate-400">
            <span class="font-bold text-slate-300">${r.name}</span> (${r.score}pts, ${r.momentum}) — ${r.news}
          </div>
        `).join('')}
      </div>
    `;

    modal.classList.remove('hidden');
    modal.classList.add('flex');
  },

  closeSummaryModal() {
    const modal = document.getElementById('quarterSummaryModal');
    modal.classList.add('hidden');
    modal.classList.remove('flex');
  },

  showGameOver() {
    const s = this.state;
    const modal = document.getElementById('gameOverModal');
    const reason = s.game_over_reason || 'unknown';

    const reasonMap = {
      'bankruptcy': { emoji: '💀', title: 'Bankrupt!', desc: 'You ran out of cash. The startup is dead.' },
      'all_milestones_completed': { emoji: '🏆', title: 'Victory!', desc: 'You completed all milestones! Incredible.' },
      'time_up_survived': { emoji: '⏰', title: 'Time\'s Up', desc: 'You survived 8 quarters but didn\'t complete all milestones.' },
      'time_up_bankrupt': { emoji: '💀', title: 'Time\'s Up & Broke', desc: 'Game over. Ran out of time and money.' },
    };
    const r = reasonMap[reason] || { emoji: '🎮', title: 'Game Over', desc: reason };

    document.getElementById('gameOverEmoji').textContent = r.emoji;
    document.getElementById('gameOverTitle').textContent = r.title;
    document.getElementById('gameOverReason').textContent = r.desc;
    document.getElementById('gameOverStats').innerHTML = `
      <div>Final Cash: <strong>${this.fmtMoney(s.cash)}</strong></div>
      <div>Final Valuation: <strong>${this.fmtMoney(s.valuation)}</strong></div>
      <div>Milestones: <strong>${s.milestones_completed}/3</strong></div>
      <div>Quarters Played: <strong>${s.current_quarter}</strong></div>
      <div>Success Probability: <strong>${Math.round(s.success_probability * 100)}%</strong></div>
    `;

    modal.classList.remove('hidden');
    modal.classList.add('flex');
  },

  // ═══════════════════════════════════════════════════════
  // UTILITIES
  // ═══════════════════════════════════════════════════════

  fmtMoney(amount) {
    if (amount >= 1000000) return `$${(amount / 1000000).toFixed(1)}M`;
    if (amount >= 1000) return `$${Math.round(amount).toLocaleString()}`;
    return `$${Math.round(amount)}`;
  },

  showToast(message) {
    const existing = document.querySelector('.reaction-toast');
    if (existing) existing.remove();

    const toast = document.createElement('div');
    toast.className = 'reaction-toast';
    toast.textContent = message;
    document.body.appendChild(toast);
    setTimeout(() => toast.remove(), 4000);
  },
};

// ── Boot ──
document.addEventListener('DOMContentLoaded', () => game.init());
