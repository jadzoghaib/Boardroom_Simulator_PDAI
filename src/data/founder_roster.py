from pathlib import Path
from typing import Any, Dict, List, Optional
import csv


DATA_PATH = Path(__file__).resolve().parents[2] / "data" / "classmates.csv"
FACULTY_PDF_DIR = Path(__file__).resolve().parents[2] / "data" / "ESADE Faculty"


STAT_KEYS = ["growth", "brand", "product", "tech", "ops", "finance", "innovation", "execution"]


CELEBRITY_PARTNERS: List[Dict[str, Any]] = [
    {
        "name": "Taylor Swift",
        "domain": "Brand",
        "core_ability": "Cult Builder",
        "description": "Fan loyalty, storytelling, and premium brand momentum.",
        "wikipedia_url": "https://en.wikipedia.org/wiki/Taylor_Swift",
        "avatar_url": "https://upload.wikimedia.org/wikipedia/commons/thumb/f/f1/Taylor_Swift_at_the_2023_Met_Gala.jpg/440px-Taylor_Swift_at_the_2023_Met_Gala.jpg",
        "cost": 8,
        "stats": {"growth": 7, "brand": 10, "product": 5, "tech": 2, "ops": 4, "finance": 6, "innovation": 5, "execution": 7},
    },
    {
        "name": "Elon Musk",
        "domain": "Tech",
        "core_ability": "Moonshot Architect",
        "description": "Breakthrough innovation and aggressive technical bets.",
        "wikipedia_url": "https://en.wikipedia.org/wiki/Elon_Musk",
        "avatar_url": "https://upload.wikimedia.org/wikipedia/commons/thumb/3/34/Elon_Musk_Royal_Society_%28crop2%29.jpg/440px-Elon_Musk_Royal_Society_%28crop2%29.jpg",
        "cost": 10,
        "stats": {"growth": 7, "brand": 8, "product": 7, "tech": 10, "ops": 4, "finance": 5, "innovation": 10, "execution": 5},
    },
    {
        "name": "Steve Jobs",
        "domain": "Product",
        "core_ability": "Product Perfectionist",
        "description": "Elite product taste, UX leadership, and premium positioning.",
        "wikipedia_url": "https://en.wikipedia.org/wiki/Steve_Jobs",
        "avatar_url": "https://upload.wikimedia.org/wikipedia/commons/thumb/8/85/Steve_Jobs_2006-11-05.jpg/440px-Steve_Jobs_2006-11-05.jpg",
        "cost": 10,
        "stats": {"growth": 6, "brand": 10, "product": 10, "tech": 6, "ops": 4, "finance": 7, "innovation": 9, "execution": 7},
    },
    {
        "name": "MrBeast",
        "domain": "Growth",
        "core_ability": "Viral Growth Hacker",
        "description": "Audience acceleration and high-velocity growth loops.",
        "wikipedia_url": "https://en.wikipedia.org/wiki/MrBeast",
        "avatar_url": "https://upload.wikimedia.org/wikipedia/commons/thumb/f/f4/MrBeast_at_VidCon_2015.jpg/440px-MrBeast_at_VidCon_2015.jpg",
        "cost": 7,
        "stats": {"growth": 10, "brand": 8, "product": 4, "tech": 3, "ops": 5, "finance": 3, "innovation": 6, "execution": 7},
    },
    {
        "name": "Warren Buffett",
        "domain": "Finance",
        "core_ability": "Capital Allocator",
        "description": "Capital discipline, risk control, and long-term value focus.",
        "wikipedia_url": "https://en.wikipedia.org/wiki/Warren_Buffett",
        "avatar_url": "https://upload.wikimedia.org/wikipedia/commons/thumb/5/5e/Warren_Buffett_2023.jpg/440px-Warren_Buffett_2023.jpg",
        "cost": 8,
        "stats": {"growth": 3, "brand": 6, "product": 2, "tech": 2, "ops": 8, "finance": 10, "innovation": 3, "execution": 9},
    },
    {
        "name": "Jeff Bezos",
        "domain": "Operations",
        "core_ability": "Scale Engine",
        "description": "Operational systems, reliability, and scalable execution.",
        "wikipedia_url": "https://en.wikipedia.org/wiki/Jeff_Bezos",
        "avatar_url": "https://upload.wikimedia.org/wikipedia/commons/thumb/6/6d/Jeff_Bezos_at_Amazon_Shareholder_Meeting_2023.jpg/440px-Jeff_Bezos_at_Amazon_Shareholder_Meeting_2023.jpg",
        "cost": 9,
        "stats": {"growth": 7, "brand": 5, "product": 7, "tech": 8, "ops": 10, "finance": 8, "innovation": 7, "execution": 9},
    },
    {
        "name": "Albert Einstein",
        "domain": "R&D",
        "core_ability": "Deep Thinker",
        "description": "Long-horizon research thinking and intellectual breakthroughs.",
        "wikipedia_url": "https://en.wikipedia.org/wiki/Albert_Einstein",
        "avatar_url": "https://upload.wikimedia.org/wikipedia/commons/thumb/d/d3/Albert_Einstein_Head.jpg/440px-Albert_Einstein_Head.jpg",
        "cost": 6,
        "stats": {"growth": 1, "brand": 5, "product": 2, "tech": 8, "ops": 1, "finance": 1, "innovation": 10, "execution": 2},
    },
    {
        "name": "Lionel Messi",
        "domain": "Team",
        "core_ability": "Team Synergy",
        "description": "Team cohesion, consistency, and precision execution.",
        "wikipedia_url": "https://en.wikipedia.org/wiki/Lionel_Messi",
        "avatar_url": "https://upload.wikimedia.org/wikipedia/commons/thumb/b/b4/Lionel_Messi_2022.jpg/440px-Lionel_Messi_2022.jpg",
        "cost": 7,
        "stats": {"growth": 5, "brand": 8, "product": 7, "tech": 3, "ops": 6, "finance": 5, "innovation": 5, "execution": 10},
    },
]


