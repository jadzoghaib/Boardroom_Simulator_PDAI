"""
Market dynamics for the 8-quarter startup simulation.

7 market conditions with Markov chain transitions.
Each condition affects revenue/burn multipliers and stat modifiers.
Includes news headlines per condition and market shock logic.
"""

from __future__ import annotations

import random
from typing import Any, Dict, List, Tuple


# ═══════════════════════════════════════════════════════════════════
# MARKET CONDITIONS
# ═══════════════════════════════════════════════════════════════════

MARKET_CONDITIONS: Dict[str, Dict[str, Any]] = {
    "ai_hype": {
        "label": "AI Hype",
        "emoji": "🤖",
        "description": "AI mania grips the market. Everyone wants in.",
        "revenue_mult": 1.3,
        "burn_mult": 1.1,
        "stat_mods": {"growth": 2, "innovation": 1},
    },
    "ai_winter": {
        "label": "AI Winter",
        "emoji": "❄️",
        "description": "AI skepticism rises. Budgets freeze.",
        "revenue_mult": 0.7,
        "burn_mult": 0.95,
        "stat_mods": {"growth": -2, "innovation": -1},
    },
    "regulation_wave": {
        "label": "Regulation Wave",
        "emoji": "📋",
        "description": "Governments crack down. Compliance costs surge.",
        "revenue_mult": 0.9,
        "burn_mult": 1.15,
        "stat_mods": {"ops": -1, "finance": -1},
    },
    "talent_war": {
        "label": "Talent War",
        "emoji": "🎯",
        "description": "Big tech is poaching everyone. Salaries skyrocket.",
        "revenue_mult": 1.0,
        "burn_mult": 1.2,
        "stat_mods": {"ops": -2, "execution": -1},
    },
    "boom": {
        "label": "Economic Boom",
        "emoji": "🚀",
        "description": "Markets soar. Customers spend freely. VCs write checks.",
        "revenue_mult": 1.25,
        "burn_mult": 1.05,
        "stat_mods": {"growth": 2, "finance": 1},
    },
    "recession": {
        "label": "Recession",
        "emoji": "📉",
        "description": "Economy contracts. Budgets slashed. Survival mode.",
        "revenue_mult": 0.6,
        "burn_mult": 0.9,
        "stat_mods": {"growth": -2, "finance": -2},
    },
    "stable": {
        "label": "Stable",
        "emoji": "⚖️",
        "description": "Markets are calm. Business as usual.",
        "revenue_mult": 1.0,
        "burn_mult": 1.0,
        "stat_mods": {},
    },
}


# ═══════════════════════════════════════════════════════════════════
# TRANSITION MATRIX (Markov chain)
# ═══════════════════════════════════════════════════════════════════
# Each row sums to 1.0. Order: ai_hype, ai_winter, regulation_wave,
# talent_war, boom, recession, stable

CONDITION_ORDER = ["ai_hype", "ai_winter", "regulation_wave", "talent_war", "boom", "recession", "stable"]

TRANSITION_MATRIX: Dict[str, List[Tuple[str, float]]] = {
    "ai_hype":          [("ai_hype", 0.30), ("ai_winter", 0.15), ("regulation_wave", 0.15), ("talent_war", 0.10), ("boom", 0.15), ("recession", 0.05), ("stable", 0.10)],
    "ai_winter":        [("ai_hype", 0.10), ("ai_winter", 0.25), ("regulation_wave", 0.10), ("talent_war", 0.05), ("boom", 0.10), ("recession", 0.20), ("stable", 0.20)],
    "regulation_wave":  [("ai_hype", 0.10), ("ai_winter", 0.10), ("regulation_wave", 0.25), ("talent_war", 0.10), ("boom", 0.10), ("recession", 0.15), ("stable", 0.20)],
    "talent_war":       [("ai_hype", 0.15), ("ai_winter", 0.05), ("regulation_wave", 0.10), ("talent_war", 0.25), ("boom", 0.20), ("recession", 0.05), ("stable", 0.20)],
    "boom":             [("ai_hype", 0.15), ("ai_winter", 0.05), ("regulation_wave", 0.10), ("talent_war", 0.15), ("boom", 0.25), ("recession", 0.10), ("stable", 0.20)],
    "recession":        [("ai_hype", 0.05), ("ai_winter", 0.15), ("regulation_wave", 0.10), ("talent_war", 0.05), ("boom", 0.10), ("recession", 0.30), ("stable", 0.25)],
    "stable":           [("ai_hype", 0.12), ("ai_winter", 0.08), ("regulation_wave", 0.10), ("talent_war", 0.10), ("boom", 0.15), ("recession", 0.10), ("stable", 0.35)],
}


def transition_market(current_condition: str) -> str:
    """Sample next market condition from the Markov transition matrix."""
    transitions = TRANSITION_MATRIX.get(current_condition, TRANSITION_MATRIX["stable"])
    roll = random.random()
    cumulative = 0.0
    for condition, probability in transitions:
        cumulative += probability
        if roll <= cumulative:
            return condition
    return "stable"


# ═══════════════════════════════════════════════════════════════════
# NEWS HEADLINES
# ═══════════════════════════════════════════════════════════════════

