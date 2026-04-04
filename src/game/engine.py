"""
Core game engine for the 8-quarter startup simulation.

Handles: event drawing, choice application, quarter end,
valuation calculation, milestone checking, game-over detection.
"""

from __future__ import annotations

import random
import copy
from typing import Any, Dict, List, Optional

from src.game.state import (
    GameState, GameEvent, EventChoice, MilestoneState, RivalState,
    MarketShock, QuarterLog, StaffMember, STAT_KEYS, FUNDING_STAGES,
)
from src.data.events import get_events_for_sector, get_shock_events, get_event_by_id
from src.data.milestones import get_milestones_for_sector
from src.data.market import (
    transition_market, maybe_generate_shock, get_market_multipliers,
    get_headline, get_condition_stat_mods, MARKET_CONDITIONS,
)
from src.data.rivals import get_rivals_for_sector, simulate_rival_quarter, get_rival_news


# ═══════════════════════════════════════════════════════════════════
# GAME INITIALIZATION
# ═══════════════════════════════════════════════════════════════════

def create_initial_state(
    classmate: dict,
    celebrity: dict,
    professor: dict,
    country: dict,
    sector: str,
    founder_experience: int,
    founder_background: int,
    synergy_data: dict,
    seeded_physics: dict,
) -> GameState:
    """Create a fresh GameState from setup data."""

    # Build initial stats from partner team final_stats
    final_stats = synergy_data.get("final_stats", {})
    stats = {k: final_stats.get(k, 0) for k in STAT_KEYS}

    # Build ML features
    ml_features = {
        "funding_rounds": seeded_physics.get("funding_rounds", 1),
        "founder_experience_years": founder_experience,
        "team_size": seeded_physics.get("team_size", 4),
        "market_size_billion": seeded_physics.get("market_size_billion", 10.0),
        "product_traction_users": seeded_physics.get("product_traction_users", 1000),
        "burn_rate_million": round(seeded_physics.get("burn_rate", 35000) / 1_000_000, 4),
        "revenue_million": round(seeded_physics.get("revenue", 8000) / 1_000_000, 4),
        "investor_type": seeded_physics.get("investor_type", 0),
        "sector": sector,
        "founder_background": founder_background,
    }

    # Initial valuation based on sector + experience + synergy
    base_val = 800000 + founder_experience * 50000
    synergy_bonus = synergy_data.get("synergy_bonus", 0.0)
    valuation = int(base_val * (1 + synergy_bonus))

    # Initial market condition
    initial_markets = ["stable", "stable", "stable", "ai_hype", "boom"]
    market_condition = random.choice(initial_markets)

    state = GameState(
        classmate=classmate,
        celebrity=celebrity,
        professor=professor,
        country=country,
        sector=sector,
        founder_experience=founder_experience,
        founder_background=founder_background,
        synergy_data=synergy_data,
        current_quarter=1,
        phase="events",
        cash=float(seeded_physics.get("budget", 300000)),
        burn_rate=float(seeded_physics.get("burn_rate", 35000)),
        revenue=float(seeded_physics.get("revenue", 8000)),
        valuation=float(valuation),
        funding_stage="bootstrap",
        equity_given=0.0,
        stats=stats,
        ap_base=6,
        ap_bonus=0,
        ap_spent=0,
        ml_features=ml_features,
        market_condition=market_condition,
        market_history=[market_condition],
        milestones=[
            MilestoneState(**ms)
            for ms in get_milestones_for_sector(sector)
        ],
        rivals=[
            RivalState(**r)
            for r in get_rivals_for_sector(sector)
        ],
    )

    # Draw initial events for Q1
    state = draw_quarter_events(state)

    return state


# ═══════════════════════════════════════════════════════════════════
# EVENT DRAWING
# ═══════════════════════════════════════════════════════════════════

