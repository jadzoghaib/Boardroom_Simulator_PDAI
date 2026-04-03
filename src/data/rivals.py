"""
Rival companies for the 8-quarter startup simulation.

3 competitors per sector (15 total) with CEO personality, team, and scores.
Each quarter, rivals simulate progress (1-3 points, market-adjusted).
Rivals can beat the player to milestones → valuation penalty.
"""

from __future__ import annotations

import random
from typing import Any, Dict, List


# ═══════════════════════════════════════════════════════════════════
# RIVAL TEMPLATES (3 per sector)
# ═══════════════════════════════════════════════════════════════════

RIVAL_TEMPLATES: Dict[str, List[Dict[str, Any]]] = {
    "AI": [
        {
            "name": "NeuralForge",
            "ceo": "Dr. Sarah Chen",
            "description": "Stanford spin-off with deep pockets and a published paper trail.",
            "base_growth": 2.2,
            "personality": "academic",
        },
        {
            "name": "CogniTech AI",
            "ceo": "Marcus Williams",
            "description": "Scrappy Y Combinator grad moving fast and breaking things.",
            "base_growth": 2.5,
            "personality": "aggressive",
        },
        {
            "name": "SynthMind",
            "ceo": "Anika Patel",
            "description": "Enterprise-focused AI with Fortune 500 contracts already signed.",
            "base_growth": 1.8,
            "personality": "corporate",
        },
    ],
    "Fintech": [
        {
            "name": "PayStream",
            "ceo": "James Morton",
            "description": "Ex-Goldman team building next-gen payment rails.",
            "base_growth": 2.0,
            "personality": "corporate",
        },
        {
            "name": "FinLeap",
            "ceo": "Elena Vogt",
            "description": "Berlin-based neobank expanding aggressively into new markets.",
            "base_growth": 2.3,
            "personality": "aggressive",
        },
        {
            "name": "TrustVault",
            "ceo": "David Okonkwo",
            "description": "Security-first fintech with banking licenses in 12 countries.",
            "base_growth": 1.7,
            "personality": "conservative",
        },
    ],
    "SaaS": [
        {
            "name": "CloudPilot",
            "ceo": "Rachel Kim",
            "description": "Product-led growth machine with viral onboarding.",
            "base_growth": 2.4,
            "personality": "aggressive",
        },
        {
            "name": "WorkflowHQ",
            "ceo": "Tom Bradley",
            "description": "Enterprise workflow automation backed by Andreessen Horowitz.",
            "base_growth": 2.0,
            "personality": "corporate",
        },
        {
            "name": "MetricStack",
            "ceo": "Priya Sharma",
            "description": "Analytics SaaS with a cult following among data teams.",
            "base_growth": 2.1,
            "personality": "academic",
        },
    ],
    "Healthtech": [
        {
            "name": "MediBridge",
            "ceo": "Dr. Lisa Huang",
            "description": "FDA-cleared diagnostics platform with hospital partnerships.",
            "base_growth": 1.8,
            "personality": "conservative",
        },
        {
            "name": "VitalAI",
            "ceo": "Omar Farooq",
            "description": "AI-powered patient monitoring with Series B funding.",
            "base_growth": 2.2,
            "personality": "academic",
        },
        {
            "name": "HealthLoop",
            "ceo": "Maria Santos",
            "description": "Consumer health app going viral on TikTok.",
            "base_growth": 2.5,
            "personality": "aggressive",
        },
    ],
    "E-commerce": [
        {
            "name": "ShopWave",
            "ceo": "Alex Turner",
            "description": "DTC brand with 500K Instagram followers and celebrity endorsements.",
            "base_growth": 2.3,
            "personality": "aggressive",
        },
        {
            "name": "CartLogic",
            "ceo": "Nina Johansson",
            "description": "B2B e-commerce infrastructure used by 200+ brands.",
            "base_growth": 1.9,
            "personality": "corporate",
        },
        {
            "name": "GreenCart",
            "ceo": "Daniel Osei",
            "description": "Sustainable e-commerce platform with a loyal niche audience.",
            "base_growth": 2.0,
            "personality": "conservative",
        },
    ],
}


