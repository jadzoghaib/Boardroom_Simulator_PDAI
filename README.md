# ESADE Entrepreneurs — 8-Quarter Startup Simulation

A startup decision game built for ESADE MBA cohorts. Play as a founder through 8 quarters of events, advisor chats, hiring, fundraising, and board reviews — all powered by LLM agents and an ML success predictor.

---

## What It Is

- **8 quarters** (2 years) of startup decisions
- **Pre-written events** per quarter across Product, Growth, Brand, Tech, Ops, Finance departments
- **LLM advisory chat** — ask your Celebrity and Professor advisors anything before choosing
- **Market dynamics** — 7 market conditions (Boom, Recession, AI Hype, etc.) that shift each quarter
- **Rival simulation** — 3 sector competitors that gain momentum each quarter
- **Hiring system** — 4 exec slots (CTO, CMO, CFO, COO), each with 3 candidates
- **Fundraising** — 5 stages from Bootstrap → Angels → Seed → Series A → Series B
- **Milestones** — 3 sector-specific goals to achieve before Q8
- **ML prediction** — live success probability based on burn, revenue, experience, and sector
- **Board reviews** — VC/partner review at Q2, Q4, Q6, Q8

---

## Game Architecture & Flow

### 1. Full Game Lifecycle

```mermaid
flowchart TD
    A([Player opens UI]) --> B[Setup Screen\nChoose Founder · Country · Sector]
    B --> C[Choose Celebrity Advisor\n+ Professor Advisor]
    C --> D[POST /api/setup/founder\nCreates GameState in memory]
    D --> E[Game Board — Q1/8\nPhase: events]

    E --> F{Quarter Loop\nRepeats Q1–Q8}

    F --> G[Draw 2–3 Events\nfrom events.py]
    G --> H[Player reads event\nSees 3 choices + AP costs]
    H --> I{Ask Advisors?}
    I -- Yes --> J[Chat with Celebrity\nPOST /chat/celebrity\nGroq LLM + RAG]
    I -- Yes --> K[Chat with Professor\nPOST /chat/professor\nGroq LLM + RAG]
    J --> H
    K --> H
    I -- No --> L[Choose Option\nPOST /choose_event]
    L --> M[Apply stat deltas\nDeduct AP\nShow reaction toast]
    M --> N{More events\n+ AP remaining?}
    N -- Yes --> H
    N -- No --> O[Phase: quarter_end]

    O --> P{Optional Actions}
    P --> Q[Hire Exec\nPOST /hire\nAdds AP bonus + stat boost\nIncreases burn rate]
    P --> R[Raise Funding\nPOST /raise_funding\nInjects cash\nDilutes equity]
    P --> S[End Quarter\nPOST /end_quarter]

    S --> T[Engine: end_quarter\nDeduct burn · Add revenue\nSimulate rivals\nShift market condition\nCheck milestones\nCheck bankruptcy]
    T --> U[ML Predictor\nPOST /api/predict\nUpdates success %]
    T --> V[Quarter Summary Modal\nCash · Valuation · Rivals · Market]

    V --> W{Every 2 quarters?}
    W -- Yes --> X[Board Review\nPOST /board_review\nVC + Partner assessment]
    W -- No --> Y{Q8 done or\nbankrupt?}
    X --> Y
    Y -- No --> F
    Y -- Yes --> Z([Game Over / Win Screen])
```

---

### 2. Score & Stats System

```mermaid
flowchart LR
    subgraph Stats ["8 Startup Dimensions"]
        S1[Growth]
        S2[Brand]
        S3[Product]
        S4[Tech]
        S5[Ops]
        S6[Finance]
        S7[Innovation]
        S8[Execution]
    end

    subgraph Sources ["What changes stats"]
        E1[Event Choices\n±1–5 per stat]
        E2[Hired Execs\n+stat bonuses on hire]
        E3[Market Shocks\nmultiply revenue/burn]
    end

    subgraph Financials ["Financial Metrics"]
        F1[Cash\nStarts seeded from exp + country]
        F2[Burn Rate\n= base + exec salaries]
        F3[Revenue\n= base × market multiplier]
        F4[Runway\n= cash ÷ net burn]
        F5[Valuation\n= revenue × sector multiple]
    end

    subgraph AP ["Action Points per Quarter"]
        A1[Base: 6 AP]
        A2[+1 AP per hired exec]
        A3[Event choices cost 1–3 AP]
    end

    Sources --> Stats
    Stats --> F5
    F1 --> F4
    F2 --> F4
    F3 --> F4
    A1 --> AP
    A2 --> AP
    A3 --> AP
```

---

### 3. Advisory Chat — Backend Integration

