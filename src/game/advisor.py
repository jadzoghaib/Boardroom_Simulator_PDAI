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


def _founder_info(state) -> tuple[str, str, str]:
    """Return (founder_name, founder_background_label, founder_experience_str)."""
    name = state.classmate.get("name", "the founder")
    first_name = name.split()[0] if name else "the founder"
    bg_map = {0: "first-time entrepreneur", 1: "business background", 2: "technical background"}
    bg = bg_map.get(state.founder_background, "first-time entrepreneur") if isinstance(state.founder_background, int) else str(state.founder_background)
    exp = f"{state.founder_experience} years"
    return first_name, bg, exp


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

    founder_name, founder_bg, founder_exp = _founder_info(state)
    professor_system = PROFESSOR_ADVISOR_PROMPT.format(
        professor_name=professor_name,
        professor_domain=state.professor.get("domain", "General"),
        professor_core_ability=state.professor.get("core_ability", ""),
        professor_description=state.professor.get("description", ""),
        professor_rag_context=professor_rag or "No additional background available.",
        founder_name=founder_name,
        founder_background=founder_bg,
        founder_experience=founder_exp,
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


def get_celebrity_response(state, user_message: str) -> str:
    """
    Get a response from the Celebrity advisor only.
    Used by the /chat/celebrity endpoint.
    """
    llm = _get_llm()
    cond = MARKET_CONDITIONS.get(state.market_condition, {})
    market_label = cond.get("label", "Stable")
    event_context = _build_event_context(state)

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

    history = _build_chat_history(state)
    try:
        messages = [
            SystemMessage(content=celebrity_system),
            *history,
            HumanMessage(content=user_message),
        ]
        result = llm.invoke(messages)
        return getattr(result, "content", "").strip()
    except Exception as e:
        logger.error(f"Celebrity LLM call failed: {e}")
        return f"[{celebrity_name}]: Sorry, I'm having trouble connecting right now. Go with your gut on this one."


def get_professor_response(state, user_message: str) -> str:
    """
    Get a response from the Professor advisor only.
    Used by the /chat/professor endpoint.
    """
    llm = _get_llm()
    cond = MARKET_CONDITIONS.get(state.market_condition, {})
    market_label = cond.get("label", "Stable")
    event_context = _build_event_context(state)

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

    founder_name, founder_bg, founder_exp = _founder_info(state)
    professor_system = PROFESSOR_ADVISOR_PROMPT.format(
        professor_name=professor_name,
        professor_domain=state.professor.get("domain", "General"),
        professor_core_ability=state.professor.get("core_ability", ""),
        professor_description=state.professor.get("description", ""),
        professor_rag_context=professor_rag or "No additional background available.",
        founder_name=founder_name,
        founder_background=founder_bg,
        founder_experience=founder_exp,
        quarter=state.current_quarter,
        sector=state.sector,
        cash=state.cash,
        burn_rate=state.burn_rate,
        revenue=state.revenue,
        runway_months=state.runway_months,
        market_condition=market_label,
        event_context=event_context,
    )

    history = _build_chat_history(state)
    try:
        messages = [
            SystemMessage(content=professor_system),
            *history,
            HumanMessage(content=user_message),
        ]
        result = llm.invoke(messages)
        return getattr(result, "content", "").strip()
    except Exception as e:
        logger.error(f"Professor LLM call failed: {e}")
        return f"[Prof. {professor_name}]: I apologize, but I'm unable to provide analysis at the moment. Consider the risk-adjusted options carefully."


# ═══════════════════════════════════════════════════════════════════
# END-OF-GAME DEBRIEF
# ═══════════════════════════════════════════════════════════════════

def get_game_debrief(state) -> str:
    """Generate a detailed post-game debrief using the full game history."""
    llm = _get_llm()

    from src.agents.prompts import DEBRIEF_PROMPT

    # Build full game history
    quarter_history = ""
    for i, q in enumerate(state.quarter_log or [], 1):
        if isinstance(q, dict):
            quarter_history += (
                f"\nQ{i}: Cash ${q.get('cash_end', 0):,.0f} | "
                f"Revenue ${q.get('revenue', 0):,.0f}/mo | "
                f"Burn ${q.get('burn_rate', 0):,.0f}/mo | "
                f"Market: {q.get('market_condition', '?')}\n"
            )
        else:
            quarter_history += (
                f"\nQ{i}: Cash ${getattr(q, 'cash_end', 0):,.0f} | "
                f"Revenue ${getattr(q, 'revenue', 0):,.0f}/mo | "
                f"Burn ${getattr(q, 'burn_rate', 0):,.0f}/mo | "
                f"Market: {getattr(q, 'market_condition', '?')}\n"
            )

    resolved = state.resolved_event_ids or []
    event_summary = f"{len(resolved)} events resolved across all quarters."

    user_content = f"""
Founder: {state.classmate.get('name', 'Unknown')}
Sector: {state.sector}
Celebrity Advisor: {state.celebrity.get('name', '?')}
Professor Advisor: {state.professor.get('name', '?')}

FINAL FINANCIALS:
- Cash: ${state.cash:,.0f}
- Burn Rate: ${state.burn_rate:,.0f}/mo
- Revenue: ${state.revenue:,.0f}/mo
- Runway: {state.runway_months:.1f} months
- Valuation: ${state.valuation:,.0f}
- Funding Stage: {state.funding_stage}
- Equity Given: {state.equity_given:.1f}%

GAME OUTCOME:
- Quarters Completed: {state.current_quarter}/8
- Game Over Reason: {state.game_over_reason or 'Completed all 8 quarters'}
- Milestones Completed: {state.milestones_completed}/3
- Success Probability (ML): {state.success_probability:.0%}

FINAL STATS:
{chr(10).join(f'- {k.title()}: {v}/100' for k, v in state.stats.items())}

STAFF HIRED:
{chr(10).join(f'- {s.name} ({s.role})' for s in state.staff) or '- No executives hired'}

QUARTER-BY-QUARTER:
{quarter_history or 'No quarter log available.'}

EVENTS: {event_summary}

RIVALS AT END:
{chr(10).join(f'- {r.name} : {r.score} pts ({r.momentum})' for r in state.rivals)}
"""

    try:
        result = llm.invoke([
            SystemMessage(content=DEBRIEF_PROMPT),
            HumanMessage(content=user_content)
        ])
        return getattr(result, "content", "").strip()
    except Exception as e:
        logger.error(f"Debrief LLM call failed: {e}")
        return "Unable to generate debrief at this time."


# ═══════════════════════════════════════════════════════════════════
# BOARDROOM VC CHAT
# ═══════════════════════════════════════════════════════════════════

def get_vc_opening(state) -> str:
    """Generate the VC's opening statement for the board review."""
    llm = _get_llm()
    from src.agents.prompts import VC_BOARDROOM_PROMPT

    rivals_summary = "\n".join(
        f"- {r.name}: {r.score} pts ({r.momentum})"
        for r in state.rivals[:3]
    )
    stats_summary = ", ".join(f"{k}: {v}" for k, v in state.stats.items())

    system = VC_BOARDROOM_PROMPT.format(
        quarter=state.current_quarter,
        sector=state.sector,
        cash=state.cash,
        burn_rate=state.burn_rate,
        revenue=state.revenue,
        runway_months=state.runway_months,
        valuation=state.valuation,
        funding_stage=state.funding_stage,
        milestones_completed=state.milestones_completed,
        success_probability=state.success_probability,
        rivals_summary=rivals_summary or "No rivals tracked.",
        stats_summary=stats_summary or "No stats yet.",
    )

    opening_prompt = (
        f"This is the start of the board review for Q{state.current_quarter}. "
        "Give your opening assessment of this startup in 3-4 sentences. "
        "Be direct about what concerns you and what you want to discuss. Do not give a verdict yet."
    )

    try:
        result = llm.invoke([
            SystemMessage(content=system),
            HumanMessage(content=opening_prompt)
        ])
        return getattr(result, "content", "").strip()
    except Exception as e:
        logger.error(f"VC opening failed: {e}")
        return "Let's cut to the chase. Your burn rate concerns me. Walk me through your plan to reach profitability."


def get_vc_response(state, user_message: str):
    """
    Get VC and partner response to founder's message during board review.
    Returns (vc_response, partner_response, verdict_or_none)
    """
    import re as _re
    llm = _get_llm()
    from src.agents.prompts import VC_BOARDROOM_PROMPT, PARTNER_BOARDROOM_PROMPT

    rivals_summary = "\n".join(
        f"- {r.name}: {r.score} pts ({r.momentum})"
        for r in state.rivals[:3]
    )
    stats_summary = ", ".join(f"{k}: {v}" for k, v in state.stats.items())

    vc_system = VC_BOARDROOM_PROMPT.format(
        quarter=state.current_quarter,
        sector=state.sector,
        cash=state.cash,
        burn_rate=state.burn_rate,
        revenue=state.revenue,
        runway_months=state.runway_months,
        valuation=state.valuation,
        funding_stage=state.funding_stage,
        milestones_completed=state.milestones_completed,
        success_probability=state.success_probability,
        rivals_summary=rivals_summary or "No rivals tracked.",
        stats_summary=stats_summary or "No stats yet.",
    )

    bg_map = {0: "first-time founder", 1: "business background", 2: "technical background"}
    founder_bg_type = bg_map.get(state.founder_background, state.founder_background) if isinstance(state.founder_background, int) else state.founder_background
    founder_background = (
        f"- Name: {state.classmate.get('name', 'Unknown')}\n"
        f"- Background: {founder_bg_type}\n"
        f"- Years of experience: {state.founder_experience}\n"
        f"- Country: {state.classmate.get('country', 'Unknown')}\n"
        f"- Sector interests: {state.classmate.get('sector_tags', 'Not specified')}"
    )

    partner_system = PARTNER_BOARDROOM_PROMPT.format(
        partner_name=state.professor.get("name", "Professor"),
        quarter=state.current_quarter,
        sector=state.sector,
        cash=state.cash,
        burn_rate=state.burn_rate,
        revenue=state.revenue,
        runway_months=state.runway_months,
        valuation=state.valuation,
        funding_stage=state.funding_stage,
        milestones_completed=state.milestones_completed,
        success_probability=state.success_probability,
        stats_summary=stats_summary or "No stats yet.",
        founder_background=founder_background,
    )

    # Build history from board_chat_messages
    history = []
    for msg in state.board_chat_messages[-8:]:
        if msg.role == "user":
            history.append(HumanMessage(content=f"[Founder]: {msg.content}"))
        elif msg.role == "vc":
            history.append(HumanMessage(content=f"[VC]: {msg.content}"))
        elif msg.role == "partner":
            partner_name = state.professor.get("name", "Professor")
            history.append(HumanMessage(content=f"[{partner_name}]: {msg.content}"))

    # Determine if this should be the final exchange (after 3+ founder messages)
    founder_msgs = sum(1 for m in state.board_chat_messages if m.role == "user")
    is_final = founder_msgs >= 3

    final_instruction = (
        "\nThis is the final exchange. Give your verdict now. "
        "End your response with [VERDICT: IMPRESSED], [VERDICT: NEUTRAL], or [VERDICT: CONCERNED] on its own line."
        if is_final else ""
    )

    # VC response
    vc_response = ""
    try:
        vc_msgs = [
            SystemMessage(content=vc_system + final_instruction),
            *history,
            HumanMessage(content=user_message),
        ]
        result = llm.invoke(vc_msgs)
        vc_response = getattr(result, "content", "").strip()
    except Exception as e:
        logger.error(f"VC response failed: {e}")
        vc_response = "Interesting point. But I need to see better numbers before I'm convinced."

    # Extract verdict if present
    verdict = None
    verdict_match = _re.search(r'\[VERDICT:\s*(IMPRESSED|NEUTRAL|CONCERNED)\]', vc_response)
    if verdict_match:
        verdict = verdict_match.group(1)
        vc_response = vc_response[:verdict_match.start()].strip()

    # Partner response
    partner_response = ""
    partner_name = state.professor.get("name", "Professor")
    try:
        partner_context = (
            f"The founder said: '{user_message[:300]}'. "
            f"The VC responded: '{vc_response[:300]}'. "
            "Give your independent assessment. You may agree or disagree with the VC. "
            "End with a direct question to the founder."
        )
        prof_msgs = [
            SystemMessage(content=partner_system),
            *history,
            HumanMessage(content=partner_context),
        ]
        result = llm.invoke(prof_msgs)
        partner_response = getattr(result, "content", "").strip()
    except Exception as e:
        logger.error(f"Partner board response failed: {e}")
        partner_response = "I agree with the VC's assessment. The data speaks for itself."

    return vc_response, partner_response, verdict
