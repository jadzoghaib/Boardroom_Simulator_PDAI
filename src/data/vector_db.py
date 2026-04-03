import os
import logging
from typing import Dict, List, Optional
from urllib.parse import urlparse

import chromadb
import wikipediaapi

from src.data.founder_roster import CELEBRITY_PARTNERS, PROFESSOR_PARTNERS, FACULTY_FILE_MATCHES, FACULTY_PDF_DIR

logger = logging.getLogger(__name__)

DB_PATH = os.path.join(os.path.dirname(__file__), "chroma_db")

PLAYBOOK_COLLECTION = "startup_playbooks"
CELEBRITY_COLLECTION = "celebrity_backgrounds"
PROFESSOR_COLLECTION = "professor_backgrounds"


def _get_client() -> chromadb.PersistentClient:
    return chromadb.PersistentClient(path=DB_PATH)


def _chunk_text(text: str, chunk_size: int = 900) -> List[str]:
    text = (text or "").strip()
    if not text:
        return []
    chunks: List[str] = []
    start = 0
    while start < len(text):
        end = min(len(text), start + chunk_size)
        chunks.append(text[start:end].strip())
        start = end
    return [chunk for chunk in chunks if chunk]


def _wiki_title_from_url(url: str) -> str:
    path = urlparse(url).path.strip("/")
    if path.startswith("wiki/"):
        path = path[len("wiki/") :]
    return path.replace("_", " ").strip()

def build_mentor_kb():
    """Builds a local vector database of startup playbooks for the Mentor Agent."""
    client = _get_client()
    collection = client.get_or_create_collection(name=PLAYBOOK_COLLECTION)
    
    playbooks = [
        {"id": "doc_1", "text": "If burn rate is too high relative to revenue, cut marketing spend immediately and focus on organic growth channels to extend runway."},
        {"id": "doc_2", "text": "For high-experience founders in SaaS, finding a strategic corporate partner is often better and faster than securing traditional VC funding."},
        {"id": "doc_3", "text": "A cash runway of less than 6 months requires an emergency bridge round or an aggressive product pivot towards short-term revenue."},
        {"id": "doc_4", "text": "In the Fintech sector, compliance costs inflate burn rate early. Counter VC skepticism by highlighting regulatory moats as a competitive advantage."}
    ]
    
    if collection.count() == 0:
        texts = [item["text"] for item in playbooks]
        ids = [item["id"] for item in playbooks]
        collection.add(documents=texts, ids=ids)
    
    return collection

def search_playbook(query: str, n_results: int = 1) -> str:
    """Searches the ChromaDB vector store for relevant business advice."""
    client = _get_client()
    collection = client.get_or_create_collection(name=PLAYBOOK_COLLECTION)
    
    results = collection.query(query_texts=[query], n_results=n_results)
    if results and results['documents'] and len(results['documents'][0]) > 0:
        return results['documents'][0][0]
    return "No specific playbook strategy found."


def build_celebrity_kb(force_refresh: bool = False) -> None:
    """Builds a celebrity background vector collection from Wikipedia pages."""
    client = _get_client()
    collection = client.get_or_create_collection(name=CELEBRITY_COLLECTION)

    if not force_refresh and collection.count() > 0:
        return

    if force_refresh and collection.count() > 0:
        existing = collection.get(include=[])
        ids = existing.get("ids", []) if existing else []
        if ids:
            collection.delete(ids=ids)

    wiki = wikipediaapi.Wikipedia(
        language="en",
        user_agent="boardroom-sim/1.0 (celebrity-rag-ingestion)",
    )

    docs: List[str] = []
    ids: List[str] = []
    metadatas: List[Dict[str, str]] = []

    for celeb in CELEBRITY_PARTNERS:
        celeb_name = celeb["name"]
        wiki_url = celeb.get("wikipedia_url", "")
        title = _wiki_title_from_url(wiki_url) or celeb_name

        page = wiki.page(title)
        text = page.text if page.exists() else ""
        fallback = celeb.get("description", "")
        source_text = text.strip() or fallback

        if not source_text:
            continue

        for idx, chunk in enumerate(_chunk_text(source_text)):
            chunk_id = f"celeb_{celeb_name.lower().replace(' ', '_')}_{idx}"
            docs.append(chunk)
            ids.append(chunk_id)
            metadatas.append(
                {
                    "name": celeb_name,
                    "domain": celeb.get("domain", ""),
                    "core_ability": celeb.get("core_ability", ""),
                    "wikipedia_url": wiki_url,
                }
            )

    if docs:
        collection.add(documents=docs, ids=ids, metadatas=metadatas)


