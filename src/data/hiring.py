"""
Hiring candidates for the 8-quarter startup simulation.

4 exec slots: CTO, CMO, CFO, COO.
3 candidates per slot (12 total) with CVs, salary, equity ask, AP bonus, stat bonuses.
"""

from __future__ import annotations
from typing import Any, Dict, List


CANDIDATES: List[Dict[str, Any]] = [
    # ── CTO candidates ──
    {
        "id": "cto-1",
        "name": "Alex Rivera",
        "role": "CTO",
        "title": "Ex-Google Staff Engineer",
        "bio": "10 years at Google building distributed systems. Led a 40-person team. Obsessed with clean architecture.",
        "salary": 12000,
        "equity_ask": 3.0,
        "ap_bonus": 1,
        "stat_bonuses": {"tech": 4, "execution": 2, "innovation": 1},
    },
    {
        "id": "cto-2",
        "name": "Mei Zhang",
        "role": "CTO",
        "title": "AI Research Lead (ex-DeepMind)",
        "bio": "PhD in ML. Published 20+ papers. Can build anything but hates meetings.",
        "salary": 14000,
        "equity_ask": 4.0,
        "ap_bonus": 0,
        "stat_bonuses": {"tech": 5, "innovation": 4},
    },
    {
        "id": "cto-3",
        "name": "Jordan Blake",
        "role": "CTO",
        "title": "Startup CTO (3rd rodeo)",
        "bio": "Built and sold 2 startups. Scrappy. Ships fast. Code quality? 'We'll fix it later.'",
        "salary": 8000,
        "equity_ask": 5.0,
        "ap_bonus": 1,
        "stat_bonuses": {"tech": 3, "execution": 3, "product": 1},
    },

    # ── CMO candidates ──
    {
        "id": "cmo-1",
        "name": "Sofia Martinez",
        "role": "CMO",
        "title": "VP Marketing (ex-Spotify)",
        "bio": "Built Spotify's growth engine in LATAM. Data-driven marketer who speaks fluent creative.",
        "salary": 10000,
        "equity_ask": 2.5,
        "ap_bonus": 1,
        "stat_bonuses": {"brand": 4, "growth": 3},
    },
    {
        "id": "cmo-2",
        "name": "Tyler Washington",
        "role": "CMO",
        "title": "Growth Hacker (ex-Airbnb)",
        "bio": "Wrote the book on viral loops. Literally — it's on Amazon. All about acquisition, not retention.",
        "salary": 11000,
        "equity_ask": 3.0,
        "ap_bonus": 0,
        "stat_bonuses": {"growth": 5, "brand": 2},
    },
    {
        "id": "cmo-3",
        "name": "Lena Kowalski",
        "role": "CMO",
        "title": "Brand Strategist (ex-Apple)",
        "bio": "Former Apple creative lead. Builds brands that people tattoo on their bodies. Expensive taste.",
        "salary": 13000,
        "equity_ask": 2.0,
        "ap_bonus": 1,
        "stat_bonuses": {"brand": 5, "product": 2, "growth": 1},
    },

    # ── CFO candidates ──
    {
        "id": "cfo-1",
        "name": "David Park",
        "role": "CFO",
        "title": "Investment Banker (ex-Goldman Sachs)",
        "bio": "Spent 8 years on Wall Street. Can model anything. Knows every VC in town.",
        "salary": 12000,
        "equity_ask": 2.0,
        "ap_bonus": 1,
        "stat_bonuses": {"finance": 5, "ops": 1},
    },
    {
        "id": "cfo-2",
        "name": "Aisha Osman",
        "role": "CFO",
        "title": "Startup Finance (3 exits)",
        "bio": "CFO at 3 startups, all acquired. Master of runway extension and creative cap table management.",
        "salary": 9000,
        "equity_ask": 3.5,
        "ap_bonus": 1,
        "stat_bonuses": {"finance": 4, "ops": 2, "execution": 1},
    },
    {
        "id": "cfo-3",
        "name": "Henrik Larsson",
        "role": "CFO",
        "title": "Big 4 Auditor turned Operator",
        "bio": "Deloitte trained. Loves spreadsheets. Zero tolerance for financial sloppiness.",
        "salary": 8000,
        "equity_ask": 2.0,
        "ap_bonus": 0,
        "stat_bonuses": {"finance": 4, "ops": 3},
    },

    # ── COO candidates ──
    {
        "id": "coo-1",
        "name": "Priya Reddy",
        "role": "COO",
        "title": "Operations VP (ex-Amazon)",
        "bio": "Ran fulfillment for Amazon EU. Obsessed with process optimization and Six Sigma.",
        "salary": 11000,
        "equity_ask": 2.5,
        "ap_bonus": 1,
        "stat_bonuses": {"ops": 5, "execution": 3},
    },
    {
        "id": "coo-2",
        "name": "Chris Nakamura",
        "role": "COO",
        "title": "Chief of Staff (ex-Stripe)",
        "bio": "Built Stripe's operational playbook. Calm under pressure. The team trusts him implicitly.",
        "salary": 10000,
        "equity_ask": 3.0,
        "ap_bonus": 1,
        "stat_bonuses": {"ops": 4, "execution": 2, "finance": 1},
    },
    {
        "id": "coo-3",
        "name": "Emma Fischer",
        "role": "COO",
        "title": "Founder-Operator (bootstrapped to $5M ARR)",
        "bio": "Bootstrapped her own startup to $5M ARR. Does everything herself. Might burn out.",
        "salary": 7000,
        "equity_ask": 4.0,
        "ap_bonus": 2,
        "stat_bonuses": {"ops": 3, "execution": 4, "growth": 1},
    },
]


# ═══════════════════════════════════════════════════════════════════
# HELPERS
# ═══════════════════════════════════════════════════════════════════

def get_all_candidates() -> List[Dict[str, Any]]:
    """Return all 12 hiring candidates."""
    return CANDIDATES


def get_candidates_by_role(role: str) -> List[Dict[str, Any]]:
    """Return 3 candidates for a given role (CTO, CMO, CFO, COO)."""
    return [c for c in CANDIDATES if c["role"].upper() == role.upper()]


def get_candidate_by_id(candidate_id: str) -> Dict[str, Any] | None:
    """Look up a candidate by their ID."""
    for c in CANDIDATES:
        if c["id"] == candidate_id:
            return c
    return None


def get_available_roles() -> List[str]:
    """Return the 4 available exec roles."""
    return ["CTO", "CMO", "CFO", "COO"]
