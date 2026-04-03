"""
Milestones for the 8-quarter startup simulation.

3 milestones per sector (conservative / balanced / ambitious).
Each milestone has stat thresholds and/or financial requirements.
The player must complete all 3 before Q8 or bankruptcy to win.
"""

from __future__ import annotations
from typing import Any, Dict, List


def _ms(
    id: str,
    name: str,
    description: str,
    sector: str,
    tier: str,
    stat_requirements: dict | None = None,
    financial_requirements: dict | None = None,
) -> Dict[str, Any]:
    return {
        "id": id,
        "name": name,
        "description": description,
        "sector": sector,
        "tier": tier,
        "stat_requirements": stat_requirements or {},
        "financial_requirements": financial_requirements or {},
        "completed": False,
        "completed_quarter": None,
    }


# ═══════════════════════════════════════════════════════════════════
# AI MILESTONES
# ═══════════════════════════════════════════════════════════════════

AI_MILESTONES: List[Dict[str, Any]] = [
    _ms("AI-M1", "Model-Market Fit",
        "Achieve product-market fit: your AI model is deployed in production with paying customers.",
        "AI", "conservative",
        stat_requirements={"product": 8, "tech": 10},
        financial_requirements={"revenue": 15000}),

    _ms("AI-M2", "Enterprise Pipeline",
        "Build a robust enterprise sales pipeline with multiple signed contracts.",
        "AI", "balanced",
        stat_requirements={"growth": 10, "finance": 8, "brand": 8},
        financial_requirements={"revenue": 40000}),

    _ms("AI-M3", "AI Platform Dominance",
        "Become the go-to platform in your AI niche. Ecosystem of developers and integrations.",
        "AI", "ambitious",
        stat_requirements={"tech": 15, "innovation": 14, "growth": 12},
        financial_requirements={"valuation": 5000000}),
]

# ═══════════════════════════════════════════════════════════════════
# FINTECH MILESTONES
# ═══════════════════════════════════════════════════════════════════

FINTECH_MILESTONES: List[Dict[str, Any]] = [
    _ms("FIN-M1", "Regulatory Cleared",
        "Obtain all necessary regulatory approvals and achieve compliance certification.",
        "Fintech", "conservative",
        stat_requirements={"ops": 10, "finance": 8},
        financial_requirements={"cash": 100000}),

    _ms("FIN-M2", "Banking Partner Signed",
        "Secure a partnership with a major bank or financial institution.",
        "Fintech", "balanced",
        stat_requirements={"brand": 10, "ops": 10, "finance": 10},
        financial_requirements={"revenue": 35000}),

    _ms("FIN-M3", "Financial Infrastructure",
        "Process $10M+ in transactions. Your rails are trusted by institutions.",
        "Fintech", "ambitious",
        stat_requirements={"tech": 14, "ops": 14, "finance": 12},
        financial_requirements={"valuation": 5000000}),
]

# ═══════════════════════════════════════════════════════════════════
# SAAS MILESTONES
# ═══════════════════════════════════════════════════════════════════

SAAS_MILESTONES: List[Dict[str, Any]] = [
    _ms("SAAS-M1", "Product-Led Growth",
        "Achieve consistent organic signups through product virality and word of mouth.",
        "SaaS", "conservative",
        stat_requirements={"product": 10, "growth": 8},
        financial_requirements={"revenue": 12000}),

    _ms("SAAS-M2", "Net Revenue Retention > 120%",
        "Existing customers expand their usage and spend more each quarter.",
        "SaaS", "balanced",
        stat_requirements={"product": 10, "finance": 10, "brand": 8},
        financial_requirements={"revenue": 30000}),

    _ms("SAAS-M3", "Platform Ecosystem",
        "Third-party developers build on your API. Marketplace of integrations.",
        "SaaS", "ambitious",
        stat_requirements={"tech": 14, "growth": 12, "innovation": 12},
        financial_requirements={"valuation": 5000000}),
]

# ═══════════════════════════════════════════════════════════════════
# HEALTHTECH MILESTONES
# ═══════════════════════════════════════════════════════════════════

HEALTHTECH_MILESTONES: List[Dict[str, Any]] = [
    _ms("HT-M1", "Clinical Validation",
        "Complete a clinical study demonstrating efficacy of your health product.",
        "Healthtech", "conservative",
        stat_requirements={"innovation": 10, "tech": 8},
        financial_requirements={"cash": 80000}),

    _ms("HT-M2", "Hospital System Rollout",
        "Deploy your product across a major hospital network.",
        "Healthtech", "balanced",
        stat_requirements={"ops": 10, "brand": 10, "product": 8},
        financial_requirements={"revenue": 35000}),

    _ms("HT-M3", "FDA Approved Market Leader",
        "Achieve FDA clearance and become the standard of care in your category.",
        "Healthtech", "ambitious",
        stat_requirements={"ops": 14, "innovation": 14, "brand": 12},
        financial_requirements={"valuation": 5000000}),
]

# ═══════════════════════════════════════════════════════════════════
# E-COMMERCE MILESTONES
# ═══════════════════════════════════════════════════════════════════

ECOMMERCE_MILESTONES: List[Dict[str, Any]] = [
    _ms("EC-M1", "Brand Recognition",
        "Establish brand recognition in your niche with strong repeat purchase rate.",
        "E-commerce", "conservative",
        stat_requirements={"brand": 10, "growth": 8},
        financial_requirements={"revenue": 20000}),

    _ms("EC-M2", "Supply Chain Mastery",
        "Optimize supply chain to achieve industry-leading margins and fulfillment speed.",
        "E-commerce", "balanced",
        stat_requirements={"ops": 12, "finance": 10, "execution": 8},
        financial_requirements={"revenue": 40000}),

    _ms("EC-M3", "Category Dominant",
        "Become the #1 brand in your product category across multiple channels.",
        "E-commerce", "ambitious",
        stat_requirements={"brand": 14, "growth": 14, "ops": 12},
        financial_requirements={"valuation": 5000000}),
]


# ═══════════════════════════════════════════════════════════════════
# MASTER LIST + HELPERS
# ═══════════════════════════════════════════════════════════════════

ALL_MILESTONES: List[Dict[str, Any]] = (
    AI_MILESTONES
    + FINTECH_MILESTONES
    + SAAS_MILESTONES
    + HEALTHTECH_MILESTONES
    + ECOMMERCE_MILESTONES
)

SECTOR_MILESTONE_MAP: Dict[str, List[Dict[str, Any]]] = {
    "AI": AI_MILESTONES,
    "Fintech": FINTECH_MILESTONES,
    "SaaS": SAAS_MILESTONES,
    "Healthtech": HEALTHTECH_MILESTONES,
    "E-commerce": ECOMMERCE_MILESTONES,
}


def get_milestones_for_sector(sector: str) -> List[Dict[str, Any]]:
    """Return the 3 milestones (conservative, balanced, ambitious) for a given sector."""
    return SECTOR_MILESTONE_MAP.get(sector, AI_MILESTONES)


def get_milestone_by_id(milestone_id: str) -> Dict[str, Any] | None:
    """Look up any milestone by ID."""
    for ms in ALL_MILESTONES:
        if ms["id"] == milestone_id:
            return ms
    return None