def draw_quarter_events(state: GameState, count: int = 3) -> GameState:
    """Draw 2-3 events for the current quarter. No repeats within a game."""
    phase = "early" if state.current_quarter <= 4 else "late"
    pool = get_events_for_sector(state.sector)

    # Filter by phase and exclude already-resolved events
    available = [
        e for e in pool
        if e["phase"] == phase and e["id"] not in state.resolved_event_ids
    ]

    # If we have a shock, add one shock event
    if state.active_shock and state.current_quarter >= 2:
        shock_pool = [
            s for s in get_shock_events()
            if s["id"] not in state.resolved_event_ids
        ]
        if shock_pool:
            shock_event = random.choice(shock_pool)
            available.append(shock_event)

    # Sample up to `count` events
    count = min(count, len(available))
    if count == 0:
        # Fallback: reset resolved to allow replay of universal events
        state.resolved_event_ids = [
            eid for eid in state.resolved_event_ids
            if not eid.startswith("UNI-")
        ]
        available = [
            e for e in pool
            if e["phase"] == phase and e["id"] not in state.resolved_event_ids
        ]
        count = min(3, len(available))

    selected = random.sample(available, count) if count > 0 else []

    state.current_events = [
        GameEvent(
            id=e["id"],
            title=e["title"],
            description=e["description"],
            department=e.get("department", "general"),
            sector=e.get("sector"),
            phase=e.get("phase", "early"),
            choices=[EventChoice(**c) for c in e.get("choices", [])],
            is_shock=e.get("is_shock", False),
        )
        for e in selected
    ]
    state.pending_event = state.current_events[0] if state.current_events else None
    state.phase = "events"

    return state


# ═══════════════════════════════════════════════════════════════════
# CHOICE APPLICATION
# ═══════════════════════════════════════════════════════════════════

def apply_choice(state: GameState, event_id: str, choice_index: int) -> GameState:
    """Apply a player's choice for an event. Deduct AP, apply effects."""
    # Find the event
    event = None
    for e in state.current_events:
        if e.id == event_id:
            event = e
            break

    if event is None:
        return state

    if choice_index < 0 or choice_index >= len(event.choices):
        return state

    choice = event.choices[choice_index]

    # Check AP
    if state.ap_available < choice.ap_cost:
        return state  # Not enough AP

    # Deduct AP
    state.ap_spent += choice.ap_cost

    # Apply effects
    effects = choice.effects
    for key in STAT_KEYS:
        if key in effects:
            state.stats[key] = max(0, state.stats[key] + effects[key])

    if "cash" in effects:
        state.cash += effects["cash"]
    if "burn_rate" in effects:
        state.burn_rate = max(0, state.burn_rate + effects["burn_rate"])
    if "revenue" in effects:
        state.revenue = max(0, state.revenue + effects["revenue"])
    if "valuation_mult" in effects:
        state.valuation *= effects["valuation_mult"]
    if "equity" in effects:
        state.equity_given += effects["equity"]
    if "traction_users" in effects:
        current = state.ml_features.get("product_traction_users", 1000)
        state.ml_features["product_traction_users"] = current + effects["traction_users"]

    # Mark event as resolved
    state.resolved_event_ids.append(event_id)

    # Remove from current events and advance to next
    state.current_events = [e for e in state.current_events if e.id != event_id]

    if state.current_events:
        state.pending_event = state.current_events[0]
    else:
        state.pending_event = None
        state.phase = "quarter_end"

    return state


def skip_remaining_events(state: GameState) -> GameState:
    """Skip all remaining events this quarter (no AP cost)."""
    state.current_events = []
    state.pending_event = None
    state.phase = "quarter_end"
    return state


# ═══════════════════════════════════════════════════════════════════
# QUARTER END
# ═══════════════════════════════════════════════════════════════════