# ═══════════════════════════════════════════════════════════════════
# MARKET CONDITION GROWTH MODIFIERS FOR RIVALS
# ═══════════════════════════════════════════════════════════════════

MARKET_GROWTH_MODS: Dict[str, float] = {
    "ai_hype": 1.3,
    "ai_winter": 0.6,
    "regulation_wave": 0.8,
    "talent_war": 0.9,
    "boom": 1.3,
    "recession": 0.5,
    "stable": 1.0,
}


# ═══════════════════════════════════════════════════════════════════
# FUNCTIONS
# ═══════════════════════════════════════════════════════════════════

def get_rivals_for_sector(sector: str) -> List[Dict[str, Any]]:
    """Return 3 rival templates for the given sector, initialized with score=0."""
    templates = RIVAL_TEMPLATES.get(sector, RIVAL_TEMPLATES["AI"])
    return [
        {
            "name": r["name"],
            "ceo": r["ceo"],
            "sector": sector,
            "score": 0,
            "momentum": "steady",
            "milestones_hit": 0,
            "description": r["description"],
            "base_growth": r["base_growth"],
            "personality": r["personality"],
        }
        for r in templates
    ]


def simulate_rival_quarter(rival: Dict[str, Any], market_condition: str) -> Dict[str, Any]:
    """
    Simulate one quarter of rival progress.
    Returns updated rival dict with new score and momentum.
    """
    base = rival.get("base_growth", 2.0)
    market_mod = MARKET_GROWTH_MODS.get(market_condition, 1.0)

    # Personality affects variance
    personality = rival.get("personality", "corporate")
    if personality == "aggressive":
        variance = random.uniform(-0.5, 1.5)
    elif personality == "conservative":
        variance = random.uniform(0.0, 0.8)
    elif personality == "academic":
        variance = random.uniform(-0.3, 1.0)
    else:  # corporate
        variance = random.uniform(-0.2, 1.0)

    growth = max(0, int(round(base * market_mod + variance)))
    old_score = rival.get("score", 0)
    new_score = old_score + growth

    # Determine momentum
    if growth >= 3:
        momentum = "rising"
    elif growth <= 0:
        momentum = "falling"
    else:
        momentum = "steady"

    # Milestone check: rivals hit milestones at score thresholds
    milestones_hit = rival.get("milestones_hit", 0)
    milestone_thresholds = [8, 18, 30]
    for threshold in milestone_thresholds:
        if new_score >= threshold and old_score < threshold:
            milestones_hit += 1

    return {
        **rival,
        "score": new_score,
        "momentum": momentum,
        "milestones_hit": milestones_hit,
    }


def get_rival_news(rival: Dict[str, Any]) -> str:
    """Generate a short news blurb about a rival based on their momentum."""
    name = rival["name"]
    ceo = rival["ceo"]
    momentum = rival.get("momentum", "steady")

    rising_news = [
        f"{name} raises another round — {ceo} seen celebrating on LinkedIn.",
        f"{name} launches killer feature. Industry takes notice.",
        f"{name} signs partnership with major enterprise client.",
        f"TechCrunch profiles {name}: 'One to watch this year.'",
    ]
    steady_news = [
        f"{name} continues steady execution under {ceo}'s leadership.",
        f"{name} ships incremental update. Nothing flashy.",
        f"{name} is quietly building. No drama, no headlines.",
    ]
    falling_news = [
        f"{name} reportedly struggling with internal conflicts.",
        f"Glassdoor reviews for {name} take a nosedive.",
        f"{name} loses key engineer to competitor.",
        f"Rumors swirl about leadership shake-up at {name}.",
    ]

    if momentum == "rising":
        return random.choice(rising_news)
    elif momentum == "falling":
        return random.choice(falling_news)
    else:
        return random.choice(steady_news)
