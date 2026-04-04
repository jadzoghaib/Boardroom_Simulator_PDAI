"""
Boardroom Sim API — 8-Quarter Startup Simulation

Endpoints:
  Setup:  GET /api/setup/countries, classmates, classmate-intro, celebrity-partners, professor-partners
          POST /api/setup/founder  → creates a new game session

  Game:   GET  /api/game/{id}/state
          POST /api/game/{id}/choose_event
          POST /api/game/{id}/skip_events
          POST /api/game/{id}/chat
          POST /api/game/{id}/end_quarter
          POST /api/game/{id}/hire
          POST /api/game/{id}/fire
          GET  /api/game/{id}/candidates
          POST /api/game/{id}/raise_funding
          POST /api/game/{id}/board_review
          GET  /api/game/{id}/quarter_summary
"""

from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from langchain_core.messages import HumanMessage, SystemMessage
from dotenv import load_dotenv
from langchain_groq import ChatGroq
from src.ml.predictor import MarketPredictor
from src.data.cost_of_living_data import get_country_list, get_country_profile
from src.data.founder_roster import (
    get_classmates,
    get_partner_options,
    get_celebrity_partners,
    get_professor_partners,
    get_classmate_by_name,
    evaluate_partner_team,
    parse_classmate_years_experience,
    parse_classmate_sector_tags,
)
from src.game.state import GameState
from src.game.engine import (
    create_initial_state,
    apply_choice,
    skip_remaining_events,
    end_quarter,
    hire_staff,
    fire_staff,
    get_funding_offer,
    accept_funding,
    get_quarter_summary,
    draw_quarter_events,
)
from src.data.hiring import get_all_candidates, get_candidate_by_id, get_candidates_by_role
from html import unescape
from html.parser import HTMLParser
from typing import Any, Dict, List, Optional
from functools import lru_cache
from pathlib import Path
from urllib.request import Request, urlopen
from urllib.error import HTTPError, URLError
import os
import re
import asyncio

load_dotenv()

app = FastAPI(title="Boardroom Sim API")
predictor = MarketPredictor()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

WEB_DIR = Path(__file__).resolve().parents[2] / "frontend" / "web"
if WEB_DIR.exists():
    app.mount("/ui", StaticFiles(directory=str(WEB_DIR), html=True), name="ui")


# ═══════════════════════════════════════════════════════════════════
# IN-MEMORY GAME SESSION STORE
# ═══════════════════════════════════════════════════════════════════

game_sessions: Dict[str, GameState] = {}


def _get_game(game_id: str) -> GameState:
    if game_id not in game_sessions:
        raise HTTPException(status_code=404, detail=f"Game {game_id} not found")
    return game_sessions[game_id]


# ═══════════════════════════════════════════════════════════════════
# ROOT
# ═══════════════════════════════════════════════════════════════════

@app.get("/")
def read_root():
    return {
        "status": "online",
        "message": "The Boardroom Sim FastAPI backend is running.",
        "ui": "/ui/index.html",
        "active_games": len(game_sessions),
    }


# ═══════════════════════════════════════════════════════════════════
# REQUEST MODELS
# ═══════════════════════════════════════════════════════════════════

class FounderSetupRequest(BaseModel):
    classmate_name: str
    profile_text: Optional[str] = None
    founder_background: Optional[str] = None
    cofounder_background: Optional[str] = None
    country: Optional[str] = None
    preferred_sector: Optional[str] = None
    celebrity_partner_name: Optional[str] = None
    professor_partner_name: Optional[str] = None


class ChooseEventRequest(BaseModel):
    event_id: str
    choice_index: int


class ChatRequest(BaseModel):
    message: str


class HireRequest(BaseModel):
    candidate_id: str


class FireRequest(BaseModel):
    staff_id: str


# ═══════════════════════════════════════════════════════════════════
# SETUP UTILITIES (kept from original)
# ═══════════════════════════════════════════════════════════════════