def end_quarter(state: GameState) -> GameState:
    """
    Finalize the current quarter:
    1. Apply burn/revenue with market multipliers
    2. Deduct staff salaries
    3. Transition market condition
    4. Maybe generate shock
    5. Simulate rivals
    6. Check milestones
    7. Update valuation
    8. Check game over conditions
    9. Advance to next quarter or end game
    """
    q = state.current_quarter

    # ── 1. Financials ──
    mults = get_market_multipliers(state.market_condition,
                                    state.active_shock.model_dump() if state.active_shock else None)
    effective_revenue = state.revenue * mults["revenue_mult"]
    effective_burn = state.burn_rate * mults["burn_mult"]

    # Add staff salaries to burn
    staff_cost = state.staff_salary_total
    total_burn = effective_burn + staff_cost

    # Net cash change for the quarter (3 months)
    net = (effective_revenue - total_burn) * 3
    cash_start = state.cash
    state.cash = round(state.cash + net, 2)

    # Update ML features
    state.ml_features["burn_rate_million"] = round(total_burn / 1_000_000, 4)
    state.ml_features["revenue_million"] = round(effective_revenue / 1_000_000, 4)

    # ── 2. Market transition ──
    new_condition = transition_market(state.market_condition)
    state.market_condition = new_condition
    state.market_history.append(new_condition)

    # ── 3. Shock handling ──
    if state.active_shock:
        state.active_shock.quarters_remaining -= 1
        if state.active_shock.quarters_remaining <= 0:
            state.active_shock = None

    if state.active_shock is None:
        shock = maybe_generate_shock(q, new_condition)
        if shock:
            state.active_shock = MarketShock(**shock)

    # ── 4. Simulate rivals ──
    updated_rivals = []
    for rival in state.rivals:
        updated = simulate_rival_quarter(rival.model_dump(), state.market_condition)
        updated_rivals.append(RivalState(**updated))
    state.rivals = updated_rivals

    # ── 5. Check milestones ──
    milestones_hit_this_q = []
    for ms in state.milestones:
        if ms.completed:
            continue
        if _check_milestone(state, ms):
            ms.completed = True
            ms.completed_quarter = q
            milestones_hit_this_q.append(ms.name)

    # ── 6. Update valuation ──
    state.valuation = calculate_valuation(state)

    # ── 7. Quarter log ──
    state.quarter_log.append(QuarterLog(
        quarter=q,
        events_resolved=[eid for eid in state.resolved_event_ids[-5:]],  # last few
        cash_start=cash_start,
        cash_end=state.cash,
        revenue=effective_revenue,
        burn_rate=total_burn,
        market_condition=state.market_condition,
        milestones_completed=milestones_hit_this_q,
    ))

    # ── 8. Game over checks ──
    if state.cash <= 0:
        state.game_over = True
        state.game_over_reason = "bankruptcy"
        state.phase = "game_over"
        return state

    if state.milestones_completed >= 3:
        state.game_over = True
        state.game_over_reason = "all_milestones_completed"
        state.phase = "game_over"
        return state

    if q >= 8:
        state.game_over = True
        if state.milestones_completed >= 3:
            state.game_over_reason = "all_milestones_completed"
        elif state.cash > 0:
            state.game_over_reason = "time_up_survived"
        else:
            state.game_over_reason = "time_up_bankrupt"
        state.phase = "game_over"
        return state

    # ── 9. Advance to next quarter ──
    state.current_quarter = q + 1
    state.ap_spent = 0  # Reset AP

    # Recalculate AP bonus from staff
    state.ap_bonus = sum(s.ap_bonus for s in state.staff)

    # Check if board review quarter (Q2, Q4, Q6, Q8)
    if state.current_quarter % 2 == 0:
        state.phase = "board_review"
    else:
        # Draw new events
        state = draw_quarter_events(state)

    return state


# ═══════════════════════════════════════════════════════════════════
# MILESTONE CHECKING
# ═══════════════════════════════════════════════════════════════════

