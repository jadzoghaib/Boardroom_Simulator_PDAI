"""
Advisory chat system for the 8-quarter startup simulation.

Provides LLM-powered responses from Celebrity + Professor advisors.
Uses direct Groq calls (not LangGraph) for speed in multi-turn chat.
Pulls RAG context from ChromaDB for both celebrity and professor.
"""

from __future__ import annotations

import os
import logging
from typing import Any, Dict, List, Tuple

from langchain_core.messages import HumanMessage, SystemMessage
from langchain_groq import ChatGroq

from src.agents.prompts import CELEBRITY_ADVISOR_PROMPT, PROFESSOR_ADVISOR_PROMPT
from src.data.vector_db import search_celebrity_background, search_professor_background
from src.data.market import MARKET_CONDITIONS

logger = logging.getLogger(__name__)


def _get_llm() -> ChatGroq:
    """Get a Groq LLM instance for advisory chat."""
    api_key = os.getenv("GROQ_API_KEY", "").strip()
    if not api_key:
        raise RuntimeError("GROQ_API_KEY is not set.")
    return ChatGroq(model="llama-3.3-70b-versatile", temperature=0.7, api_key=api_key)


def _build_event_context(state) -> str:
    """Build a text description of the current pending event for advisor context."""
    if state.pending_event:
        ev = state.pending_event
        choices_text = "\n".join(
            f"  Option {i+1}: {c.text} (costs {c.ap_cost} AP)"
            for i, c in enumerate(ev.choices)
        )
        return f"Event: {ev.title}\n{ev.description}\n\nChoices:\n{choices_text}"
    elif state.current_events:
        ev = state.current_events[0]
        choices_text = "\n".join(
            f"  Option {i+1}: {c.text} (costs {c.ap_cost} AP)"
            for i, c in enumerate(ev.choices)
        )
        return f"Event: {ev.title}\n{ev.description}\n\nChoices:\n{choices_text}"
    else:
        return "No specific event is pending. The founder is asking for general strategic advice."


def _build_chat_history(state, max_messages: int = 6) -> List:
    """Build recent chat history as LangChain messages for context."""
    recent = state.chat_messages[-max_messages:] if state.chat_messages else []
    messages = []
    for msg in recent:
        if msg.role == "user":
            messages.append(HumanMessage(content=f"[Founder]: {msg.content}"))
        else:
            messages.append(HumanMessage(content=f"[{msg.speaker}]: {msg.content}"))
    return messages


def get_advisor_responses(
    state,
    user_message: str,
) -> Tuple[str, str]:
    """
    Get responses from both Celebrity and Professor advisors.

    Args:
        state: GameState instance
        user_message: The founder's question/message

    Returns:
        Tuple of (celebrity_response, professor_response)
    """
    llm = _get_llm()

    # Get market condition label
    cond = MARKET_CONDITIONS.get(state.market_condition, {})
    market_label = cond.get("label", "Stable")

    # Build event context
    event_context = _build_event_context(state)

    # ── Celebrity advisor ──
    celebrity_name = state.celebrity.get("name", "Celebrity Advisor")
    celebrity_rag = ""
    try:
        celebrity_rag = search_celebrity_background(
            query=f"{event_context} {user_message}",
            celebrity_name=celebrity_name,
            n_results=2,
        )
    except Exception as e:
        logger.warning(f"Celebrity RAG failed: {e}")

    celebrity_system = CELEBRITY_ADVISOR_PROMPT.format(
        celebrity_name=celebrity_name,
        celebrity_domain=state.celebrity.get("domain", "General"),
        celebrity_core_ability=state.celebrity.get("core_ability", ""),
        celebrity_description=state.celebrity.get("description", ""),
        celebrity_rag_context=celebrity_rag or "No additional background available.",
        quarter=state.current_quarter,
        sector=state.sector,
        cash=state.cash,
        burn_rate=state.burn_rate,
        revenue=state.revenue,
        runway_months=state.runway_months,
        market_condition=market_label,
        event_context=event_context,
    )

    # ── Professor advisor ──
    professor_name = state.professor.get("name", "Professor Advisor")
    professor_rag = ""
    try:
        professor_rag = search_professor_background(
            query=f"{event_context} {user_message}",
            professor_name=professor_name,
            n_results=2,
        )
    except Exception as e:
        logger.warning(f"Professor RAG failed: {e}")

    professor_system = PROFESSOR_ADVISOR_PROMPT.format(
        professor_name=professor_name,
        professor_domain=state.professor.get("domain", "General"),
        professor_core_ability=state.professor.get("core_ability", ""),
        professor_description=state.professor.get("description", ""),
        professor_rag_context=professor_rag or "No additional background available.",
        quarter=state.current_quarter,
        sector=state.sector,
        cash=state.cash,
        burn_rate=state.burn_rate,
        revenue=state.revenue,
        runway_months=state.runway_months,
        market_condition=market_label,
        event_context=event_context,
    )

    # Build chat history for context
    history = _build_chat_history(state)

    # ── Call LLM for celebrity ──
    celebrity_response = ""
    try:
        celeb_messages = [
            SystemMessage(content=celebrity_system),
            *history,
            HumanMessage(content=user_message),
        ]
        celeb_result = llm.invoke(celeb_messages)
        celebrity_response = getattr(celeb_result, "content", "").strip()
    except Exception as e:
        logger.error(f"Celebrity LLM call failed: {e}")
        celebrity_response = f"[{celebrity_name}]: *adjusts microphone* Sorry, I'm having trouble connecting right now. Go with your gut on this one."

    # ── Call LLM for professor ──
    professor_response = ""
    try:
        prof_messages = [
            SystemMessage(content=professor_system),
            *history,
            HumanMessage(content=user_message),
        ]
        prof_result = llm.invoke(prof_messages)
        professor_response = getattr(prof_result, "content", "").strip()
    except Exception as e:
        logger.error(f"Professor LLM call failed: {e}")
        professor_response = f"[Prof. {professor_name}]: I apologize, but I'm unable to provide analysis at the moment. Consider the risk-adjusted options carefully."

    return celebrity_response, professor_response