def _extract_experience_years(profile_text: str) -> int:
    match = re.search(r"(\d{1,2})\+?\s+years?", profile_text.lower())
    if match:
        return max(0, min(20, int(match.group(1))))
    signal_words = ["intern", "junior", "lead", "manager", "director", "founder"]
    score = sum(1 for word in signal_words if word in profile_text.lower())
    return max(1, min(15, score + 2))


def _infer_sector(profile_text: str, preferred_sector: Optional[str]) -> str:
    if preferred_sector:
        return preferred_sector
    text = profile_text.lower()
    mapping = {
        "fintech": ["bank", "finance", "payments", "fintech"],
        "healthtech": ["health", "hospital", "medical", "bio"],
        "saas": ["b2b", "software", "saas", "enterprise"],
        "ai": ["ai", "machine learning", "llm", "data science"],
        "e-commerce": ["ecommerce", "e-commerce", "shop", "retail", "marketplace"],
    }
    for sector, words in mapping.items():
        if any(word in text for word in words):
            if sector == "ai":
                return "AI"
            if sector == "e-commerce":
                return "E-commerce"
            return sector.title()
    return "AI"


def _infer_founder_background(profile_text: str) -> int:
    text = profile_text.lower()
    if any(word in text for word in ["engineer", "developer", "software", "data"]):
        return 2
    if any(word in text for word in ["mba", "finance", "consulting", "investment"]):
        return 1
    return 0


def _background_to_code(background: str) -> Optional[int]:
    value = (background or "").strip().lower()
    if not value:
        return None
    if value in {"technical", "tech", "engineering", "engineer", "developer", "data"}:
        return 2
    if value in {"business", "commercial", "mba", "finance", "consulting"}:
        return 1
    if value in {"other", "general"}:
        return 0
    return None


class _PageTextParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.title_parts: list[str] = []
        self.description = ""
        self.text_parts: list[str] = []
        self._in_title = False
        self._skip_depth = 0

    def handle_starttag(self, tag: str, attrs):
        attr_map = {key.lower(): (value or "") for key, value in attrs}
        if tag == "title":
            self._in_title = True
        elif tag in {"script", "style", "noscript"}:
            self._skip_depth += 1
        elif tag == "meta":
            meta_key = (attr_map.get("property") or attr_map.get("name") or "").strip().lower()
            content = (attr_map.get("content") or "").strip()
            if content and not self.description and meta_key in {"description", "og:description", "twitter:description"}:
                self.description = content
            if content and not self.title_parts and meta_key in {"og:title", "twitter:title"}:
                self.title_parts.append(content)

    def handle_endtag(self, tag: str):
        if tag == "title":
            self._in_title = False
        elif tag in {"script", "style", "noscript"} and self._skip_depth > 0:
            self._skip_depth -= 1

    def handle_data(self, data: str):
        text = data.strip()
        if not text:
            return
        if self._in_title:
            self.title_parts.append(text)
        elif self._skip_depth == 0:
            self.text_parts.append(text)


def _clean_text(text: str) -> str:
    return re.sub(r"\s+", " ", unescape(text or "")).strip()


def _truncate_text(text: str, max_chars: int = 2500) -> str:
    cleaned = _clean_text(text)
    if len(cleaned) <= max_chars:
        return cleaned
    return cleaned[:max_chars].rsplit(" ", 1)[0].strip() + "..."


def _looks_like_blocked_page(text: str) -> bool:
    lowered = (text or "").lower()
    blocked_signals = [
        "sign in", "sign up", "join linkedin", "log in", "login",
        "security verification", "captcha", "we are no longer providing this service",
    ]
    return any(signal in lowered for signal in blocked_signals)


