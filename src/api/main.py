from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from langchain_core.messages import HumanMessage, SystemMessage
from dotenv import load_dotenv
from langchain_groq import ChatGroq
from src.ml.predictor import MarketPredictor
from src.agents.graph import boardroom_graph
from src.data.cost_of_living_data import get_country_list, get_country_profile
from src.data.founder_roster import (
    get_classmates,
    get_partner_options,
    get_classmate_by_name,
    get_partner_by_name,
    parse_classmate_years_experience,
    parse_classmate_sector_tags,
)
from html import unescape
from html.parser import HTMLParser
from typing import Any, Dict, Optional
from functools import lru_cache
from pathlib import Path
from urllib.request import Request, urlopen
from urllib.error import HTTPError, URLError
import os
import re

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

@app.get("/")
def read_root():
    return {
        "status": "online",
        "message": "The Boardroom Sim FastAPI backend is running.",
        "ui": "/ui/index.html",
    }

class BoardroomRequest(BaseModel):
    thread_id: str
    budget: float
    burn_rate: float
    revenue: float
    founder_experience: int
    sector: str
    pitch: str
    action: str = "start"  # "start" or "resume"


class FounderSetupRequest(BaseModel):
    classmate_name: str
    profile_text: Optional[str] = None
    founder_background: Optional[str] = None
    cofounder_background: Optional[str] = None
    country: Optional[str] = None
    preferred_sector: Optional[str] = None
    partner_name: Optional[str] = None


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
    }
    for sector, words in mapping.items():
        if any(word in text for word in words):
            return sector.upper() if sector == "ai" else sector.title()

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
        "sign in",
        "sign up",
        "join linkedin",
        "log in",
        "login",
        "security verification",
        "captcha",
        "we are no longer providing this service",
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
        return {
            "status": status,
            "final_url": final_url,
            "title": "",
            "description": "",
            "text": "",
        }

    parser = _PageTextParser()
    parser.feed(raw_html)

    title = _clean_text(" ".join(parser.title_parts))
    description = _clean_text(parser.description)
    text = _truncate_text(" ".join(parser.text_parts))

    return {
        "status": status,
        "final_url": final_url,
        "title": title,
        "description": description,
        "text": text,
    }


def _get_profile_llm() -> ChatGroq:
    api_key = os.getenv("GROQ_API_KEY", "").strip()
    if not api_key:
        raise RuntimeError("GROQ_API_KEY is not set. Add it to your .env or environment variables.")
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
        f"Founder name: {name}\n"
        f"LinkedIn URL: {classmate.get('linkedin_url', '')}\n"
        f"Final URL: {final_url}\n"
        f"HTTP status: {page_status}\n"
        f"Roster metadata: {'; '.join(roster_bits) if roster_bits else 'none'}\n"
        f"Page title: {page_title or 'none'}\n"
        f"Page description: {page_description or 'none'}\n"
        f"Page text: {page_text or 'none'}\n"
    )

    llm = _get_profile_llm()
    response = llm.invoke([
        SystemMessage(content=prompt),
        HumanMessage(content=user_message),
    ])

    content = _clean_text(getattr(response, "content", ""))
    return content or _build_roster_intro(classmate)


def _seed_startup_physics(exp_years: int, cost_index: float, partner_name: Optional[str] = None) -> Dict[str, Any]:
    cost_multiplier = max(0.7, min(1.6, cost_index / 65.0))
    partner = get_partner_by_name(partner_name or "") or {}
    budget_boost = float(partner.get("budget_multiplier", 1.0))
    burn_boost = float(partner.get("burn_multiplier", 1.0))

    budget = int((280000 + exp_years * 14000) * (1 + (cost_multiplier - 1) * 0.2) * budget_boost)
    burn_rate = int((32000 * cost_multiplier + exp_years * 1300) * burn_boost)
    revenue = int(max(5000, burn_rate * 0.22 + exp_years * 900))

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


@app.get("/api/setup/countries")
def list_countries():
    return {"countries": get_country_list()}


@app.get("/api/setup/classmates")
def list_classmates():
    return {"classmates": get_classmates()}


@app.get("/api/setup/classmate-intro")
def classmate_intro(name: str):
    classmate = get_classmate_by_name(name)
    if not classmate:
        return {
            "name": name,
            "linkedin_url": "",
            "intro": "Select a founder to see a short intro based on their public profile.",
            "source": "missing",
        }

    linkedin_url = classmate.get("linkedin_url", "")
    page_snapshot = _fetch_html_page(linkedin_url) if linkedin_url else {}
    page_text = " ".join(
        [
            _clean_text(page_snapshot.get("title", "")),
            _clean_text(page_snapshot.get("description", "")),
            _clean_text(page_snapshot.get("text", "")),
        ]
    )

    if not page_snapshot or _looks_like_blocked_page(page_text) or len(page_text) < 120:
        intro = _build_roster_intro(classmate)
        source = "roster fallback"
    else:
        try:
            intro = _build_llm_intro(classmate, page_snapshot)
            source = "LLM profile summary"
        except Exception:
            intro = _build_roster_intro(classmate)
            source = "roster fallback"

    return {
        "name": classmate["name"],
        "linkedin_url": linkedin_url,
        "intro": intro,
        "source": source,
    }