PROFESSOR_PARTNERS: List[Dict[str, Any]] = [
    {
        "name": "Oriol Rius",
        "domain": "Technology",
        "core_ability": "Tech Architect",
        "description": "IoT, cloud/devops, and engineering execution depth.",
        "linkedin_url": "https://www.linkedin.com/in/oriolrius/",
        "avatar_url": "https://api.dicebear.com/7.x/avataaars/svg?seed=oriol-rius-prof",
        "cost": 5,
        "stats": {"growth": 3, "brand": 4, "product": 5, "tech": 9, "ops": 8, "finance": 3, "innovation": 7, "execution": 8},
    },
    {
        "name": "Esteve Almirall",
        "domain": "Innovation",
        "core_ability": "Innovation Strategist",
        "description": "Open innovation and digital transformation strategy.",
        "linkedin_url": "https://www.linkedin.com/in/ealmirall/",
        "avatar_url": "https://api.dicebear.com/7.x/avataaars/svg?seed=esteve-almirall-innovation",
        "cost": 4,
        "stats": {"growth": 3, "brand": 5, "product": 5, "tech": 5, "ops": 4, "finance": 4, "innovation": 9, "execution": 5},
    },
    {
        "name": "Jose A. Rodriguez-Serrano",
        "domain": "AI / ML",
        "core_ability": "ML Strategist",
        "description": "Research-to-product AI systems and ML platform design.",
        "linkedin_url": "https://www.linkedin.com/in/jose-a-rodriguez-serrano-46505653/",
        "avatar_url": "https://api.dicebear.com/7.x/avataaars/svg?seed=jose-rodriguez-serrano-aiml",
        "cost": 5,
        "stats": {"growth": 2, "brand": 3, "product": 6, "tech": 10, "ops": 5, "finance": 3, "innovation": 9, "execution": 6},
    },
    {
        "name": "Ruben Coca",
        "domain": "Analytics",
        "core_ability": "Industry Analyst",
        "description": "Decision analytics and financial KPI discipline.",
        "linkedin_url": "https://www.linkedin.com/in/rub%C3%A9n-coca-90a5518/",
        "avatar_url": "https://api.dicebear.com/7.x/avataaars/svg?seed=ruben-coca-analytics",
        "cost": 4,
        "stats": {"growth": 3, "brand": 3, "product": 4, "tech": 6, "ops": 8, "finance": 7, "innovation": 4, "execution": 8},
    },
    {
        "name": "Jordi Nin",
        "domain": "Data Science / AI",
        "core_ability": "Research Scientist",
        "description": "AI and complex systems research depth with industry bridge.",
        "linkedin_url": "https://www.linkedin.com/in/dataminion/",
        "avatar_url": "https://api.dicebear.com/7.x/avataaars/svg?seed=jordi-nin-datasci",
        "cost": 4,
        "stats": {"growth": 2, "brand": 3, "product": 4, "tech": 9, "ops": 4, "finance": 3, "innovation": 10, "execution": 5},
    },
    {
        "name": "Maja Tampe",
        "domain": "Sustainability",
        "core_ability": "Governance Architect",
        "description": "Governance, strategy, and systems-level organizational change.",
        "linkedin_url": "https://www.linkedin.com/in/majatampe/",
        "avatar_url": "https://api.dicebear.com/7.x/avataaars/svg?seed=maja-tampe-governance",
        "cost": 4,
        "stats": {"growth": 3, "brand": 7, "product": 4, "tech": 2, "ops": 5, "finance": 5, "innovation": 6, "execution": 6},
    },
]