@lru_cache(maxsize=64)
def _fetch_html_page(url: str, timeout: int = 12) -> Dict[str, Any]:
    if not url:
        return {}
    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
            "(KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36"
        ),
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.9",
    }
    request = Request(url, headers=headers)
    status = None
    final_url = url
    raw_html = ""
    try:
        with urlopen(request, timeout=timeout) as response:
            status = getattr(response, "status", response.getcode())
            final_url = response.geturl() or url
            raw_html = response.read().decode("utf-8", errors="replace")
    except HTTPError as error:
        status = error.code
        try:
            final_url = error.geturl() or url
        except Exception:
            final_url = url
        try:
            raw_html = error.read().decode("utf-8", errors="replace")
        except Exception:
            raw_html = ""
    except (URLError, TimeoutError, ValueError):
        return {}

    if not raw_html:
        return {"status": status, "final_url": final_url, "title": "", "description": "", "text": ""}

    parser = _PageTextParser()
    parser.feed(raw_html)
    title = _clean_text(" ".join(parser.title_parts))
    description = _clean_text(parser.description)
    text = _truncate_text(" ".join(parser.text_parts))
    return {"status": status, "final_url": final_url, "title": title, "description": description, "text": text}


def _get_profile_llm() -> ChatGroq:
    api_key = os.getenv("GROQ_API_KEY", "").strip()
    if not api_key:
        raise RuntimeError("GROQ_API_KEY is not set.")
    return ChatGroq(model="llama-3.3-70b-versatile", temperature=0.2, api_key=api_key)


def _build_roster_intro(classmate: Dict[str, str]) -> str:
    name = classmate.get("name", "This founder") or "This founder"
    parts = [f"{name} is listed in the founder roster."]
    years = parse_classmate_years_experience(classmate)
    if years is not None:
        parts.append(f"They appear to have about {years} years of experience.")
    background = classmate.get("background", "").strip()
    if background:
        parts.append(f"Roster background: {background}.")
    sector_tags = parse_classmate_sector_tags(classmate)
    if sector_tags:
        parts.append(f"Relevant sectors: {', '.join(sector_tags)}.")
    notes = classmate.get("notes", "").strip()
    if notes:
        parts.append(notes)
    return " ".join(part.strip() for part in parts if part.strip())


def _build_llm_intro(classmate: Dict[str, str], page_snapshot: Dict[str, Any]) -> str:
    name = classmate.get("name", "This founder") or "This founder"
    roster_bits = []
    years = parse_classmate_years_experience(classmate)
    if years is not None:
        roster_bits.append(f"years_experience={years}")
    background = classmate.get("background", "").strip()
    if background:
        roster_bits.append(f"background={background}")
    sector_tags = parse_classmate_sector_tags(classmate)
    if sector_tags:
        roster_bits.append(f"sector_tags={', '.join(sector_tags)}")
    notes = classmate.get("notes", "").strip()
    if notes:
        roster_bits.append(f"notes={notes}")

    page_title = _clean_text(page_snapshot.get("title", ""))
    page_description = _clean_text(page_snapshot.get("description", ""))
    page_text = _clean_text(page_snapshot.get("text", ""))
    page_status = page_snapshot.get("status", "")
    final_url = _clean_text(page_snapshot.get("final_url", ""))

    prompt = (
        "Write a concise founder intro in 2 sentences max. "
        "Use only the facts provided below. "
        "If the page text looks like a login wall or is too thin to be useful, say that briefly and lean on the roster metadata instead. "
        "Do not mention that you are an AI. Do not invent details."
    )
    user_message = (
        f"Founder name: {name}\nLinkedIn URL: {classmate.get('linkedin_url', '')}\n"
        f"Final URL: {final_url}\nHTTP status: {page_status}\n"
        f"Roster metadata: {'; '.join(roster_bits) if roster_bits else 'none'}\n"
        f"Page title: {page_title or 'none'}\nPage description: {page_description or 'none'}\n"
        f"Page text: {page_text or 'none'}\n"
    )
    llm = _get_profile_llm()
    response = llm.invoke([SystemMessage(content=prompt), HumanMessage(content=user_message)])
    content = _clean_text(getattr(response, "content", ""))
    return content or _build_roster_intro(classmate)