def _check_milestone(state: GameState, milestone: MilestoneState) -> bool:
    """Check if a milestone's requirements are met."""
    # Check stat requirements
    for stat, required in milestone.stat_requirements.items():
        if state.stats.get(stat, 0) < required:
            return False

    # Check financial requirements
    fin = milestone.financial_requirements
    if "revenue" in fin and state.revenue < fin["revenue"]:
        return False
    if "cash" in fin and state.cash < fin["cash"]:
        return False
    if "valuation" in fin and state.valuation < fin["valuation"]:
        return False

    return True


# ═══════════════════════════════════════════════════════════════════
# VALUATION CALCULATION
# ═══════════════════════════════════════════════════════════════════

def calculate_valuation(state: GameState) -> float:
    """
    Calculate startup valuation based on:
    - Revenue (12x ARR for early, 8x for late)
    - Stats sum as quality multiplier
    - Milestones as step-ups
    - Market condition modifier
    - Rival penalty if they're ahead
    """
    # Base: revenue annualized × multiple
    stage_mult = {
        "bootstrap": 15,
        "angels": 12,
        "seed": 10,
        "series_a": 8,
        "series_b": 6,
    }
    multiple = stage_mult.get(state.funding_stage, 10)
    arr = state.revenue * 12
    base_val = arr * multiple

    # Stats quality bonus (sum of all stats / 80 as a multiplier, e.g. 0.5x to 2x)
    stat_sum = sum(state.stats.values())
    stat_mult = max(0.5, min(2.5, stat_sum / 40))

    # Milestone bonus: +25% per milestone completed
    milestone_mult = 1.0 + (state.milestones_completed * 0.25)

    # Market condition modifier
    market_mods = {
        "ai_hype": 1.3, "boom": 1.2, "stable": 1.0,
        "talent_war": 0.95, "regulation_wave": 0.9,
        "ai_winter": 0.75, "recession": 0.6,
    }
    market_mult = market_mods.get(state.market_condition, 1.0)

    # Rival penalty: if any rival has more milestones, -10% per
    rival_penalty = 1.0
    for rival in state.rivals:
        if rival.milestones_hit > state.milestones_completed:
            rival_penalty -= 0.05
    rival_penalty = max(0.7, rival_penalty)

    valuation = base_val * stat_mult * milestone_mult * market_mult * rival_penalty
    return max(100000, round(valuation, -3))  # Floor at $100K, round to nearest $1K


# ═══════════════════════════════════════════════════════════════════
# HIRING / FIRING
# ═══════════════════════════════════════════════════════════════════

def hire_staff(state: GameState, candidate: dict) -> GameState:
    """Hire a candidate into an exec slot."""
    role = candidate["role"]

    # Check if slot already filled
    for s in state.staff:
        if s.role == role:
            return state  # Slot already taken

    member = StaffMember(
        name=candidate["name"],
        role=role,
        salary=candidate.get("salary", 0),
        equity_ask=candidate.get("equity_ask", 0.0),
        ap_bonus=candidate.get("ap_bonus", 0),
        stat_bonuses=candidate.get("stat_bonuses", {}),
        hired_quarter=state.current_quarter,
    )

    state.staff.append(member)
    state.equity_given += member.equity_ask

    # Apply stat bonuses
    for stat, bonus in member.stat_bonuses.items():
        if stat in state.stats:
            state.stats[stat] += bonus

    # Update AP bonus
    state.ap_bonus = sum(s.ap_bonus for s in state.staff)

    return state


def fire_staff(state: GameState, staff_id: str) -> GameState:
    """Fire a staff member. Remove their stat bonuses."""
    target = None
    for s in state.staff:
        if s.id == staff_id:
            target = s
            break

    if target is None:
        return state

    # Remove stat bonuses
    for stat, bonus in target.stat_bonuses.items():
        if stat in state.stats:
            state.stats[stat] = max(0, state.stats[stat] - bonus)

    state.staff = [s for s in state.staff if s.id != staff_id]

    # Recalculate AP bonus
    state.ap_bonus = sum(s.ap_bonus for s in state.staff)

    return state


# ═══════════════════════════════════════════════════════════════════
# FUNDRAISING
# ═══════════════════════════════════════════════════════════════════

