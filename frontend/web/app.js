/**
 * ESADE Entrepreneurs — 8-Quarter Startup Simulation
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
        <div class="text-xs text-slate-400 mt-1">Cost: ${p.cost}/10</div>
      `;
      card.addEventListener('click', () => this.selectPartner(type, p.name, card, containerId));
      container.appendChild(card);
    });
  },

  selectPartner(type, name, card, containerId) {
    document.querySelectorAll(`#${containerId} .partner-card`).forEach(c => c.classList.remove('selected'));
    card.classList.add('selected');

    if (type === 'celebrity') this.selectedCelebrity = name;
    else this.selectedProfessor = name;

    const btn = document.getElementById('startGameBtn');
    btn.disabled = !(this.selectedCelebrity && this.selectedProfessor);

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
    details.innerHTML = `<span class="text-slate-700">${this.selectedCelebrity} + ${this.selectedProfessor}</span>`;
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
      btn.textContent = 'Launch Your Startup';
    }
  },

  // ═══════════════════════════════════════════════════════
  // GAME ACTIONS
  // ═══════════════════════════════════════════════════════

  async chooseEvent(eventId, choiceIndex) {
    // Disable all choice buttons while request is in flight
    document.querySelectorAll('.choice-btn').forEach(b => b.disabled = true);

    try {
      const res = await fetch(`${API}/api/game/${this.gameId}/choose_event`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ event_id: eventId, choice_index: choiceIndex }),
      });
      const data = await res.json();

      if (data.reaction) this.showToast(data.reaction);

      await this.refreshState();
    } catch (e) {
      console.error('Choose event failed:', e);
      // Re-enable buttons on error
      document.querySelectorAll('.choice-btn').forEach(b => b.disabled = false);
    }
  },

  async skipEvents() {
    const btn = document.getElementById('skipEventsBtn');
    btn.disabled = true;
    btn.textContent = 'Skipping...';
    try {
      await fetch(`${API}/api/game/${this.gameId}/skip_events`, { method: 'POST' });
      await this.refreshState();
    } catch (e) {
      console.error('Skip events failed:', e);
    } finally {
      btn.disabled = false;
      btn.textContent = 'Skip Events';
    }
  },

  async endQuarter() {
    const btn = document.getElementById('endQuarterBtn');
    btn.disabled = true;
    btn.textContent = 'Processing...';
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
    } catch (e) {
      console.error('End quarter failed:', e);
    } finally {
      btn.disabled = false;
      btn.textContent = 'End Quarter';
    }
  },

  async boardReview() {
    // Legacy shim — now delegates to openBoardReview
    return this.openBoardReview();
  },

  // ═══════════════════════════════════════════════════════
  // BOARD REVIEW CHAT (Feature 3)
  // ═══════════════════════════════════════════════════════

  async openBoardReview() {
    const btn = document.getElementById('boardReviewBtn');
    btn.disabled = true;
    btn.textContent = 'Connecting...';

    try {
      const res = await fetch(`${API}/api/game/${this.gameId}/board_review`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
      });
      const data = await res.json();

      this.state = data.state;

      // Open modal
      document.getElementById('boardModal').classList.remove('hidden');
      document.getElementById('boardModal').classList.add('flex');
      document.getElementById('boardModalTitle').textContent = `Board Review — Q${data.quarter}/8`;
      document.getElementById('boardVCName').textContent = data.vc_name;
      document.getElementById('boardPartnerName').textContent = data.partner_name;

      // Clear chat and add VC opening
      document.getElementById('boardChatMessages').innerHTML = '';
      this.addBoardBubble('vc', data.vc_name, data.vc_message);

      // Reset verdict area and inputs
      document.getElementById('boardVerdict').classList.add('hidden');
      document.getElementById('boardVerdict').innerHTML = '';
      document.getElementById('boardChatInput').disabled = false;
      document.getElementById('boardSendBtn').disabled = false;
      document.getElementById('boardChatInput').value = '';
      document.getElementById('boardChatInput').focus();

    } catch (e) {
      console.error('Board review failed:', e);
      this.showToast('Could not connect to board. Please try again.');
    } finally {
      btn.disabled = false;
      btn.textContent = '🏛️ Board Review';
    }
  },

  async sendBoardMessage() {
    const input = document.getElementById('boardChatInput');
    const btn = document.getElementById('boardSendBtn');
    const message = input.value.trim();
    if (!message || btn.disabled) return;

    input.value = '';
    btn.disabled = true;
    input.disabled = true;

    this.addBoardBubble('user', 'You', message);

    // Typing indicator
    const typingId = 'typing_' + Date.now();
    document.getElementById('boardChatMessages').insertAdjacentHTML('beforeend',
      `<div id="${typingId}" class="text-xs text-slate-400 italic p-2 animate-pulse">Board is deliberating...</div>`
    );

    try {
      const res = await fetch(`${API}/api/game/${this.gameId}/board_chat`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ message }),
      });
      const data = await res.json();

      document.getElementById(typingId)?.remove();

      this.addBoardBubble('vc', data.vc_name, data.vc_response);
      this.addBoardBubble('partner', data.partner_name, data.partner_response);

      this.state = data.state;
      this.render();

      if (data.verdict) {
        this.showBoardVerdict(data.verdict, data.outcome);
      } else {
        btn.disabled = false;
        input.disabled = false;
        input.focus();
      }
    } catch (e) {
      document.getElementById(typingId)?.remove();
      console.error('Board chat failed:', e);
      btn.disabled = false;
      input.disabled = false;
    }
  },

  addBoardBubble(role, speaker, content) {
    const container = document.getElementById('boardChatMessages');
    const isUser = role === 'user';
    const bubble = document.createElement('div');
    bubble.className = `flex ${isUser ? 'justify-end' : 'justify-start'} mb-3 animate-fade-in`;

    const colors = {
      vc: 'bg-red-50 border-red-200 text-red-900',
      partner: 'bg-teal-50 border-teal-200 text-teal-900',
      user: 'bg-blue-50 border-blue-200 text-blue-900',
    };

    bubble.innerHTML = `
      <div class="max-w-[80%] rounded-xl border p-3 text-sm ${colors[role] || colors.user}">
        <div class="font-bold text-xs opacity-70 mb-1">${speaker}</div>
        <div>${content}</div>
      </div>`;
    container.appendChild(bubble);
    container.scrollTop = container.scrollHeight;
  },

  showBoardVerdict(verdict, outcome) {
    const verdictEl = document.getElementById('boardVerdict');
    const colors = {
      IMPRESSED: 'bg-green-100 border-green-400 text-green-800',
      NEUTRAL: 'bg-yellow-100 border-yellow-400 text-yellow-800',
      CONCERNED: 'bg-red-100 border-red-400 text-red-800',
    };
    const icons = { IMPRESSED: '🚀', NEUTRAL: '🤝', CONCERNED: '⚠️' };

    verdictEl.className = `mt-2 p-4 rounded-xl border text-center ${colors[verdict] || colors.NEUTRAL}`;
    verdictEl.innerHTML = `
      <div class="text-2xl mb-1">${icons[verdict] || '🤝'}</div>
      <div class="font-bold text-sm uppercase tracking-wide">${verdict}</div>
      <div class="text-xs mt-1 opacity-80">${outcome?.effect || ''}</div>
      <button onclick="game.closeBoardModal()" class="mt-3 px-5 py-2 bg-white rounded-lg text-sm font-semibold shadow-sm hover:shadow-md border border-slate-200 transition-all">Continue →</button>`;
    verdictEl.classList.remove('hidden');

    document.getElementById('boardChatInput').disabled = true;
    document.getElementById('boardSendBtn').disabled = true;
  },

  closeBoardModal() {
    document.getElementById('boardModal').classList.add('hidden');
    document.getElementById('boardModal').classList.remove('flex');
    this.render();
  },

  // ═══════════════════════════════════════════════════════
  // END-OF-GAME DEBRIEF (Feature 1)
  // ═══════════════════════════════════════════════════════

  async showDebrief() {
    document.getElementById('debriefModal').classList.remove('hidden');
    document.getElementById('debriefModal').classList.add('flex');
    document.getElementById('debriefContent').innerHTML =
      '<div class="text-center text-slate-500 py-12"><div class="text-3xl mb-3 animate-pulse">⏳</div><div class="font-medium">Generating your debrief...</div><div class="text-xs text-slate-400 mt-1">This takes a moment — your full journey is being analysed.</div></div>';

    try {
      const res = await fetch(`${API}/api/game/${this.gameId}/debrief`, { method: 'POST' });
      const data = await res.json();

      // Render markdown-like text into styled HTML
      const html = (data.debrief || 'No debrief available.')
        .replace(/## (.+)/g, '<h3 class="text-base font-black text-slate-800 mt-6 mb-2 pb-1 border-b border-slate-100">$1</h3>')
        .replace(/^- (.+)/gm, '<li class="ml-4 text-slate-700 mb-1.5 list-none flex gap-2"><span class="text-slate-400 flex-shrink-0">•</span><span>$1</span></li>')
        .replace(/\n\n/g, '</p><p class="mb-3">')
        .replace(/\n/g, '<br>');

      document.getElementById('debriefContent').innerHTML =
        `<div class="prose-like">${html}</div>`;
    } catch (e) {
      document.getElementById('debriefContent').innerHTML =
        '<p class="text-red-500 text-center py-8">Could not generate debrief. Please try again.</p>';
    }
  },

  closeDebrief() {
    document.getElementById('debriefModal').classList.add('hidden');
    document.getElementById('debriefModal').classList.remove('flex');
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
  // ADVISORY CHAT — two separate boxes
  // ═══════════════════════════════════════════════════════

  async sendCelebrityChat() {
    const input = document.getElementById('celebChatInput');
    const btn = document.getElementById('celebChatBtn');
    const spinner = document.getElementById('celebChatSpinner');
    const message = input.value.trim();
    if (!message || btn.disabled) return;

    input.value = '';
    btn.disabled = true;
    spinner.classList.remove('hidden');

    // Show user message in celebrity panel
    this.addCelebChatBubble('user', 'You', message);

    try {
      const res = await fetch(`${API}/api/game/${this.gameId}/chat/celebrity`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ message }),
      });
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      const data = await res.json();
      this.addCelebChatBubble('celebrity', data.speaker, data.content);
    } catch (e) {
      console.error('Celebrity chat failed:', e);
      this.addCelebChatBubble('system', 'System', 'Could not reach celebrity advisor. Please try again.');
    } finally {
      btn.disabled = false;
      spinner.classList.add('hidden');
    }
  },

  async sendProfessorChat() {
    const input = document.getElementById('profChatInput');
    const btn = document.getElementById('profChatBtn');
    const spinner = document.getElementById('profChatSpinner');
    const message = input.value.trim();
    if (!message || btn.disabled) return;

    input.value = '';
    btn.disabled = true;
    spinner.classList.remove('hidden');

    // Show user message in professor panel
    this.addProfChatBubble('user', 'You', message);

    try {
      const res = await fetch(`${API}/api/game/${this.gameId}/chat/professor`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ message }),
      });
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      const data = await res.json();
      this.addProfChatBubble('professor', data.speaker, data.content);
    } catch (e) {
      console.error('Professor chat failed:', e);
      this.addProfChatBubble('system', 'System', 'Could not reach professor advisor. Please try again.');
    } finally {
      btn.disabled = false;
      spinner.classList.add('hidden');
    }
  },

  addCelebChatBubble(role, speaker, content) {
    const container = document.getElementById('celebChatMessages');
    const placeholder = container.querySelector('.italic');
    if (placeholder) placeholder.remove();

    const bubble = document.createElement('div');
    bubble.className = `chat-bubble ${role} animate-fade-in`;
    bubble.innerHTML = `<div class="speaker">${speaker}</div><div>${content}</div>`;
    container.appendChild(bubble);
    container.scrollTop = container.scrollHeight;
  },

  addProfChatBubble(role, speaker, content) {
    const container = document.getElementById('profChatMessages');
    const placeholder = container.querySelector('.italic');
    if (placeholder) placeholder.remove();

    const bubble = document.createElement('div');
    bubble.className = `chat-bubble ${role} animate-fade-in`;
    bubble.innerHTML = `<div class="speaker">${speaker}</div><div>${content}</div>`;
    container.appendChild(bubble);
    container.scrollTop = container.scrollHeight;
  },

  // Pre-fill both chat boxes when "Ask Advisors" is clicked on an event card
  askAdvisors(eventTitle) {
    const question = `What should I do about "${eventTitle}"?`;
    document.getElementById('celebChatInput').value = question;
    document.getElementById('profChatInput').value = question;
    document.getElementById('celebChatInput').focus();
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
          <h3 class="text-sm font-bold text-slate-600 mb-2">${role} ${filled ? '<span class="text-green-600">(Filled)</span>' : ''}</h3>
          <div class="grid grid-cols-3 gap-2">
            ${roleCandidates.map(c => `
              <div class="hiring-card">
                <div class="font-bold text-sm text-slate-800">${c.name}</div>
                <div class="text-xs text-slate-500">${c.title}</div>
                <div class="text-xs text-slate-400 mt-1">${c.bio}</div>
                <div class="flex justify-between text-xs mt-2">
                  <span class="text-red-600">$${c.salary.toLocaleString()}/mo</span>
                  <span class="text-amber-600">+${c.ap_bonus} AP</span>
                </div>
                <div class="text-xs text-slate-400 mt-1">Equity: ${c.equity_ask}%</div>
                <button onclick="game.hireCandidate('${c.id}')" class="w-full mt-2 bg-blue-600 hover:bg-blue-700 text-white text-xs py-1.5 rounded font-bold transition-colors ${c.slot_filled ? 'opacity-30 cursor-not-allowed' : ''}" ${c.slot_filled ? 'disabled' : ''}>
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
      container.innerHTML = '<p class="text-slate-500">You are already at the maximum funding stage.</p>';
      return;
    }

    if (!offer.available) {
      container.innerHTML = `
        <div class="text-center">
          <div class="text-3xl mb-2">🔒</div>
          <div class="text-slate-500">Next: <strong class="text-slate-700">${offer.label}</strong></div>
          <div class="text-sm text-red-600 mt-2">${offer.reason}</div>
        </div>
      `;
      return;
    }

    container.innerHTML = `
      <div class="text-center space-y-3">
        <div class="text-3xl">💰</div>
        <div class="text-xl font-bold text-slate-800">${offer.label}</div>
        <div class="text-green-600 text-2xl font-black">$${offer.amount.toLocaleString()}</div>
        <div class="text-sm text-slate-500">For <span class="text-red-600 font-bold">${offer.equity}% equity</span></div>
        <div class="text-xs text-slate-400">Post-money valuation: $${offer.post_money_valuation.toLocaleString()}</div>
        <button onclick="game.acceptFunding()" class="w-full bg-green-600 hover:bg-green-700 text-white font-bold py-3 rounded-lg mt-4 transition-colors">Accept Funding</button>
      </div>
    `;
  },

  async acceptFunding() {
    try {
      const res = await fetch(`${API}/api/game/${this.gameId}/raise_funding`, { method: 'POST' });
      const data = await res.json();
      this.showToast(`Raised funding! New stage: ${data.new_stage}`);
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
    const apTotal = s.ap_base + s.ap_bonus;
    const apLeft  = s.ap_available;
    document.getElementById('headerAP').textContent = `${apLeft}/${apTotal}`;

    // AP indicator pips
    const apFraction = document.getElementById('apFraction');
    const apPips     = document.getElementById('apPips');
    const apBarFill  = document.getElementById('apBarFill');
    if (apFraction && apPips && apBarFill) {
      apFraction.textContent = `${apLeft}/${apTotal}`;
      apFraction.className = `text-lg font-black ${apLeft > apTotal * 0.5 ? 'text-amber-500' : apLeft > 0 ? 'text-orange-500' : 'text-red-500'}`;
      // Render pips
      apPips.innerHTML = Array.from({length: apTotal}, (_, i) =>
        `<div class="w-5 h-5 rounded-full border-2 transition-all duration-300 ${i < apLeft ? 'bg-amber-400 border-amber-500' : 'bg-slate-100 border-slate-300'}"></div>`
      ).join('');
      // Bar fill
      const pct = apTotal > 0 ? Math.round((apLeft / apTotal) * 100) : 0;
      apBarFill.style.width = pct + '%';
      apBarFill.className = `h-full rounded-full transition-all duration-500 ${apLeft > apTotal * 0.5 ? 'bg-gradient-to-r from-amber-400 to-yellow-300' : apLeft > 0 ? 'bg-gradient-to-r from-orange-400 to-amber-300' : 'bg-red-400'}`;
    }

    // Market badge
    document.getElementById('marketBadge').textContent = s.market_condition.replace(/_/g, ' ');

    // Financials
    document.getElementById('finCash').textContent = this.fmtMoney(s.cash);
    document.getElementById('finBurn').textContent = this.fmtMoney(s.burn_rate) + '/mo';
    document.getElementById('finRevenue').textContent = this.fmtMoney(s.revenue) + '/mo';
    document.getElementById('finRunway').textContent = s.runway_months >= 99 ? 'Profitable ∞' : `${s.runway_months} months`;
    document.getElementById('finValuation').textContent = this.fmtMoney(s.valuation);
    document.getElementById('finStage').textContent = s.funding_stage.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase());
    document.getElementById('finEquity').textContent = `${s.equity_given.toFixed(1)}%`;

    // Color-code cash
    const cashEl = document.getElementById('finCash');
    cashEl.className = `font-bold ${s.cash > 100000 ? 'text-game-green' : s.cash > 50000 ? 'text-game-yellow' : 'text-game-red'}`;
    const runwayEl = document.getElementById('headerRunway');
    runwayEl.className = `font-bold ${s.runway_months >= 12 ? 'text-game-green' : s.runway_months >= 6 ? 'text-game-yellow' : 'text-game-red'}`;

    // Phase buttons
    const isEvents = s.phase === 'events' || s.phase === 'advise';
    const isQuarterEnd = s.phase === 'quarter_end';
    const isBoardReview = s.phase === 'board_review';

    document.getElementById('skipEventsBtn').classList.toggle('hidden', !isEvents || !s.current_events?.length);
    document.getElementById('endQuarterBtn').classList.toggle('hidden', !isQuarterEnd);
    document.getElementById('boardReviewBtn').classList.toggle('hidden', !isBoardReview);

    // Advisor names in chat headers
    if (s.celebrity?.name) document.getElementById('celebAdvisorName').textContent = s.celebrity.name;
    if (s.professor?.name) document.getElementById('profAdvisorName').textContent = s.professor.name;

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

    // Partners panel
    document.getElementById('partnerCeleb').textContent = s.celebrity?.name || '—';
    document.getElementById('partnerProf').textContent = s.professor?.name || '—';
    const synergyBadges = document.getElementById('synergyBadges');
    synergyBadges.innerHTML = (s.synergy_names || []).map(n =>
      `<span class="text-xs bg-purple-100 text-purple-700 px-2 py-0.5 rounded-full">${n}</span>`
    ).join('');

    // Success probability
    const prob = Math.round((s.success_probability || 0.5) * 100);
    const probCircle = document.getElementById('probCircle');
    probCircle.textContent = `${prob}%`;
    probCircle.className = `w-12 h-12 rounded-full border-4 flex items-center justify-center text-sm font-bold ${
      prob >= 60 ? 'border-green-500 text-green-600' : prob >= 40 ? 'border-amber-500 text-amber-600' : 'border-red-500 text-red-600'
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

    const ev = s.pending_event || events[0];
    if (!ev) { container.innerHTML = ''; return; }

    container.innerHTML = `
      <div class="event-card animate-fade-in">
        <div class="event-card-header">
          <div class="event-card-dept">${ev.department}${ev.is_shock ? ' • SHOCK' : ''}</div>
          <div class="event-card-title">${ev.title}</div>
          <div class="event-card-desc">${ev.description}</div>
          <div class="text-xs text-slate-400 mt-2">Events remaining: ${events.length}</div>
        </div>
        <div class="event-card-choices">
          ${(ev.choices || []).map((c, i) => `
            <button class="choice-btn" onclick="game.chooseEvent('${ev.id}', ${i})" ${s.ap_available < c.ap_cost ? 'disabled' : ''}>
              <span>${c.text}</span>
              <span class="ap-cost">${c.ap_cost} AP</span>
            </button>
          `).join('')}
          <button class="choice-btn ask-advisors-btn" onclick="game.askAdvisors('${ev.title.replace(/'/g, "\\'")}')">
            <span>💬 Ask Advisors</span>
            <span class="ap-cost" style="color: #7c3aed;">FREE</span>
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
      container.innerHTML = '<div class="text-xs text-slate-400">No milestones</div>';
      return;
    }

    container.innerHTML = milestones.map(m => `
      <div class="milestone-item ${m.completed ? 'completed' : ''}">
        <div class="milestone-icon ${m.completed ? 'completed' : 'pending'}">${m.completed ? '✓' : m.tier[0].toUpperCase()}</div>
        <div>
          <div class="text-xs font-bold ${m.completed ? 'text-green-600' : 'text-slate-700'}">${m.name}</div>
          <div class="text-xs text-slate-400">${m.description}</div>
          ${m.completed ? `<div class="text-xs text-green-600 mt-1">Completed Q${m.completed_quarter}</div>` : ''}
        </div>
      </div>
    `).join('');
  },

  renderRivals(rivals) {
    const container = document.getElementById('rivalList');
    if (!rivals || rivals.length === 0) {
      container.innerHTML = '<div class="text-xs text-slate-400">No rivals</div>';
      return;
    }

    container.innerHTML = rivals.map(r => `
      <div class="rival-item">
        <div>
          <div class="font-bold text-xs text-slate-700">${r.name}</div>
          <div class="text-xs text-slate-400">${r.ceo}</div>
        </div>
        <div class="flex items-center gap-2">
          <span class="text-xs font-bold text-slate-600">${r.score}pts</span>
          <span class="rival-momentum ${r.momentum}">${r.momentum}</span>
        </div>
      </div>
    `).join('');
  },

  renderStaff(staff) {
    const container = document.getElementById('staffList');
    if (!staff || staff.length === 0) {
      container.innerHTML = '<div class="text-slate-400 italic text-xs">No executives hired yet</div>';
      return;
    }

    container.innerHTML = staff.map(s => `
      <div class="flex items-center justify-between bg-slate-50 rounded-lg p-2 border border-slate-100">
        <div>
          <div class="font-bold text-xs text-slate-700">${s.name}</div>
          <div class="text-xs text-slate-400">${s.role} • $${s.salary.toLocaleString()}/mo</div>
        </div>
        <button onclick="game.fireStaff('${s.id}')" class="text-red-500 text-xs hover:text-red-700">Fire</button>
      </div>
    `).join('');
  },

  // ═══════════════════════════════════════════════════════
  // MODALS
  // ═══════════════════════════════════════════════════════

  showQuarterSummary(summary) {
    const modal = document.getElementById('quarterSummaryModal');
    document.getElementById('summaryTitle').textContent = `Quarter ${summary.quarter} Summary`;

    const content = document.getElementById('summaryContent');
    content.innerHTML = `
      <div class="text-lg font-bold text-slate-800">${summary.headline}</div>
      <div class="flex items-center gap-2 text-sm text-slate-600">
        <span>${summary.market_emoji}</span>
        <span>Market: <strong>${summary.market_condition}</strong></span>
      </div>
      <div class="grid grid-cols-2 gap-3 text-sm">
        <div class="bg-slate-50 rounded-lg p-3 border border-slate-200">
          <div class="text-slate-500">Cash</div>
          <div class="font-bold ${summary.cash > 0 ? 'text-green-600' : 'text-red-600'}">${this.fmtMoney(summary.cash)}</div>
        </div>
        <div class="bg-slate-50 rounded-lg p-3 border border-slate-200">
          <div class="text-slate-500">Valuation</div>
          <div class="font-bold text-purple-600">${this.fmtMoney(summary.valuation)}</div>
        </div>
        <div class="bg-slate-50 rounded-lg p-3 border border-slate-200">
          <div class="text-slate-500">Revenue</div>
          <div class="font-bold text-slate-700">${this.fmtMoney(summary.revenue)}/mo</div>
        </div>
        <div class="bg-slate-50 rounded-lg p-3 border border-slate-200">
          <div class="text-slate-500">Runway</div>
          <div class="font-bold text-slate-700">${summary.runway_months >= 99 ? '∞' : summary.runway_months + ' months'}</div>
        </div>
      </div>
      <div class="text-sm text-slate-600">
        <div class="font-bold mb-1">Milestones: ${summary.milestones_completed}/${summary.milestones_total}</div>
      </div>
      ${summary.shock ? `
        <div class="bg-red-50 border border-red-200 rounded-lg p-3 text-sm">
          <div class="font-bold text-red-600">⚡ ${summary.shock.name}</div>
          <div class="text-slate-500">${summary.shock.description}</div>
        </div>
      ` : ''}
      <div class="space-y-1">
        <div class="text-xs font-bold text-slate-500 uppercase">Rival Activity</div>
        ${(summary.rival_news || []).map(r => `
          <div class="text-xs text-slate-500">
            <span class="font-bold text-slate-600">${r.name}</span> (${r.score}pts, ${r.momentum}) — ${r.news}
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
      'time_up_survived': { emoji: '⏰', title: "Time's Up", desc: 'You survived 8 quarters but did not complete all milestones.' },
      'time_up_bankrupt': { emoji: '💀', title: "Time's Up & Broke", desc: 'Game over. Ran out of time and money.' },
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

  // ═══════════════════════════════════════════════════════
  // HOW TO PLAY MODAL
  // ═══════════════════════════════════════════════════════

  _htpTabs: ['overview', 'quarter', 'ap', 'advisors', 'financials', 'winning'],
  _htpCurrent: 0,

  openHowToPlay() {
    document.getElementById('howToPlayModal').classList.remove('hidden');
    document.getElementById('howToPlayModal').classList.add('flex');
    this._htpCurrent = 0;
    this._renderHTPTab();
  },

  closeHowToPlay() {
    document.getElementById('howToPlayModal').classList.add('hidden');
    document.getElementById('howToPlayModal').classList.remove('flex');
  },

  switchHTPTab(tabId) {
    const idx = this._htpTabs.indexOf(tabId);
    if (idx >= 0) { this._htpCurrent = idx; this._renderHTPTab(); }
  },

  nextHTPTab() {
    if (this._htpCurrent < this._htpTabs.length - 1) { this._htpCurrent++; this._renderHTPTab(); }
    else this.closeHowToPlay();
  },

  prevHTPTab() {
    if (this._htpCurrent > 0) { this._htpCurrent--; this._renderHTPTab(); }
  },

  _renderHTPTab() {
    const tabs  = this._htpTabs;
    const cur   = this._htpCurrent;

    // Show/hide panels
    tabs.forEach(t => {
      const panel = document.getElementById(`htp-${t}`);
      if (panel) panel.classList.toggle('hidden', t !== tabs[cur]);
    });

    // Active tab styling
    tabs.forEach(t => {
      const btn = document.getElementById(`htp-tab-${t}`);
      if (!btn) return;
      if (t === tabs[cur]) {
        btn.className = 'htp-tab htp-tab-active px-4 py-2 text-xs font-semibold whitespace-nowrap border-b-2 border-blue-600 text-blue-700 bg-blue-50';
      } else {
        btn.className = 'htp-tab px-4 py-2 text-xs font-semibold whitespace-nowrap text-slate-500 hover:text-slate-800 hover:bg-slate-50 transition-colors';
      }
    });

    // Dots
    const dotsEl = document.getElementById('htpDots');
    if (dotsEl) {
      dotsEl.innerHTML = tabs.map((_, i) =>
        `<div class="w-2 h-2 rounded-full transition-all ${i === cur ? 'bg-blue-600' : 'bg-slate-300'}"></div>`
      ).join('');
    }

    // Prev / Next button labels
    const prevBtn = document.getElementById('htpPrevBtn');
    const nextBtn = document.getElementById('htpNextBtn');
    if (prevBtn) prevBtn.disabled = cur === 0;
    if (nextBtn) nextBtn.textContent = cur === tabs.length - 1 ? 'Done ✓' : 'Next →';
  },
};

// ── Boot ──
document.addEventListener('DOMContentLoaded', () => game.init());