def _seed_startup_physics(
    exp_years: int,
    cost_index: float,
    budget_multiplier: float = 1.0,
    burn_multiplier: float = 1.0,
    revenue_multiplier: float = 1.0,
) -> Dict[str, Any]:
    cost_multiplier = max(0.7, min(1.6, cost_index / 65.0))
    budget = int((280000 + exp_years * 14000) * (1 + (cost_multiplier - 1) * 0.2) * budget_multiplier)
    burn_rate = int((32000 * cost_multiplier + exp_years * 1300) * burn_multiplier)
    revenue = int(max(5000, burn_rate * 0.22 + exp_years * 900) * revenue_multiplier)
    return {
        "budget": budget,
        "burn_rate": burn_rate,
        "revenue": revenue,
        "team_size": max(3, min(14, int(4 + exp_years / 2 - (cost_multiplier - 1) * 2))),
        "funding_rounds": 1 if exp_years < 7 else 2,
        "market_size_billion": round(8 + exp_years * 0.7, 1),
        "product_traction_users": int(700 + exp_years * 180),
        "investor_type": 1 if exp_years >= 8 else 0,
    }


# ═══════════════════════════════════════════════════════════════════
# SETUP ENDPOINTS
# ═══════════════════════════════════════════════════════════════════

@app.get("/api/setup/countries")
def list_countries():
    return {"countries": get_country_list()}


@app.get("/api/setup/classmates")
def list_classmates():
    return {"classmates": get_classmates()}


@app.get("/api/setup/classmate-intro")
async def classmate_intro(name: str):
    classmate = get_classmate_by_name(name)
    if not classmate:
        return {
            "name": name, "linkedin_url": "",
            "intro": "Select a founder to see a short intro based on their public profile.",
            "source": "missing",
        }
    linkedin_url = classmate.get("linkedin_url", "")
    # LinkedIn always blocks automated requests, so skip the network fetch
    # and use roster metadata directly. This avoids blocking the thread pool
    # with a 12-second timeout that always ends in a login-wall redirect.
    intro = _build_roster_intro(classmate)
    source = "roster"
    return {"name": classmate["name"], "linkedin_url": linkedin_url, "intro": intro, "source": source}


@app.get("/api/setup/partners")
def list_partners():
    return {"partners": get_partner_options()}


@app.get("/api/setup/celebrity-partners")
def list_celebrity_partners():
    return {"celebrity_partners": get_celebrity_partners()}


@app.get("/api/setup/professor-partners")
def list_professor_partners():
    return {"professor_partners": get_professor_partners()}


# ═══════════════════════════════════════════════════════════════════
# FOUNDER SETUP → CREATES GAME SESSION
# ═══════════════════════════════════════════════════════════════════

@app.post("/api/setup/founder")
async def setup_founder(req: FounderSetupRequest):
    classmate = get_classmate_by_name(req.classmate_name) or {
        "name": req.classmate_name, "linkedin_url": "", "notes": "",
        "country": "", "years_experience": "", "background": "", "sector_tags": "",
    }

    requested_country = (req.country or "").strip()
    classmate_country = (classmate.get("country") or "").strip()
    selected_country = classmate_country or requested_country

    country = get_country_profile(selected_country) or {
        "country": selected_country or "Unknown", "year": 0, "continent": "",
        "cost_of_living_index": 60.0, "rent_index": 50.0, "local_purchasing_power_index": 100.0,
    }

    profile_text = req.profile_text or ""
    founder_bg = (req.founder_background or "").strip()
    cofounder_bg = (req.cofounder_background or "").strip()
    combined_background = f"{founder_bg} {cofounder_bg}".strip() if (founder_bg or cofounder_bg) else profile_text

    classmate_years = parse_classmate_years_experience(classmate)
    exp_years = classmate_years if classmate_years is not None else _extract_experience_years(combined_background or profile_text)

    classmate_sectors = parse_classmate_sector_tags(classmate)
    sector = classmate_sectors[0] if classmate_sectors else _infer_sector(combined_background or profile_text, req.preferred_sector)

    classmate_background = _background_to_code(classmate.get("background", ""))
    founder_background = classmate_background if classmate_background is not None else _infer_founder_background(combined_background or profile_text)

    partner_team = evaluate_partner_team(
        req.celebrity_partner_name or "",
        req.professor_partner_name or "",
    )

    seeded = _seed_startup_physics(
        exp_years,
        country["cost_of_living_index"],
        budget_multiplier=float(partner_team.get("budget_multiplier", 1.0)),
        burn_multiplier=float(partner_team.get("burn_multiplier", 1.0)),
        revenue_multiplier=float(partner_team.get("revenue_multiplier", 1.0)),
    )

    synergy_bonus = float(partner_team.get("synergy_bonus", 0.0))
    seeded["budget"] = int(seeded["budget"] * (1 + synergy_bonus * 0.25))
    seeded["burn_rate"] = int(seeded["burn_rate"] * (1 + synergy_bonus * 0.10))
    seeded["revenue"] = int(seeded["revenue"] * (1 + synergy_bonus * 0.08))

    # Create game state
    state = create_initial_state(
        classmate=classmate,
        celebrity=partner_team.get("celebrity", {}),
        professor=partner_team.get("professor", {}),
        country=country,
        sector=sector,
        founder_experience=exp_years,
        founder_background=founder_background,
        synergy_data=partner_team,
        seeded_physics=seeded,
    )

    # Run ML predictor for initial probability
    try:
        ml_feats = state.to_ml_features()
        prob = predictor.predict_success_probability(
            state.burn_rate, state.revenue, state.founder_experience, state.sector
        )
        state.success_probability = prob
    except Exception:
        state.success_probability = 0.5

    # Store session
    game_sessions[state.game_id] = state

    return {
        "game_id": state.game_id,
        "state": state.summary_dict(),
        # Legacy fields for backward compat
        "classmate": classmate,
        "partner_team": partner_team,
        "country": country,
        "founder_experience": exp_years,
        "founder_background": founder_background,
        "sector": sector,
    }


