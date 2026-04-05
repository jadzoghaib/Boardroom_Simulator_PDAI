"""
GameState — Pydantic model for the 8-quarter startup simulation.

Tracks everything: financials, stats, staff, events, market, rivals,
milestones, advisory chat, partner/VC status, and game outcome.
"""

from __future__ import annotations

import uuid
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


# ── Helpers ──────────────────────────────────────────────────────────

STAT_KEYS = ["growth", "brand", "product", "tech", "ops", "finance", "innovation", "execution"]

FUNDING_STAGES = ["bootstrap", "angels", "seed", "series_a", "series_b"]

SECTORS = ["AI", "Fintech", "SaaS", "Healthtech", "E-commerce"]


def _default_stats() -> Dict[str, int]:
    return {k: 0 for k in STAT_KEYS}


def _default_ml_features() -> Dict[str, Any]:
    return {
        "funding_rounds": 1,
        "founder_experience_years": 3,
        "team_size": 4,
        "market_size_billion": 10.0,
        "product_traction_users": 1000,
        "burn_rate_million": 0.035,
        "revenue_million": 0.008,
        "investor_type": 0,
        "sector": "AI",
        "founder_background": 0,
    }


# ── Sub-models ───────────────────────────────────────────────────────

class StaffMember(BaseModel):
    id: str = Field(default_factory=lambda: uuid.uuid4().hex[:8])
    name: str
    role: str  # CTO, CMO, CFO, COO
    salary: int = 0
    equity_ask: float = 0.0
    ap_bonus: int = 0
    stat_bonuses: Dict[str, int] = Field(default_factory=dict)
    hired_quarter: int = 1


class RivalState(BaseModel):
    name: str
    ceo: str
    sector: str
    score: int = 0
    momentum: str = "steady"  # rising, steady, falling
    milestones_hit: int = 0
    description: str = ""


class MilestoneState(BaseModel):
    id: str
    name: str
    description: str
    tier: str  # conservative, balanced, ambitious
    stat_requirements: Dict[str, int] = Field(default_factory=dict)
    financial_requirements: Dict[str, float] = Field(default_factory=dict)
    completed: bool = False
    completed_quarter: Optional[int] = None


class EventChoice(BaseModel):
    text: str
    ap_cost: int = 1
    effects: Dict[str, Any] = Field(default_factory=dict)
    reaction: str = ""


class GameEvent(BaseModel):
    id: str
    title: str
    description: str
    department: str = "general"
    sector: Optional[str] = None
    phase: str = "early"  # early (Q1-4) or late (Q5-8)
    choices: List[EventChoice] = Field(default_factory=list)
    is_shock: bool = False


class MarketShock(BaseModel):
    name: str
    description: str
    effects: Dict[str, float] = Field(default_factory=dict)
    duration_quarters: int = 1
    quarters_remaining: int = 1


class ChatMessage(BaseModel):
    role: str  # user, celebrity, professor, system
    speaker: str = ""
    content: str
    quarter: int = 1


class QuarterLog(BaseModel):
    quarter: int
    events_resolved: List[str] = Field(default_factory=list)
    cash_start: float = 0
    cash_end: float = 0
    revenue: float = 0
    burn_rate: float = 0
    market_condition: str = "stable"
    staff_changes: List[str] = Field(default_factory=list)
    milestones_completed: List[str] = Field(default_factory=list)
    notes: str = ""


# ── Main GameState ───────────────────────────────────────────────────

