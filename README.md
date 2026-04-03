# Esade Entrepreneurs Boardroom Sim

Esade Entrepreneurs Boardroom Sim is a startup decision game that combines:

- structured setup generation (founder + country + partner synergy),
- an ML market physics pass (success probability + runway),
- a LangGraph boardroom conversation with VC and partner agents,
- retrieval-augmented partner advice using local playbooks and celebrity background knowledge.

## Current Features

### Founder setup

- Select a classmate founder, country, sector, and optional founder/cofounder background text.
- Startup metrics are seeded from experience, cost-of-living profile, and partner multipliers.

### Dual partner system

- You must choose both:
  - 1 celebrity co-founder
  - 1 professor partner
- Partner cards include avatar, description, domain, stats, strengths, and detail modal.
- Specific combinations unlock synergy bonuses that modify budget, burn, and revenue.
- Professor records include source file metadata (LinkedIn PDF + faculty profile PDF).

### Founder intro generation

- The app tries to read public profile HTML and generate a concise intro with Groq.
- If profile content is blocked/sparse, it falls back to roster metadata.

### Boardroom flow (actual runtime behavior)

- `start` runs: ML analyst node -> VC node -> pause before partner node.
- `resume` runs: partner node -> graph end.
- Status is:
  - `paused` when interruption is active.
  - `done` when graph reaches `END`.
- In practice, one start + one resume completes a thread.

### Partner disagreement/departure mechanic

- Partner responses are scanned for disagreement signals.
- Three consecutive disagreement cycles trigger partner departure.
- Departure removes synergy benefit from budget/burn/revenue and logs a penalty message.

### Retrieval-augmented partner context

- Startup advice retrieval from local playbook snippets in ChromaDB.
- Celebrity background retrieval from a Wikipedia-ingested ChromaDB collection.
- Selected celebrity name is passed from UI -> API -> graph state so partner advice can use matching context.

## Requirements

- Python 3.10+ recommended
- `GROQ_API_KEY` in `.env`

You can use any active Python environment (not necessarily `.venv`).

## Installation

Use interpreter-bound pip to avoid Windows launcher issues:

```bash
python -m pip install -r requirements.txt
```

## Environment setup

Copy [.env.example](.env.example) to `.env` and set at least:

```env
GROQ_API_KEY=your_real_groq_api_key_here
```

## Run

Start backend from project root:

```bash
python -m uvicorn src.api.main:app --reload --host 127.0.0.1 --port 8000
```

Open UI:

- `http://127.0.0.1:8000/ui/index.html`

If port 8000 is occupied, use `--port 8001` and open `/ui/index.html` on that port.

## How to play

1. Select founder, country, sector, and both partner types.
2. Click Generate Setup.
3. Click Run Market Physics to get success probability + runway.
4. Enter pitch and click Start Board Meeting.
5. Read VC feedback, enter counter-argument, click Submit Counter-Argument.
6. Review final partner response and outcome for that thread.

## API endpoints

- `GET /` health + UI route
- `GET /api/setup/countries`
- `GET /api/setup/classmates`
- `GET /api/setup/classmate-intro?name=...`
- `GET /api/setup/partners`
- `GET /api/setup/celebrity-partners`
- `GET /api/setup/professor-partners`
- `POST /api/setup/founder`
- `POST /api/predict`
- `POST /api/boardroom_turn` (`action` = `start` or `resume`)

## Key files

- [frontend/web/index.html](frontend/web/index.html)
- [frontend/web/app.js](frontend/web/app.js)
- [frontend/web/styles.css](frontend/web/styles.css)
- [src/api/main.py](src/api/main.py)
- [src/agents/graph.py](src/agents/graph.py)
- [src/agents/tools.py](src/agents/tools.py)
- [src/data/founder_roster.py](src/data/founder_roster.py)
- [src/data/vector_db.py](src/data/vector_db.py)
- [src/ml/predictor.py](src/ml/predictor.py)
- [src/ml/startup_model_workbench.ipynb](src/ml/startup_model_workbench.ipynb)
- [.env.example](.env.example)

## Data and storage

- `data/classmates.csv`
- `data/startup_funding_and_outcome.csv`
- `cost_of_living.csv`
- `data/Classmates Linkedin/` PDFs (when present)
- `data/ESADE Faculty/` PDFs (when present)
- `src/data/chroma_db/` persisted vector collections

## Notes

- The LLM and intro generation flows require a valid `GROQ_API_KEY`.
- If the trained ML file is missing, predictor falls back to a baseline estimate.
- On Windows, prefer `python -m pip ...` over `pip ...` if you hit `failed to create process`.