# ═══════════════════════════════════════════════════════════════════
# GAME STATE ENDPOINT
# ═══════════════════════════════════════════════════════════════════

@app.get("/api/game/{game_id}/state")
def get_game_state(game_id: str):
    state = _get_game(game_id)
    return {"game_id": game_id, "state": state.summary_dict()}


# ═══════════════════════════════════════════════════════════════════
# EVENT ENDPOINTS
# ═══════════════════════════════════════════════════════════════════

@app.post("/api/game/{game_id}/choose_event")
def choose_event(game_id: str, req: ChooseEventRequest):
    state = _get_game(game_id)

    if state.game_over:
        raise HTTPException(400, "Game is over")
    if state.phase not in ("events", "advise"):
        raise HTTPException(400, f"Cannot choose events in phase '{state.phase}'")

    old_stats = dict(state.stats)
    state = apply_choice(state, req.event_id, req.choice_index)
    game_sessions[game_id] = state

    # Find the reaction text
    event_data = None
    from src.data.events import get_event_by_id
    raw = get_event_by_id(req.event_id)
    reaction = ""
    if raw and 0 <= req.choice_index < len(raw.get("choices", [])):
        reaction = raw["choices"][req.choice_index].get("reaction", "")

    return {
        "game_id": game_id,
        "reaction": reaction,
        "ap_remaining": state.ap_available,
        "stats": state.stats,
        "stat_changes": {k: state.stats[k] - old_stats.get(k, 0) for k in state.stats if state.stats[k] != old_stats.get(k, 0)},
        "cash": state.cash,
        "burn_rate": state.burn_rate,
        "revenue": state.revenue,
        "phase": state.phase,
        "pending_event": state.pending_event.model_dump() if state.pending_event else None,
        "events_remaining": len(state.current_events),
    }


@app.post("/api/game/{game_id}/skip_events")
def skip_events(game_id: str):
    state = _get_game(game_id)
    if state.game_over:
        raise HTTPException(400, "Game is over")
    state = skip_remaining_events(state)
    game_sessions[game_id] = state
    return {"game_id": game_id, "phase": state.phase}


# ═══════════════════════════════════════════════════════════════════
# QUARTER END
# ═══════════════════════════════════════════════════════════════════