FACULTY_FILE_MATCHES: Dict[str, Dict[str, str]] = {
    "Oriol Rius": {
        "linkedin_pdf": "Oriol Rius Linkedin.pdf",
        "profile_pdf": "Oriol_Rius_Canals_Profile.pdf",
    },
    "Esteve Almirall": {
        "linkedin_pdf": "Esteve Almirall Linkedin.pdf",
        "profile_pdf": "Esteve_Almirall_Profile.pdf",
    },
    "Jose A. Rodriguez-Serrano": {
        "linkedin_pdf": "Jose A. Rodriguez-Serrano Linkedin.pdf",
        "profile_pdf": "Jose_Rodriguez_Serrano_Profile.pdf",
    },
    "Ruben Coca": {
        "linkedin_pdf": "Rubén Coca Linkedin.pdf",
        "profile_pdf": "Ruben_Coca_Profile.pdf",
    },
    "Jordi Nin": {
        "linkedin_pdf": "Jordi Nin Linkedin.pdf",
        "profile_pdf": "Jordi_Nin_Profile.pdf",
    },
    "Maja Tampe": {
        "linkedin_pdf": "Maja Tampe Linkedin.pdf",
        "profile_pdf": "Maja_Tampe_Profile.pdf",
    },
}


SYNERGY_RULES: List[Dict[str, Any]] = [
    {
        "name": "Full Stack",
        "celebrities": ["Elon Musk"],
        "professors": ["Oriol Rius"],
        "bonus_stats": {"tech": 3, "ops": 3},
        "synergy_bonus": 0.05,
    },
    {
        "name": "AI Frontier",
        "celebrities": ["Elon Musk"],
        "professors": ["Jose A. Rodriguez-Serrano"],
        "bonus_stats": {"tech": 3, "innovation": 3},
        "synergy_bonus": 0.05,
    },
    {
        "name": "Deep Research",
        "celebrities": ["Albert Einstein"],
        "professors": ["Jordi Nin"],
        "bonus_stats": {"innovation": 4, "tech": 2},
        "synergy_bonus": 0.05,
    },
    {
        "name": "Quant Finance",
        "celebrities": ["Warren Buffett"],
        "professors": ["Ruben Coca"],
        "bonus_stats": {"finance": 4, "ops": 2},
        "synergy_bonus": 0.05,
    },
    {
        "name": "Data Empire",
        "celebrities": ["Jeff Bezos"],
        "professors": ["Ruben Coca"],
        "bonus_stats": {"ops": 3, "finance": 3},
        "synergy_bonus": 0.05,
    },
    {
        "name": "Responsible Scale",
        "celebrities": ["Jeff Bezos"],
        "professors": ["Maja Tampe"],
        "bonus_stats": {"brand": 2, "ops": 2, "finance": 2},
        "synergy_bonus": 0.05,
    },
    {
        "name": "Cult of Impact",
        "celebrities": ["Taylor Swift"],
        "professors": ["Maja Tampe"],
        "bonus_stats": {"brand": 3, "growth": 2},
        "synergy_bonus": 0.05,
    },
    {
        "name": "Product x Innovation",
        "celebrities": ["Steve Jobs"],
        "professors": ["Esteve Almirall"],
        "bonus_stats": {"product": 3, "innovation": 3},
        "synergy_bonus": 0.05,
    },
    {
        "name": "Innovation Lab",
        "celebrities": ["Elon Musk", "Albert Einstein", "Steve Jobs"],
        "professors": ["Esteve Almirall"],
        "bonus_stats": {"innovation": 3, "product": 2},
        "synergy_bonus": 0.04,
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


def get_celebrity_partners() -> List[Dict[str, Any]]:
    return CELEBRITY_PARTNERS


def get_professor_partners() -> List[Dict[str, Any]]:
    partners: List[Dict[str, Any]] = []
    for professor in PROFESSOR_PARTNERS:
        files = FACULTY_FILE_MATCHES.get(professor["name"], {})
        linkedin_pdf = files.get("linkedin_pdf")
        profile_pdf = files.get("profile_pdf")
        partners.append(
            {
                **professor,
                "source_files": {
                    "linkedin_pdf": linkedin_pdf,
                    "profile_pdf": profile_pdf,
                    "linkedin_path": str(FACULTY_PDF_DIR / linkedin_pdf) if linkedin_pdf else None,
                    "profile_path": str(FACULTY_PDF_DIR / profile_pdf) if profile_pdf else None,
                },
            }
        )
    return partners


def _find_by_name(options: List[Dict[str, Any]], name: str) -> Optional[Dict[str, Any]]:
    normalized = (name or "").strip().lower()
    if not normalized:
        return None
    for option in options:
        if option["name"].lower() == normalized:
            return option
    return None


def get_celebrity_by_name(name: str) -> Optional[Dict[str, Any]]:
    return _find_by_name(CELEBRITY_PARTNERS, name)


def get_professor_by_name(name: str) -> Optional[Dict[str, Any]]:
    return _find_by_name(PROFESSOR_PARTNERS, name)


def _sum_stats(*players: Dict[str, Any]) -> Dict[str, int]:
    result: Dict[str, int] = {key: 0 for key in STAT_KEYS}
    for player in players:
        stats = player.get("stats", {}) if player else {}
        for key in STAT_KEYS:
            result[key] += int(stats.get(key, 0))
    return result


def _apply_synergy_rules(celebrity_name: str, professor_name: str, base_stats: Dict[str, int]) -> Dict[str, Any]:
    total_bonus = {key: 0 for key in STAT_KEYS}
    unlocked_rules: List[str] = []
    synergy_bonus = 0.0

    for rule in SYNERGY_RULES:
        if celebrity_name in rule["celebrities"] and professor_name in rule["professors"]:
            unlocked_rules.append(rule["name"])
            synergy_bonus += float(rule.get("synergy_bonus", 0.0))
            for key, value in rule.get("bonus_stats", {}).items():
                if key in total_bonus:
                    total_bonus[key] += int(value)

    final_stats = {key: base_stats.get(key, 0) + total_bonus.get(key, 0) for key in STAT_KEYS}
    return {
        "unlocked_rules": unlocked_rules,
        "bonus_stats": total_bonus,
        "final_stats": final_stats,
        "synergy_bonus": synergy_bonus,
    }


def evaluate_partner_team(celebrity_name: str, professor_name: str) -> Dict[str, Any]:
    celebrity = get_celebrity_by_name(celebrity_name) or CELEBRITY_PARTNERS[0]
    professor = get_professor_by_name(professor_name) or PROFESSOR_PARTNERS[0]

    base_stats = _sum_stats(celebrity, professor)
    synergy = _apply_synergy_rules(celebrity["name"], professor["name"], base_stats)
    final_stats = synergy["final_stats"]

    budget_multiplier = 1.0 + ((final_stats["finance"] + final_stats["ops"]) / 400.0) + (synergy["synergy_bonus"] * 0.35)
    burn_multiplier = 1.0 + ((final_stats["growth"] + final_stats["innovation"]) / 700.0) - ((final_stats["ops"] + final_stats["finance"]) / 950.0)
    revenue_multiplier = 1.0 + ((final_stats["growth"] + final_stats["brand"] + final_stats["product"]) / 500.0) + (synergy["synergy_bonus"] * 0.2)

    burn_multiplier = max(0.85, min(1.25, burn_multiplier))

    combined_synergy_bonus = min(0.30, 0.08 + synergy["synergy_bonus"])
    team_name = f"{celebrity['name']} + {professor['name']}"

    return {
        "name": team_name,
        "celebrity": celebrity,
        "professor": professor,
        "base_stats": base_stats,
        "bonus_stats": synergy["bonus_stats"],
        "final_stats": final_stats,
        "unlocked_synergies": synergy["unlocked_rules"],
        "budget_multiplier": round(budget_multiplier, 3),
        "burn_multiplier": round(burn_multiplier, 3),
        "revenue_multiplier": round(revenue_multiplier, 3),
        "synergy_bonus": round(combined_synergy_bonus, 3),
        "style": f"{celebrity.get('domain', 'General')} x {professor.get('domain', 'General')}",
        "description": (
            f"{celebrity['name']} ({celebrity.get('core_ability', '')}) paired with "
            f"{professor['name']} ({professor.get('core_ability', '')})."
        ),
    }


def get_partner_options() -> List[Dict[str, Any]]:
    # Backward compatibility for old UI route.
    return [
        {
            "name": f"{c['name']} + {p['name']}",
            "style": f"{c.get('domain', 'General')} x {p.get('domain', 'General')}",
            "description": f"{c['core_ability']} + {p['core_ability']}",
            "budget_multiplier": 1.0,
            "burn_multiplier": 1.0,
            "synergy_bonus": 0.1,
        }
        for c in CELEBRITY_PARTNERS[:3]
        for p in PROFESSOR_PARTNERS[:2]
    ]


def get_classmate_by_name(name: str) -> Optional[Dict[str, str]]:
    if not name:
        return None
    for classmate in get_classmates():
        if classmate["name"].lower() == name.lower():
            return classmate
    return None


def get_partner_by_name(name: str) -> Optional[Dict[str, Any]]:
    # Backward compatibility helper for old single-partner flows.
    legacy = _find_by_name(get_partner_options(), name)
    return legacy