```mermaid
flowchart TD
    U[Player types question] --> API[POST /chat/celebrity\nor /chat/professor]
    API --> T[asyncio.to_thread\nnon-blocking]

    T --> CTX[Build context\nCurrent event + choices\nGame financials\nMarket condition\nQuarter number]

    CTX --> RAG{RAG Retrieval\nChromaDB}
    RAG --> R1[Celebrity collection\nWikipedia articles\nsearch_celebrity_background]
    RAG --> R2[Professor collection\nESADE Faculty PDFs\nsearch_professor_background]

    R1 --> PROMPT[Build system prompt\nPersona + RAG context\n+ game state + event]
    R2 --> PROMPT

    PROMPT --> LLM[Groq API\nllama-3.3-70b-versatile\ntemp=0.7]
    LLM --> RESP[Response streamed back\nto chat bubble in UI]
```

---

### 4. ML Prediction — Backend Integration

```mermaid
flowchart LR
    G[GameState] -->|burn_rate\nrevenue\nfounder_experience\nsector| P[MarketPredictor\npredict_success_probability]
    P --> M[startup_best_model.pkl\nGradient Boosting classifier\ntrained on startup_funding_and_outcome.csv]
    M --> PROB[success_probability\n0.0 – 1.0]
    PROB --> UI[ML Prediction circle\nupdates every quarter]

    subgraph Features used
        F1[funding_rounds]
        F2[founder_experience_years]
        F3[team_size]
        F4[market_size_billion]
        F5[burn_rate_million]
        F6[revenue_million]
        F7[investor_type]
        F8[sector]
        F9[founder_background]
    end
```

---

### 5. Market & Rivals — Quarter End Engine

```mermaid
flowchart TD
    EQ[POST /end_quarter] --> B[Deduct burn rate\nAdd revenue]
    B --> MKT[Shift market condition\nMarkov chain transition\n7 possible states]
    MKT --> SHOCK{25% chance\nof market shock}
    SHOCK -- Yes --> SE[Apply shock event\nmodifies rev/burn multipliers]
    SHOCK -- No --> RIV
    SE --> RIV[Simulate rivals\neach gains 1–3 pts\nmarket-adjusted]
    RIV --> MIL[Check milestones\nstat thresholds met?]
    MIL --> BNK{Cash < 0?}
    BNK -- Yes --> GO[Game Over: Bankrupt]
    BNK -- No --> ADV[Advance quarter\nDraw new events]
    ADV --> ML[Run ML predictor\nUpdate success %]
    ML --> SUM[Return quarter summary\nto UI]
```

---

- Python 3.10+ (use the `.venv` in the project root — it has all dependencies)
- `GROQ_API_KEY` in a `.env` file

---

## Environment Setup

Copy `.env.example` to `.env` and set:

```env
GROQ_API_KEY=your_real_groq_api_key_here
```

---

## Running the Server

**Always use the project `.venv`** — the system Python does not have the required packages.

From the project root (Git Bash / WSL):

```bash
.venv/Scripts/uvicorn.exe src.api.main:app --host 127.0.0.1 --port 8002
```

Or on Windows CMD / PowerShell:

```cmd
.venv\Scripts\uvicorn.exe src.api.main:app --host 127.0.0.1 --port 8002
```

Then open:

```
http://127.0.0.1:8002/ui/index.html
```

> **Port 8000 is often occupied by ghost processes on Windows.** Use `--port 8002` (or any free port). If you change the port, just open the same port in the browser — `app.js` uses `window.location.origin` so it automatically uses whichever port serves the UI.

---

## How to Play

1. **Choose Your Founder** — select a classmate from the roster
2. **Pick a Country** — affects cost of living, burn rate, and initial budget
3. **Choose Partners** — pick 1 Celebrity advisor + 1 Professor advisor (synergy bonuses apply)
4. **Click "Launch Your Startup"** — game starts at Q1 in Events phase
5. **Resolve Events** — each quarter draws 2–3 decision events; spend AP to choose options
6. **Ask Advisors** — before choosing, chat with your Celebrity or Professor for LLM-powered advice
7. **Hire Execs** — open Hire Exec to fill CTO / CMO / CFO / COO slots (adds AP bonus + stat boosts)
8. **Raise Funding** — accept investor offers to top up cash at the cost of equity
9. **End Quarter** — review the quarter summary: market news, financials, rival activity
10. **Board Review** — every 2 quarters, the VC board reviews your progress
11. **Win** — complete all 3 milestones before Q8, or survive to the end

---

## Game Mechanics

### Action Points (AP)
- Start with 6 AP per quarter (+1 per hired exec)
- Each event choice costs 1–3 AP
- Unused AP is lost at end of quarter