FUNDING_OFFERS: Dict[str, Dict[str, Any]] = {
    "bootstrap": {
        "next_stage": "angels",
        "label": "Angel Round",
        "base_amount": 50000,
        "equity_ask": 5.0,
        "valuation_threshold": 500000,
    },
    "angels": {
        "next_stage": "seed",
        "label": "Seed Round",
        "base_amount": 200000,
        "equity_ask": 10.0,
        "valuation_threshold": 1000000,
    },
    "seed": {
        "next_stage": "series_a",
        "label": "Series A",
        "base_amount": 1000000,
        "equity_ask": 15.0,
        "valuation_threshold": 3000000,
    },
    "series_a": {
        "next_stage": "series_b",
        "label": "Series B",
        "base_amount": 5000000,
        "equity_ask": 20.0,
        "valuation_threshold": 10000000,
    },
}


def get_funding_offer(state: GameState) -> Dict[str, Any] | None:
    """Get the current available funding offer, or None if not eligible."""
    offer_template = FUNDING_OFFERS.get(state.funding_stage)
    if offer_template is None:
        return None  # Already at series_b

    if state.valuation < offer_template["valuation_threshold"]:
        return {
            "available": False,
            "reason": f"Valuation must reach ${offer_template['valuation_threshold']:,} (currently ${state.valuation:,.0f})",
            "label": offer_template["label"],
        }

    # Scale amount by valuation
    amount = int(offer_template["base_amount"] * (state.valuation / offer_template["valuation_threshold"]))
    equity = offer_template["equity_ask"]

    return {
        "available": True,
        "label": offer_template["label"],
        "amount": amount,
        "equity": equity,
        "next_stage": offer_template["next_stage"],
        "post_money_valuation": state.valuation + amount,
    }


def accept_funding(state: GameState) -> GameState:
    """Accept the current funding offer."""
    offer = get_funding_offer(state)
    if offer is None or not offer.get("available"):
        return state

    state.cash += offer["amount"]
    state.equity_given += offer["equity"]
    state.funding_stage = offer["next_stage"]
    state.valuation = offer["post_money_valuation"]

    # Update ML features
    current_rounds = state.ml_features.get("funding_rounds", 1)
    state.ml_features["funding_rounds"] = current_rounds + 1
    state.ml_features["investor_type"] = 1 if state.funding_stage in ("series_a", "series_b") else 0

    return state


# ═══════════════════════════════════════════════════════════════════
# QUARTER SUMMARY HELPERS
# ═══════════════════════════════════════════════════════════════════

def get_quarter_summary(state: GameState) -> Dict[str, Any]:
    """Build a summary dict for the quarter-end modal."""
    headline = get_headline(state.market_condition)
    cond = MARKET_CONDITIONS.get(state.market_condition, {})

    rival_news = []
    for rival in state.rivals:
        rival_news.append({
            "name": rival.name,
            "score": rival.score,
            "momentum": rival.momentum,
            "news": get_rival_news(rival.model_dump()),
        })

    last_log = state.quarter_log[-1] if state.quarter_log else None
    # Use the quarter from the last log (the one just completed) or current - 1
    completed_quarter = last_log.quarter if last_log else max(1, state.current_quarter - 1)

    return {
        "quarter": completed_quarter,
        "headline": headline,
        "market_condition": cond.get("label", "Stable"),
        "market_emoji": cond.get("emoji", "⚖️"),
        "cash": state.cash,
        "revenue": state.revenue,
        "burn_rate": state.burn_rate,
        "runway_months": state.runway_months,
        "valuation": state.valuation,
        "net_change": last_log.cash_end - last_log.cash_start if last_log else 0,
        "milestones_completed": state.milestones_completed,
        "milestones_total": len(state.milestones),
        "rival_news": rival_news,
        "shock": state.active_shock.model_dump() if state.active_shock else None,
        "game_over": state.game_over,
        "game_over_reason": state.game_over_reason,
    }