NEWS_HEADLINES: Dict[str, List[str]] = {
    "ai_hype": [
        "🤖 'Every Company Is Now an AI Company' — Wall Street Journal",
        "🤖 OpenAI valued at $300B. Your dentist is building an AI startup.",
        "🤖 VC Partner: 'If it doesn't have AI in the name, I'm not reading the deck.'",
        "🤖 Stanford reports 400% increase in AI startup applications",
        "🤖 NVIDIA stock hits all-time high — again",
    ],
    "ai_winter": [
        "❄️ 'AI Bubble Bursting?' — Bloomberg",
        "❄️ Enterprise AI budgets frozen amid ROI concerns",
        "❄️ Three AI unicorns quietly shut down this month",
        "❄️ 'Show me the revenue' — VCs demand profitability from AI startups",
        "❄️ AI fatigue sets in: customers tired of ChatGPT wrappers",
    ],
    "regulation_wave": [
        "📋 EU AI Act enters enforcement phase — startups scramble",
        "📋 SEC announces new compliance framework for fintech",
        "📋 GDPR fines triple year-over-year",
        "📋 Congress holds hearings on startup labor practices",
        "📋 New data sovereignty laws create compliance nightmares",
    ],
    "talent_war": [
        "🎯 Google offers $800K packages to poach startup engineers",
        "🎯 Average ML engineer salary hits $350K in Bay Area",
        "🎯 'The Great Resignation 2.0' — startups hemorrhaging talent",
        "🎯 Remote work policies become key hiring differentiator",
        "🎯 Startups offer 4-day weeks to compete with Big Tech salaries",
    ],
    "boom": [
        "🚀 Markets rally for 6th consecutive month",
        "🚀 VC funding hits record $200B globally",
        "🚀 Consumer spending surges — best quarter in a decade",
        "🚀 IPO window wide open — three startups go public this week",
        "🚀 'Best time to build a company since 2007' — Sequoia partner",
    ],
    "recession": [
        "📉 Markets tumble 15% in worst quarter since 2008",
        "📉 Mass layoffs sweep tech sector — 50K jobs cut this month",
        "📉 VC firm: 'We're only funding profitable companies now'",
        "📉 Consumer confidence at 10-year low",
        "📉 Default rates spike — credit tightens for startups",
    ],
    "stable": [
        "⚖️ Markets flat. Nothing exciting. Just the way CFOs like it.",
        "⚖️ Steady quarter — no drama, no fireworks",
        "⚖️ Analysts: 'This calm won't last forever'",
        "⚖️ Business as usual. Build, ship, sell.",
        "⚖️ 'Boring is good' — startup advisors everywhere",
    ],
}


def get_headline(condition: str) -> str:
    """Return a random news headline for the given market condition."""
    headlines = NEWS_HEADLINES.get(condition, NEWS_HEADLINES["stable"])
    return random.choice(headlines)


# ═══════════════════════════════════════════════════════════════════
# MARKET SHOCKS
# ═══════════════════════════════════════════════════════════════════

SHOCK_TEMPLATES: List[Dict[str, Any]] = [
    {
        "name": "Black Swan Crash",
        "description": "An unexpected market crash wipes out paper valuations.",
        "effects": {"revenue_mult": 0.5, "valuation_mult": 0.7},
        "duration_quarters": 2,
    },
    {
        "name": "Tech Bubble Pop",
        "description": "The tech sector corrects sharply. Funding evaporates.",
        "effects": {"revenue_mult": 0.6, "burn_mult": 0.9},
        "duration_quarters": 2,
    },
    {
        "name": "Regulatory Crackdown",
        "description": "Sweeping new regulations catch the industry off guard.",
        "effects": {"burn_mult": 1.25, "revenue_mult": 0.85},
        "duration_quarters": 1,
    },
    {
        "name": "Talent Exodus",
        "description": "A major employer opens a campus nearby, poaching talent.",
        "effects": {"burn_mult": 1.3},
        "duration_quarters": 1,
    },
    {
        "name": "Demand Surge",
        "description": "Unexpected demand spike from a global event.",
        "effects": {"revenue_mult": 1.5, "burn_mult": 1.1},
        "duration_quarters": 1,
    },
    {
        "name": "Currency Shock",
        "description": "Currency volatility impacts international revenue.",
        "effects": {"revenue_mult": 0.8},
        "duration_quarters": 1,
    },
    {
        "name": "Supply Chain Crisis",
        "description": "Global supply chain disruption hits operations.",
        "effects": {"burn_mult": 1.2, "revenue_mult": 0.9},
        "duration_quarters": 2,
    },
    {
        "name": "Pandemic Scare",
        "description": "Health crisis fears cause economic uncertainty.",
        "effects": {"revenue_mult": 0.7, "burn_mult": 0.85},
        "duration_quarters": 2,
    },
]


def maybe_generate_shock(quarter: int, current_condition: str) -> Dict[str, Any] | None:
    """
    25% chance of a shock per quarter (Q2+).
    Returns a shock dict or None.
    """
    if quarter < 2:
        return None
    if random.random() > 0.25:
        return None

    template = random.choice(SHOCK_TEMPLATES)
    return {
        "name": template["name"],
        "description": template["description"],
        "effects": dict(template["effects"]),
        "duration_quarters": template["duration_quarters"],
        "quarters_remaining": template["duration_quarters"],
    }


def get_market_multipliers(condition: str, active_shock: dict | None = None) -> Dict[str, float]:
    """
    Return effective revenue_mult and burn_mult considering
    both the market condition and any active shock.
    """
    cond = MARKET_CONDITIONS.get(condition, MARKET_CONDITIONS["stable"])
    rev_mult = cond["revenue_mult"]
    burn_mult = cond["burn_mult"]

    if active_shock:
        effects = active_shock.get("effects", {})
        rev_mult *= effects.get("revenue_mult", 1.0)
        burn_mult *= effects.get("burn_mult", 1.0)

    return {"revenue_mult": round(rev_mult, 3), "burn_mult": round(burn_mult, 3)}


def get_condition_stat_mods(condition: str) -> Dict[str, int]:
    """Return temporary stat modifiers for the current market condition."""
    cond = MARKET_CONDITIONS.get(condition, MARKET_CONDITIONS["stable"])
    return dict(cond.get("stat_mods", {}))
