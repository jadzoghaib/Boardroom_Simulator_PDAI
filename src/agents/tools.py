from langchain_core.tools import tool
from src.ml.predictor import MarketPredictor
from src.data.vector_db import search_playbook, search_celebrity_background, search_professor_background

predictor = MarketPredictor()

@tool
def check_survival_probability(budget: float, burn_rate: float, revenue: float, founder_experience: int, sector: str) -> str:
    """Uses the custom ML model to predict the startup's chance of success and runway."""
    prob = predictor.predict_success_probability(burn_rate, revenue, founder_experience, sector)
    runway = predictor.calculate_runway(budget, burn_rate, revenue)

    variance = "high" if runway < 12 else "low"
    chance = prob * 100

    return f"The ML model predicts a {chance:.1f}% chance of success. Your runway is {runway} months. Risk variance: {variance}."

@tool
def query_startup_playbook(query: str) -> str:
    """Searches the vector database for business frameworks and pivot strategies."""
    return search_playbook(query)


@tool
def query_celebrity_background(celebrity_name: str, query: str = "") -> str:
    """Searches Wikipedia-backed celebrity background knowledge for strategic context."""
    return search_celebrity_background(query=query, celebrity_name=celebrity_name)


@tool
def query_professor_background(professor_name: str, query: str = "") -> str:
    """Searches PDF-backed professor background knowledge for academic and strategic context."""
    return search_professor_background(query=query, professor_name=professor_name)