def search_celebrity_background(query: str, celebrity_name: Optional[str] = None, n_results: int = 2) -> str:
    """Searches vectorized celebrity background knowledge built from Wikipedia."""
    build_celebrity_kb()

    client = _get_client()
    collection = client.get_or_create_collection(name=CELEBRITY_COLLECTION)

    where = {"name": celebrity_name} if celebrity_name else None
    query_text = query or "background, achievements, and strategic strengths"

    results = collection.query(query_texts=[query_text], n_results=n_results, where=where)
    docs = results.get("documents", [[]])[0] if results else []
    metas = results.get("metadatas", [[]])[0] if results else []

    if not docs:
        if celebrity_name:
            return f"No stored background found for {celebrity_name}."
        return "No celebrity background found."

    snippets: List[str] = []
    for i, doc in enumerate(docs):
        meta = metas[i] if i < len(metas) else {}
        name = meta.get("name", "Unknown")
        snippets.append(f"[{name}] {doc}")

    return "\n\n".join(snippets)

def _extract_pdf_text(pdf_path: str) -> str:
    """Extract text from a PDF using pdfplumber."""
    try:
        import pdfplumber
    except ImportError:
        logger.warning("pdfplumber not installed. Run: pip install pdfplumber")
        return ""

    text_parts = []
    try:
        with pdfplumber.open(pdf_path) as pdf:
            for page in pdf.pages:
                page_text = page.extract_text()
                if page_text:
                    text_parts.append(page_text.strip())
    except Exception as e:
        logger.warning(f"Failed to read PDF {pdf_path}: {e}")
        return ""

    return "\n\n".join(text_parts)


def build_professor_kb(force_refresh: bool = False) -> None:
    """
    Build a professor background vector collection from PDF files.
    Reads both LinkedIn PDFs and generated Profile PDFs from data/ESADE Faculty/.
    """
    client = _get_client()
    collection = client.get_or_create_collection(name=PROFESSOR_COLLECTION)

    if not force_refresh and collection.count() > 0:
        return

    if force_refresh and collection.count() > 0:
        existing = collection.get(include=[])
        ids = existing.get("ids", []) if existing else []
        if ids:
            collection.delete(ids=ids)

    docs: List[str] = []
    ids: List[str] = []
    metadatas: List[Dict[str, str]] = []

    for professor in PROFESSOR_PARTNERS:
        prof_name = professor["name"]
        files = FACULTY_FILE_MATCHES.get(prof_name, {})

        # Collect text from all available PDFs
        all_text = []

        for file_key in ("linkedin_pdf", "profile_pdf"):
            filename = files.get(file_key)
            if not filename:
                continue
            pdf_path = str(FACULTY_PDF_DIR / filename)
            if os.path.exists(pdf_path):
                text = _extract_pdf_text(pdf_path)
                if text:
                    all_text.append(text)
            else:
                logger.info(f"PDF not found: {pdf_path}")

        # Also add the description from founder_roster as a fallback
        fallback = professor.get("description", "")
        source_text = "\n\n".join(all_text) if all_text else fallback

        if not source_text:
            continue

        for idx, chunk in enumerate(_chunk_text(source_text)):
            chunk_id = f"prof_{prof_name.lower().replace(' ', '_').replace('.', '')}_{idx}"
            docs.append(chunk)
            ids.append(chunk_id)
            metadatas.append({
                "name": prof_name,
                "domain": professor.get("domain", ""),
                "core_ability": professor.get("core_ability", ""),
            })

    if docs:
        collection.add(documents=docs, ids=ids, metadatas=metadatas)
        logger.info(f"Professor KB built: {len(docs)} chunks from {len(PROFESSOR_PARTNERS)} professors")


def search_professor_background(query: str, professor_name: Optional[str] = None, n_results: int = 2) -> str:
    """Search vectorized professor background knowledge built from PDFs."""
    build_professor_kb()

    client = _get_client()
    collection = client.get_or_create_collection(name=PROFESSOR_COLLECTION)

    where = {"name": professor_name} if professor_name else None
    query_text = query or "background, expertise, research, and teaching focus"

    results = collection.query(query_texts=[query_text], n_results=n_results, where=where)
    docs = results.get("documents", [[]])[0] if results else []
    metas = results.get("metadatas", [[]])[0] if results else []

    if not docs:
        if professor_name:
            return f"No stored background found for Professor {professor_name}."
        return "No professor background found."

    snippets: List[str] = []
    for i, doc in enumerate(docs):
        meta = metas[i] if i < len(metas) else {}
        name = meta.get("name", "Unknown")
        snippets.append(f"[Prof. {name}] {doc}")

    return "\n\n".join(snippets)


if __name__ == "__main__":
    build_mentor_kb()
    build_celebrity_kb()
    build_professor_kb()
    print("Vector database populated successfully (playbooks + celebrities + professors).")