@app.post("/api/game/{game_id}/end_quarter")
def end_quarter_endpoint(game_id: str):
    state = _get_game(game_id)

    if state.game_over:
        raise HTTPException(400, "Game is over")
    if state.phase != "quarter_end":
        raise HTTPException(400, f"Cannot end quarter in phase '{state.phase}'. Finish events first.")

    state = end_quarter(state)

    # Update ML prediction
    try:
        prob = predictor.predict_success_probability(
            state.burn_rate, state.revenue, state.founder_experience, state.sector
        )
        state.success_probability = prob
    except Exception:
        pass

    game_sessions[game_id] = state

    summary = get_quarter_summary(state)
    return {"game_id": game_id, "summary": summary, "state": state.summary_dict()}


# ═══════════════════════════════════════════════════════════════════
# ADVISORY CHAT — async endpoints (one per advisor)
# ═══════════════════════════════════════════════════════════════════

@app.post("/api/game/{game_id}/chat/celebrity")
async def game_chat_celebrity(game_id: str, req: ChatRequest):
    """Chat with the celebrity advisor only. Non-blocking."""
    state = _get_game(game_id)
    if state.game_over:
        raise HTTPException(400, "Game is over")

    from src.game.state import ChatMessage
    from src.game.advisor import get_celebrity_response

    celebrity_name = state.celebrity.get("name", "Celebrity Advisor")

    # Store user message
    state.chat_messages.append(ChatMessage(
        role="user", speaker="You", content=req.message, quarter=state.current_quarter
    ))

    # Run blocking LLM call in thread pool so FastAPI stays responsive
    try:
        celeb_response = await asyncio.to_thread(get_celebrity_response, state, req.message)
    except Exception:
        celeb_response = "Bold move always pays off — trust your instincts, but watch the cash runway."

    state.chat_messages.append(ChatMessage(
        role="celebrity", speaker=celebrity_name, content=celeb_response, quarter=state.current_quarter
    ))
    game_sessions[game_id] = state

    return {
        "game_id": game_id,
        "role": "celebrity",
        "speaker": celebrity_name,
        "content": celeb_response,
    }


@app.post("/api/game/{game_id}/chat/professor")
async def game_chat_professor(game_id: str, req: ChatRequest):
    """Chat with the professor advisor only. Non-blocking."""
    state = _get_game(game_id)
    if state.game_over:
        raise HTTPException(400, "Game is over")

    from src.game.state import ChatMessage
    from src.game.advisor import get_professor_response

    professor_name = state.professor.get("name", "Professor Advisor")

    # Store user message
    state.chat_messages.append(ChatMessage(
        role="user", speaker="You", content=req.message, quarter=state.current_quarter
    ))

    # Run blocking LLM call in thread pool so FastAPI stays responsive
    try:
        prof_response = await asyncio.to_thread(get_professor_response, state, req.message)
    except Exception:
        prof_response = "The data suggests a measured approach. Consider risk-adjusted returns before committing resources."

    state.chat_messages.append(ChatMessage(
        role="professor", speaker=professor_name, content=prof_response, quarter=state.current_quarter
    ))
    game_sessions[game_id] = state

    return {
        "game_id": game_id,
        "role": "professor",
        "speaker": professor_name,
        "content": prof_response,
    }


@app.post("/api/game/{game_id}/chat")
async def game_chat(game_id: str, req: ChatRequest):
    """Chat with both advisors simultaneously (kept for backward compat). Non-blocking."""
    state = _get_game(game_id)
    if state.game_over:
        raise HTTPException(400, "Game is over")

    from src.game.state import ChatMessage
    from src.game.advisor import get_advisor_responses

    celebrity_name = state.celebrity.get("name", "Celebrity Advisor")
    professor_name = state.professor.get("name", "Professor Advisor")

    state.chat_messages.append(ChatMessage(
        role="user", speaker="You", content=req.message, quarter=state.current_quarter
    ))

    try:
        celebrity_response, professor_response = await asyncio.to_thread(
            get_advisor_responses, state, req.message
        )
    except Exception:
        celebrity_response = "Bold move always pays off — trust your instincts, but watch the cash runway."
        professor_response = "The data suggests a measured approach. Consider risk-adjusted returns before committing."

    state.chat_messages.append(ChatMessage(
        role="celebrity", speaker=celebrity_name, content=celebrity_response, quarter=state.current_quarter
    ))
    state.chat_messages.append(ChatMessage(
        role="professor", speaker=professor_name, content=professor_response, quarter=state.current_quarter
    ))
    game_sessions[game_id] = state

    return {
        "game_id": game_id,
        "messages": [
            {"role": "celebrity", "speaker": celebrity_name, "content": celebrity_response},
            {"role": "professor", "speaker": professor_name, "content": professor_response},
        ],
    }


