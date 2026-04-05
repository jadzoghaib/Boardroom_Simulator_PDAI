"""
Reads each classmate LinkedIn PDF, extracts structured data via Groq,
and writes the result to data/classmates.csv.

Run with: uv run python -m src.data.populate_classmates
"""

import csv
import json
import os
import sys
import time
from pathlib import Path

import pdfplumber
from dotenv import load_dotenv
from langchain_groq import ChatGroq
from langchain_core.messages import HumanMessage, SystemMessage

load_dotenv()

PDF_DIR   = Path(__file__).resolve().parents[2] / "data" / "Classmates Linkedin"
CSV_PATH  = Path(__file__).resolve().parents[2] / "data" / "classmates.csv"

VALID_SECTORS = {"AI", "Fintech", "SaaS", "Healthtech", "E-commerce"}

# Map PDF filenames → CSV names
PDF_TO_CSV_NAME = {
    "Amat Montoto.pdf":              "Amat Montoto",
    "Ayush Raj.pdf":                 "Ayush Raj",
    "Brice Da Costa.pdf":            "Brice Da Costa",
    "David Puchala.pdf":             "David Puchala",
    "Ella Magdić.pdf":               "Ella Magdic",
    "Fabrizio Iacuzio.pdf":          "Fabrizio Iacuzio",
    "Florian Nix.pdf":               "Florian Nix",
    "Francesc Cañavate Quero.pdf":   "Francesc Canavate",
    "Francesco Polimeni.pdf":        "Francesco Polimeni",
    "Gabriela Méndez.pdf":           "Gabriela Mendez",
    "Giorgio Fiorentino.pdf":        "Giorgio Fiorentino",
    "Hiroaki Nakano.pdf":            "Hiroaki Nakano",
    "Jad Zoghaib.pdf":               "Jad Zoghaib",
    "Lara Işıkcı.pdf":               "Lara Isikci",
    "Lucas Haesaert.pdf":            "Lucas Haesaert",
    "Marc Sardà Masriera.pdf":       "Marc Sarda",
    "Maria París Ros.pdf":           "Maria Paris",
    "María Angélica Mora Zamora.pdf":"Maria Mora",
    "Matteo Guardamagna.pdf":        "Matteo Guardamagna",
    "Miguel de Faria.pdf":           "Miguel de Faria",
    "Omar Trabelsi.pdf":             "Omar Trabelsi",
    "Pornpisuth Pongtanya.pdf":      "eng pongtanya",
    "Sara Fibla Salgado.pdf":        "Sara Fibla",
    "Sean Hoet.pdf":                 "Sean",
    "Sharath Raveendran.pdf":        "Sharath Raveendran",
    "Yiben Fruncillo.pdf":           "Yiben Fruncillo",
}

SYSTEM_PROMPT = """You are extracting structured profile data from a LinkedIn PDF export.
Return ONLY valid JSON with exactly these fields:

{
  "years_experience": <integer 1-20, total professional work experience years>,
  "background": <"technical" | "business" | "first_time">,
  "sector_tags": <pipe-separated string from: AI, Fintech, SaaS, Healthtech, E-commerce — pick 1-3 that best match their industry experience, or empty string if none match>
}

Rules:
- background = "technical" if they have CS/engineering degree or developer/data/engineering roles
- background = "business" if they have MBA or business/consulting/finance/marketing/sales roles
- background = "first_time" if unclear or very early career
- sector_tags: only use the exact names AI, Fintech, SaaS, Healthtech, E-commerce
- years_experience: count only professional work experience (not education). Use current year 2026 as reference.
- Return ONLY the JSON object, no other text."""


def extract_pdf_text(pdf_path: Path) -> str:
    with pdfplumber.open(str(pdf_path)) as pdf:
        pages = [page.extract_text() or "" for page in pdf.pages]
    return "\n".join(pages)[:4000]  # cap to avoid token limits


def query_groq(text: str, llm: ChatGroq) -> dict:
    messages = [
        SystemMessage(content=SYSTEM_PROMPT),
        HumanMessage(content=f"LinkedIn profile text:\n\n{text}"),
    ]
    response = llm.invoke(messages)
    raw = response.content.strip()
    # Strip markdown code fences if present
    if raw.startswith("```"):
        raw = raw.split("```")[1]
        if raw.startswith("json"):
            raw = raw[4:]
    return json.loads(raw.strip())


def validate(data: dict) -> dict:
    years = int(data.get("years_experience", 3))
    years = max(1, min(20, years))

    bg = data.get("background", "first_time")
    if bg not in ("technical", "business", "first_time"):
        bg = "first_time"

    raw_tags = data.get("sector_tags", "")
    tags = [t.strip() for t in str(raw_tags).split("|") if t.strip() in VALID_SECTORS]
    sector_tags = "|".join(tags)

    return {"years_experience": years, "background": bg, "sector_tags": sector_tags}


def main():
    llm = ChatGroq(model="llama-3.3-70b-versatile", temperature=0)

    # Load existing CSV rows keyed by name
    existing: dict[str, dict] = {}
    if CSV_PATH.exists():
        with CSV_PATH.open("r", encoding="utf-8", newline="") as f:
            for row in csv.DictReader(f):
                existing[row["name"]] = row

    results = {}
    pdfs = sorted(PDF_DIR.glob("*.pdf"))

    for pdf_path in pdfs:
        csv_name = PDF_TO_CSV_NAME.get(pdf_path.name)
        if not csv_name:
            print(f"  [skip] No CSV mapping for {pdf_path.name}")
            continue

        print(f"Processing {pdf_path.name} -> {csv_name} ...", end=" ", flush=True)
        try:
            text = extract_pdf_text(pdf_path)
            data = query_groq(text, llm)
            data = validate(data)
            results[csv_name] = data
            print(f"✓  exp={data['years_experience']}y  bg={data['background']}  sectors={data['sector_tags'] or '—'}")
        except Exception as e:
            print(f"✗  ERROR: {e}")
            results[csv_name] = {"years_experience": 3, "background": "first_time", "sector_tags": ""}
        time.sleep(0.3)  # avoid rate limits

    # Merge results into existing rows and write CSV
    fieldnames = ["name", "linkedin_url", "notes", "country", "years_experience", "background", "sector_tags"]
    rows = []
    for name, row in existing.items():
        enriched = dict(row)
        if name in results:
            enriched.update(results[name])
        rows.append(enriched)

    with CSV_PATH.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

    print(f"\nDone. Updated {len(results)} classmates in {CSV_PATH}")


if __name__ == "__main__":
    main()
