from functools import lru_cache
from pathlib import Path
from typing import Any, Dict, List, Optional

import pandas as pd


DATA_PATH = Path(__file__).resolve().parents[2] / "cost_of_living.csv"


@lru_cache(maxsize=1)
def _latest_rows() -> pd.DataFrame:
    if not DATA_PATH.exists():
        return pd.DataFrame()

    df = pd.read_csv(DATA_PATH)
    if "country" not in df.columns or "year" not in df.columns:
        return pd.DataFrame()

    df = df.copy()
    df["year"] = pd.to_numeric(df["year"], errors="coerce").fillna(0).astype(int)
    latest = df.sort_values(["country", "year"]).groupby("country", as_index=False).tail(1)
    return latest


def get_country_list() -> List[str]:
    latest = _latest_rows()
    if latest.empty:
        return []
    return sorted(latest["country"].dropna().astype(str).unique().tolist())


def get_country_profile(country: str) -> Optional[Dict[str, Any]]:
    latest = _latest_rows()
    if latest.empty or not country:
        return None

    match = latest[latest["country"].astype(str).str.lower() == country.lower()]
    if match.empty:
        return None

    row = match.iloc[0]
    return {
        "country": str(row.get("country", "")),
        "year": int(row.get("year", 0) or 0),
        "continent": str(row.get("continent", "")),
        "cost_of_living_index": float(row.get("cost_of_living_index", 60.0) or 60.0),
        "rent_index": float(row.get("rent_index", 50.0) or 50.0),
        "local_purchasing_power_index": float(row.get("local_purchasing_power_index", 100.0) or 100.0),
    }