# ═══════════════════════════════════════════════════════════════════
# HIRING
# ═══════════════════════════════════════════════════════════════════

@app.get("/api/game/{game_id}/candidates")
def list_candidates(game_id: str, role: Optional[str] = None):
    state = _get_game(game_id)
    filled_roles = {s.role for s in state.staff}

    if role:
        candidates = get_candidates_by_role(role)
    else:
        candidates = get_all_candidates()

    # Mark which roles are already filled
    result = []
    for c in candidates:
        result.append({
            **c,
            "slot_filled": c["role"] in filled_roles,
        })

    return {"game_id": game_id, "candidates": result, "filled_roles": list(filled_roles)}


@app.post("/api/game/{game_id}/hire")
def hire_endpoint(game_id: str, req: HireRequest):
    state = _get_game(game_id)

    if state.game_over:
        raise HTTPException(400, "Game is over")

    candidate = get_candidate_by_id(req.candidate_id)
    if candidate is None:
        raise HTTPException(404, f"Candidate {req.candidate_id} not found")

    # Check slot
    filled_roles = {s.role for s in state.staff}
    if candidate["role"] in filled_roles:
        raise HTTPException(400, f"{candidate['role']} slot already filled. Fire current {candidate['role']} first.")

    state = hire_staff(state, candidate)
    game_sessions[game_id] = state

    return {
        "game_id": game_id,
        "hired": candidate["name"],
        "role": candidate["role"],
        "salary": candidate["salary"],
        "equity_given": candidate["equity_ask"],
        "stats": state.stats,
        "ap_bonus": state.ap_bonus,
        "staff": [s.model_dump() for s in state.staff],
    }


@app.post("/api/game/{game_id}/fire")
def fire_endpoint(game_id: str, req: FireRequest):
    state = _get_game(game_id)

    if state.game_over:
        raise HTTPException(400, "Game is over")

    state = fire_staff(state, req.staff_id)
    game_sessions[game_id] = state

    return {
        "game_id": game_id,
        "fired": req.staff_id,
        "stats": state.stats,
        "ap_bonus": state.ap_bonus,
        "staff": [s.model_dump() for s in state.staff],
    }


# ═══════════════════════════════════════════════════════════════════
# FUNDRAISING
# ═══════════════════════════════════════════════════════════════════

@app.get("/api/game/{game_id}/funding")
def get_funding(game_id: str):
    state = _get_game(game_id)
    offer = get_funding_offer(state)
    return {"game_id": game_id, "current_stage": state.funding_stage, "equity_given": state.equity_given, "offer": offer}


@app.post("/api/game/{game_id}/raise_funding")
def raise_funding(game_id: str):
    state = _get_game(game_id)

    if state.game_over:
        raise HTTPException(400, "Game is over")

    offer = get_funding_offer(state)
    if offer is None or not offer.get("available"):
        raise HTTPException(400, offer.get("reason", "Not eligible for funding") if offer else "Already at max stage")

    state = accept_funding(state)
    game_sessions[game_id] = state

    return {
        "game_id": game_id,
        "new_stage": state.funding_stage,
        "cash": state.cash,
        "equity_given": state.equity_given,
        "valuation": state.valuation,
    }


# ═══════════════════════════════════════════════════════════════════
# BOARD REVIEW — live VC chat (Feature 3)
# ═══════════════════════════════════════════════════════════════════