class GameState(BaseModel):
    # ── Identity (set at setup) ──
    game_id: str = Field(default_factory=lambda: uuid.uuid4().hex[:12])
    classmate: Dict[str, Any] = Field(default_factory=dict)
    celebrity: Dict[str, Any] = Field(default_factory=dict)
    professor: Dict[str, Any] = Field(default_factory=dict)
    country: Dict[str, Any] = Field(default_factory=dict)
    sector: str = "AI"
    founder_experience: int = 3
    founder_background: int = 0  # 0=other, 1=business, 2=technical
    synergy_data: Dict[str, Any] = Field(default_factory=dict)

    # ── Quarter tracking ──
    current_quarter: int = 1  # 1-8
    phase: str = "events"
    # phases: "events" | "advise" | "resolve" | "board_review" | "quarter_end" | "game_over"

    # ── Financials ──
    cash: float = 300000.0
    burn_rate: float = 35000.0
    revenue: float = 8000.0
    valuation: float = 1000000.0
    funding_stage: str = "bootstrap"
    equity_given: float = 0.0

    # ── 8-dimensional stats ──
    stats: Dict[str, int] = Field(default_factory=_default_stats)

    # ── AP system ──
    ap_base: int = 5
    ap_bonus: int = 0
    ap_spent: int = 0

    # ── Staff (4 exec slots: CTO, CMO, CFO, COO) ──
    staff: List[StaffMember] = Field(default_factory=list)

    # ── ML features (aligned with predictor) ──
    ml_features: Dict[str, Any] = Field(default_factory=_default_ml_features)

    # ── Market dynamics ──
    market_condition: str = "stable"
    market_history: List[str] = Field(default_factory=list)
    active_shock: Optional[MarketShock] = None

    # ── Rivals (3 per sector) ──
    rivals: List[RivalState] = Field(default_factory=list)

    # ── Milestones (3 per game) ──
    milestones: List[MilestoneState] = Field(default_factory=list)

    # ── Events ──
    current_events: List[GameEvent] = Field(default_factory=list)
    resolved_event_ids: List[str] = Field(default_factory=list)
    pending_event: Optional[GameEvent] = None

    # ── Advisory chat ──
    chat_messages: List[ChatMessage] = Field(default_factory=list)
    chat_context_event: Optional[str] = None

    # ── Board review chat ──
    board_chat_messages: List[ChatMessage] = Field(default_factory=list)
    board_chat_outcome: Optional[Dict] = None  # stores final verdict outcome

    # ── Partner tracking ──
    disagreement_cycles: int = 0
    partner_departed: bool = False

    # ── VC ──
    vc_cycle: int = 0
    last_board_review_quarter: int = 0

    # ── Outcome ──
    game_over: bool = False
    game_over_reason: Optional[str] = None
    success_probability: float = 0.5
    quarter_log: List[QuarterLog] = Field(default_factory=list)

    # ── Computed properties ──

    @property
    def ap_available(self) -> int:
        """Action points remaining this quarter."""
        return max(0, self.ap_base + self.ap_bonus - self.ap_spent)

    @property
    def runway_months(self) -> float:
        """Months of cash remaining at current net burn."""
        net_burn = self.burn_rate - self.revenue
        if net_burn <= 0:
            return 99.0  # profitable
        return round(self.cash / net_burn, 1) if self.cash > 0 else 0.0

    @property
    def quarters_remaining(self) -> int:
        return max(0, 8 - self.current_quarter)

    @property
    def is_bankrupt(self) -> bool:
        return self.cash <= 0

    @property
    def milestones_completed(self) -> int:
        return sum(1 for m in self.milestones if m.completed)

    @property
    def staff_salary_total(self) -> int:
        return sum(s.salary for s in self.staff)

    def to_ml_features(self) -> Dict[str, Any]:
        """Return feature dict compatible with the ML predictor."""
        bg_map = {0: "first_time", 1: "business", 2: "technical"}
        bg = bg_map.get(self.founder_background, "first_time") if isinstance(self.founder_background, int) else self.founder_background
        return {
            "quarter":              self.current_quarter,
            "runway_months":        min(self.runway_months, 36.0),
            "funding_stage":        self.funding_stage,
            "revenue_monthly_k":    round(self.revenue / 1_000, 2),
            "burn_rate_monthly_k":  round(self.burn_rate / 1_000, 2),
            "founder_experience":   self.founder_experience,
            "founder_background":   bg,
            "sector":               self.sector,
            "milestones_completed": self.milestones_completed,
            "staff_count":          len(self.staff),
            "equity_given":         round(self.equity_given, 1),
        }

    def summary_dict(self) -> Dict[str, Any]:
        """Compact state dict for frontend consumption."""
        return {
            "game_id": self.game_id,
            "current_quarter": self.current_quarter,
            "phase": self.phase,
            "cash": self.cash,
            "burn_rate": self.burn_rate,
            "revenue": self.revenue,
            "valuation": self.valuation,
            "funding_stage": self.funding_stage,
            "equity_given": self.equity_given,
            "stats": self.stats,
            "ap_available": self.ap_available,
            "ap_base": self.ap_base,
            "ap_bonus": self.ap_bonus,
            "ap_spent": self.ap_spent,
            "market_condition": self.market_condition,
            "active_shock": self.active_shock.model_dump() if self.active_shock else None,
            "rivals": [r.model_dump() for r in self.rivals],
            "milestones": [m.model_dump() for m in self.milestones],
            "milestones_completed": self.milestones_completed,
            "current_events": [e.model_dump() for e in self.current_events],
            "pending_event": self.pending_event.model_dump() if self.pending_event else None,
            "staff": [s.model_dump() for s in self.staff],
            "staff_salary_total": self.staff_salary_total,
            "runway_months": self.runway_months,
            "sector": self.sector,
            "celebrity": {"name": self.celebrity.get("name", ""), "domain": self.celebrity.get("domain", "")},
            "professor": {"name": self.professor.get("name", ""), "domain": self.professor.get("domain", "")},
            "classmate_name": self.classmate.get("name", ""),
            "country_name": self.country.get("country", ""),
            "synergy_names": self.synergy_data.get("unlocked_synergies", []),
            "partner_departed": self.partner_departed,
            "disagreement_cycles": self.disagreement_cycles,
            "success_probability": self.success_probability,
            "game_over": self.game_over,
            "game_over_reason": self.game_over_reason,
            "quarter_log": [q.model_dump() for q in self.quarter_log],
        }