@app.get("/api/setup/partners")
def list_partners():
    return {"partners": get_partner_options()}


@app.post("/api/setup/founder")
def setup_founder(req: FounderSetupRequest):
    classmate = get_classmate_by_name(req.classmate_name) or {
        "name": req.classmate_name,
        "linkedin_url": "",
        "notes": "",
        "country": "",
        "years_experience": "",
        "background": "",
        "sector_tags": "",
    }

    requested_country = (req.country or "").strip()
    classmate_country = (classmate.get("country") or "").strip()
    selected_country = classmate_country or requested_country

    country = get_country_profile(selected_country) or {
        "country": selected_country or "Unknown",
        "year": 0,
        "continent": "",
        "cost_of_living_index": 60.0,
        "rent_index": 50.0,
        "local_purchasing_power_index": 100.0,
    }

    profile_text = req.profile_text or ""
    
    # Use split background fields if provided, otherwise fall back to combined profile_text
    founder_bg = (req.founder_background or "").strip()
    cofounder_bg = (req.cofounder_background or "").strip()
    combined_background = f"{founder_bg} {cofounder_bg}".strip() if (founder_bg or cofounder_bg) else profile_text

    classmate_years = parse_classmate_years_experience(classmate)
    exp_years = classmate_years if classmate_years is not None else _extract_experience_years(combined_background or profile_text)

    classmate_sectors = parse_classmate_sector_tags(classmate)
    sector = classmate_sectors[0] if classmate_sectors else _infer_sector(combined_background or profile_text, req.preferred_sector)

    classmate_background = _background_to_code(classmate.get("background", ""))
    founder_background = classmate_background if classmate_background is not None else _infer_founder_background(combined_background or profile_text)

    seeded = _seed_startup_physics(exp_years, country["cost_of_living_index"], req.partner_name)
    partner = get_partner_by_name(req.partner_name or "") or None

    synergy_bonus = float(partner.get("synergy_bonus", 0.0)) if partner else 0.0
    budget = int(seeded["budget"] * (1 + synergy_bonus * 0.25))
    burn_rate = int(seeded["burn_rate"] * (1 + synergy_bonus * 0.10))
    revenue = int(seeded["revenue"] * (1 + synergy_bonus * 0.08))

    return {
        "classmate": classmate,
        "partner": partner,
        "country": country,
        "founder_experience": exp_years,
        "founder_background": founder_background,
        "sector": sector,
        "budget": budget,
        "burn_rate": burn_rate,
        "revenue": revenue,
        "generated_model_features": {
            "team_size": seeded["team_size"],
            "funding_rounds": seeded["funding_rounds"],
            "market_size_billion": seeded["market_size_billion"],
            "product_traction_users": seeded["product_traction_users"],
            "investor_type": seeded["investor_type"],
        },
    }

@app.post("/api/predict")
def predict_success(req: BoardroomRequest):
    prob = predictor.predict_success_probability(req.burn_rate, req.revenue, req.founder_experience, req.sector)
    runway = predictor.calculate_runway(req.budget, req.burn_rate, req.revenue)
    return {"success_probability": prob, "runway_months": runway}

@app.post("/api/boardroom_turn")
def run_boardroom(req: BoardroomRequest):
    config = {"configurable": {"thread_id": req.thread_id}}
    
    if req.action == "start":
        initial_state = {
            "messages": [HumanMessage(content=f"[Founder Pitch]: {req.pitch}")],
            "budget": req.budget,
            "burn_rate": req.burn_rate,
            "revenue": req.revenue,
            "founder_experience": req.founder_experience,
            "sector": req.sector,
            "pitch": req.pitch
        }
        # Runs until the breakpoint (before mentor)
        boardroom_graph.invoke(initial_state, config)
        
    elif req.action == "resume":
        # Provide the player's counter-argument and resume graph!
        # First update the state with the human's new message
        boardroom_graph.update_state(config, {"messages": [HumanMessage(content=f"[Founder Counter-Argument]: {req.pitch}")]})
        # Then continue invocation
        boardroom_graph.invoke(None, config)
        
    # Return everything in memory
    current_state = boardroom_graph.get_state(config)
    messages_out = []
    for msg in current_state.values.get("messages", []):
        content = msg.content if hasattr(msg, "content") else str(msg)
        messages_out.append(content)
    
    next_nodes = current_state.next
    status = "paused" if len(next_nodes) > 0 else "done"
    
    return {
        "status": status,
        "messages": messages_out
    }