@app.post("/api/game/{game_id}/board_review")
async def board_review(game_id: str):
    """Start the board review — generates VC opening statement."""
    state = _get_game(game_id)
    if state.game_over:
        raise HTTPException(400, "Game is over")

    from src.game.advisor import get_vc_opening
    from src.game.state import ChatMessage

    # Clear previous board chat
    state.board_chat_messages = []
    state.board_chat_outcome = None

    vc_name = "Board VC"
    opening = await asyncio.to_thread(get_vc_opening, state)

    state.board_chat_messages.append(ChatMessage(
        role="vc", speaker=vc_name, content=opening, quarter=state.current_quarter
    ))

    game_sessions[game_id] = state

    return {
        "game_id": game_id,
        "vc_message": opening,
        "vc_name": vc_name,
        "partner_name": state.professor.get("name", "Professor"),
        "quarter": state.current_quarter,
        "state": state.summary_dict(),
    }


@app.post("/api/game/{game_id}/board_chat")
async def board_chat(game_id: str, req: ChatRequest):
    """Send a message to the board and get VC + partner response. Verdict may be issued."""
    state = _get_game(game_id)
    if state.game_over:
        raise HTTPException(400, "Game is over")

    from src.game.advisor import get_vc_response
    from src.game.state import ChatMessage

    vc_name = "Board VC"
    partner_name = state.professor.get("name", "Professor")

    # Store founder message
    state.board_chat_messages.append(ChatMessage(
        role="user", speaker="You", content=req.message, quarter=state.current_quarter
    ))

    # Get responses
    vc_resp, partner_resp, verdict = await asyncio.to_thread(get_vc_response, state, req.message)

    state.board_chat_messages.append(ChatMessage(
        role="vc", speaker=vc_name, content=vc_resp, quarter=state.current_quarter
    ))
    state.board_chat_messages.append(ChatMessage(
        role="partner", speaker=partner_name, content=partner_resp, quarter=state.current_quarter
    ))

    # Apply verdict effects
    outcome = None
    if verdict:
        if verdict == "IMPRESSED":
            state.valuation = int(state.valuation * 1.20)
            state.cash = int(state.cash * 1.05)
            outcome = {"verdict": "IMPRESSED", "effect": "Valuation +20%. Board is impressed with your vision."}
        elif verdict == "CONCERNED":
            state.valuation = int(state.valuation * 0.90)
            outcome = {"verdict": "CONCERNED", "effect": "Valuation -10%. Board has concerns about your trajectory."}
        else:
            outcome = {"verdict": "NEUTRAL", "effect": "Board acknowledged your progress. Keep executing."}

        state.board_chat_outcome = outcome
        state.last_board_review_quarter = state.current_quarter
        state.vc_cycle += 1

        # Draw events for next quarter
        state = draw_quarter_events(state)

    game_sessions[game_id] = state

    return {
        "game_id": game_id,
        "vc_response": vc_resp,
        "vc_name": vc_name,
        "partner_response": partner_resp,
        "partner_name": partner_name,
        "verdict": verdict,
        "outcome": outcome,
        "state": state.summary_dict(),
    }


# ═══════════════════════════════════════════════════════════════════
# END-OF-GAME DEBRIEF (Feature 1)
# ═══════════════════════════════════════════════════════════════════

@app.post("/api/game/{game_id}/debrief")
async def game_debrief(game_id: str):
    """Generate a detailed post-game debrief via LLM."""
    state = _get_game(game_id)
    from src.game.advisor import get_game_debrief
    debrief_text = await asyncio.to_thread(get_game_debrief, state)
    return {"game_id": game_id, "debrief": debrief_text}


# ═══════════════════════════════════════════════════════════════════
# QUARTER SUMMARY
# ═══════════════════════════════════════════════════════════════════

@app.get("/api/game/{game_id}/quarter_summary")
def quarter_summary(game_id: str):
    state = _get_game(game_id)
    return {"game_id": game_id, "summary": get_quarter_summary(state)}


# ═══════════════════════════════════════════════════════════════════
# ML PREDICTION (standalone, kept for backward compat)
# ═══════════════════════════════════════════════════════════════════

class PredictRequest(BaseModel):
    burn_rate: float
    revenue: float
    founder_experience: int
    sector: str


@app.post("/api/predict")
def predict_success(req: PredictRequest):
    prob = predictor.predict_success_probability(req.burn_rate, req.revenue, req.founder_experience, req.sector)
    return {"success_probability": prob}
