from pathlib import Path
from typing import Any, Dict, List, Optional
import csv


DATA_PATH = Path(__file__).resolve().parents[2] / "data" / "classmates.csv"


PARTNER_OPTIONS: List[Dict[str, Any]] = [
    {
        "name": "Technical Co-founder",
        "style": "build",
        "description": "Strong engineering depth, higher product velocity, better execution on technical risk.",
        "budget_multiplier": 1.05,
        "burn_multiplier": 1.08,
        "synergy_bonus": 0.14,
    },
    {
        "name": "Commercial Co-founder",
        "style": "sell",
        "description": "Stronger GTM, sales momentum, and investor narrative.",
        "budget_multiplier": 1.08,
        "burn_multiplier": 1.03,
        "synergy_bonus": 0.12,
    },
    {
        "name": "Operator Co-founder",
        "style": "scale",
        "description": "Focuses on hiring, process, and operational stability.",
        "budget_multiplier": 1.06,
        "burn_multiplier": 1.02,
        "synergy_bonus": 0.10,
    },
    {
        "name": "Research Co-founder",
        "style": "discover",
        "description": "Useful for deep product innovation, R&D-heavy ventures, and grant applications.",
        "budget_multiplier": 1.03,
        "burn_multiplier": 1.05,
        "synergy_bonus": 0.11,
    },
]


def get_classmates() -> List[Dict[str, str]]:
    if not DATA_PATH.exists():
        return []

    with DATA_PATH.open("r", encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle)
        return [
            {
                "name": row.get("name", "").strip(),
                "linkedin_url": row.get("linkedin_url", "").strip(),
                "notes": row.get("notes", "").strip(),
                "country": row.get("country", "").strip(),
                "years_experience": row.get("years_experience", "").strip(),
                "background": row.get("background", "").strip(),
                "sector_tags": row.get("sector_tags", "").strip(),
            }
            for row in reader
            if row.get("name")
        ]


def parse_classmate_years_experience(classmate: Dict[str, str]) -> Optional[int]:
    raw = (classmate.get("years_experience") or "").strip()
    if not raw:
        return None
    try:
        years = int(raw)
    except ValueError:
        return None
    return max(0, min(25, years))


def parse_classmate_sector_tags(classmate: Dict[str, str]) -> List[str]:
    raw = (classmate.get("sector_tags") or "").strip()
    if not raw:
        return []
    return [tag.strip() for tag in raw.split("|") if tag.strip()]


def get_partner_options() -> List[Dict[str, Any]]:
    return PARTNER_OPTIONS


def get_classmate_by_name(name: str) -> Optional[Dict[str, str]]:
    if not name:
        return None
    for classmate in get_classmates():
        if classmate["name"].lower() == name.lower():
            return classmate
    return None


def get_partner_by_name(name: str) -> Optional[Dict[str, Any]]:
    if not name:
        return None
    for partner in PARTNER_OPTIONS:
        if partner["name"].lower() == name.lower():
            return partner
    return None