### Stats (8 dimensions)
Growth · Brand · Product · Tech · Ops · Finance · Innovation · Execution

### Market Conditions
7 conditions with revenue/burn multipliers, updated each quarter via Markov chain:
`AI Hype` · `AI Winter` · `Regulation Wave` · `Talent War` · `Boom` · `Recession` · `Stable`

### Funding Stages
Bootstrap → Angels → Seed → Series A → Series B

---

## API Endpoints

### Setup
| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/api/setup/countries` | List all countries with cost-of-living data |
| `GET` | `/api/setup/classmates` | List classmate founders |
| `GET` | `/api/setup/classmate-intro?name=...` | Short bio from roster |
| `GET` | `/api/setup/celebrity-partners` | List celebrity advisors |
| `GET` | `/api/setup/professor-partners` | List professor advisors |
| `POST` | `/api/setup/founder` | Create a new game session → returns `game_id` |

### Game Loop
| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/api/game/{id}/state` | Full current game state |
| `POST` | `/api/game/{id}/choose_event` | Pick an event choice `{event_id, choice_index}` |
| `POST` | `/api/game/{id}/skip_events` | Skip remaining events this quarter |
| `POST` | `/api/game/{id}/chat/celebrity` | Chat with celebrity advisor |
| `POST` | `/api/game/{id}/chat/professor` | Chat with professor advisor |
| `POST` | `/api/game/{id}/end_quarter` | Finalize quarter, advance to next |
| `GET` | `/api/game/{id}/candidates` | List hireable candidates |
| `POST` | `/api/game/{id}/hire` | Hire a candidate `{candidate_id}` |
| `POST` | `/api/game/{id}/fire` | Fire a staff member `{staff_id}` |
| `GET` | `/api/game/{id}/funding` | Get current investor offer |
| `POST` | `/api/game/{id}/raise_funding` | Accept funding offer |
| `POST` | `/api/game/{id}/board_review` | Trigger VC board review |
| `GET` | `/api/game/{id}/quarter_summary` | Get last quarter summary |

---

## Key Files

### Frontend
| File | Purpose |
|------|---------|
| `frontend/web/index.html` | 3-column game board UI |
| `frontend/web/app.js` | Game engine — state management, all API calls, render loop |
| `frontend/web/styles.css` | Light theme — event cards, chat bubbles, stat bars, modals |

### Backend
| File | Purpose |
|------|---------|
| `src/api/main.py` | FastAPI app — all endpoints, game session store |
| `src/game/state.py` | `GameState` Pydantic model + `ChatMessage` |
| `src/game/engine.py` | Core game logic — events, quarter lifecycle, hiring, funding |
| `src/game/advisor.py` | LLM advisory chat — celebrity + professor Groq calls with RAG |
| `src/agents/graph.py` | LangGraph board review graph (VC + partner) |
| `src/agents/prompts.py` | System prompts for all LLM agents |
| `src/data/events.py` | ~150 pre-written decision events |
| `src/data/market.py` | 7 market conditions + Markov transitions + headlines |
| `src/data/rivals.py` | Rival companies + quarterly simulation |
| `src/data/hiring.py` | 12 exec candidates (3 per role) |
| `src/data/milestones.py` | 3 milestones per sector (15 total) |
| `src/data/founder_roster.py` | Classmate roster + partner definitions + synergy system |
| `src/data/vector_db.py` | ChromaDB — celebrity Wikipedia RAG + professor PDF RAG |
| `src/data/cost_of_living_data.py` | Country cost-of-living profiles |
| `src/ml/predictor.py` | ML success probability model |

### Data
| Path | Contents |
|------|----------|
| `data/classmates.csv` | Classmate roster with LinkedIn URLs |
| `data/ESADE Faculty/` | Professor PDFs (for RAG) |
| `src/data/chroma_db/` | Persisted ChromaDB vector collections |

---

## Notes

- **GROQ_API_KEY** is required for advisor chat and profile intro generation
- **ML model**: if `src/ml/models/startup_best_model.pkl` is missing, predictor falls back to a baseline estimate
- **Game sessions** are stored in-memory — restarting the server clears all active games
- **Always open a fresh browser tab** when starting a new session or after restarting the server. Reusing an old tab can leave stale HTTP connections that cause the game launch to hang silently
- **Advisory chat** is non-blocking (`asyncio.to_thread`) so the UI never freezes during LLM calls
- **LinkedIn profiles** are not fetched (LinkedIn blocks bots) — classmate intros come from the roster CSV
- On Windows, always use the `.venv` interpreter: `python -m pip` and `.venv/Scripts/uvicorn.exe`
