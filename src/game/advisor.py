"""
Advisory chat system for the 8-quarter startup simulation.

Provides LLM-powered responses from Celebrity + Professor advisors.

BRANCH: aws-deployment
CHANGE: Replaced Groq API / langchain_groq with AWS SageMaker endpoint
        (Mistral-7B-Instruct-v0.2 via HuggingFace DLC).
        Removed all GROQ_API_KEY references.
        Uses boto3 sagemaker-runtime for endpoint invocation.
"""

from __future__ import annotations

import os
import json
import logging
import boto3
from typing import Tuple, List

from src.agents.prompts import (
    CELEBRITY_ADVISOR_PROMPT,
    PROFESSOR_ADVISOR_PROMPT,
    DEBRIEF_PROMPT,
    VC_BOARDROOM_PROMPT,
    PARTNER_BOARDROOM_PROMPT,
)
from src.data.vector_db import search_celebrity_background, search_professor_background
from src.data.market import MARKET_CONDITIONS

logger = logging.getLogger(__name__)

# ── SageMaker config (set via environment variables / Docker env) ──────────────
SAGEMAKER_ENDPOINT = os.getenv("SAGEMAKER_ENDPOINT", "boardroom-mistral-endpoint")
AWS_REGION = os.getenv("AWS_REGION", "us-east-1")

# ── boto3 SageMaker runtime client ─────────────────────────────────────────────
_runtime_client = None


def _get_sagemaker_client():
    """Lazy-initialize the SageMaker runtime client."""
    global _runtime_client
    if _runtime_client is None:
        _runtime_client = boto3.client(
            "sagemaker-runtime",
            region_name=AWS_REGION,
        )
    return _runtime_client


def _call_sagemaker(system_prompt: str, user_message: str, temperature: float = 0.7, max_new_tokens: int = 512) -> str:
    """
    Invoke the SageMaker Mistral-7B-Instruct endpoint.

    Mistral uses the [INST] instruction format:
        <s>[INST] {system}\\n\\nUser: {message} [/INST]

    Args:
        system_prompt: The advisor persona + context prompt.
        user_message:  The founder's question.
        temperature:   Sampling temperature (0.0 = deterministic, 1.0 = creative).
        max_new_tokens: Maximum tokens to generate.

    Returns:
        Generated text string from the model.
    """
    # Format prompt in Mistral instruction format
    prompt = (
        f"<s>[INST] {system_prompt}\n\n"
        f"The founder asks: {user_message} [/INST]"
    )

    payload = {
        "inputs": prompt,
        "parameters": {
            "max_new_tokens": max_new_tokens,
            "temperature": temperature,
            "do_sample": True,
            "return_full_text": False,  # Only return generated part, not the prompt
            "stop": ["</s>", "[INST]"],
        },
    }

    client = _get_sagemaker_client()
    response = client.invoke_endpoint(
        EndpointName=SAGEMAKER_ENDPOINT,
        ContentType="application/json",
        Body=json.dumps(payload),
    )

    result = json.loads(response["Body"].read().decode("utf-8"))

    # HuggingFace TGI returns a list: [{"generated_text": "..."}]
    if isinstance(result, list) and len(result) > 0:
        return result[0].get("generated_text", "").strip()
    elif isinstance(result, dict):
        return result.get("generated_text", "").strip()
    return ""


# ── Helper functions ───────────────────────────────────────────────────────────

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


def _build_chat_history_text(state, max_messages: int = 6) -> str:
    """Build recent chat history as plain text for inclusion in the prompt."""
    recent = state.chat_messages[-max_messages:] if state.chat_messages else []
    lines = []
    for msg in recent:
        if msg.role == "user":
            lines.append(f"Founder: {msg.content}")
        else:
            lines.append(f"{msg.speaker}: {msg.content}")
    return "\n".join(lines)


# ── Main advisor functions ─────────────────────────────────────────────────────

def get_advisor_responses(state, user_message: str) -> Tuple[str, str]:
    """
    Get responses from both Celebrity and Professor advisors.

    Args:
        state: GameState instance
        user_message: The founder's question/message

    Returns:
        Tuple of (celebrity_response, professor_response)
    """
    cond = MARKET_CONDITIONS.get(state.market_condition, {})
    market_label = cond.get("label", "Stable")
    event_context = _build_event_context(state)
    history_text = _build_chat_history_text(state)

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
    if history_text:
        celebrity_system += f"\n\nRecent conversation:\n{history_text}"

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
    if history_text:
        professor_system += f"\n\nRecent conversation:\n{history_text}"

    # ── Call SageMaker for both ──
    celebrity_response = ""
    try:
        celebrity_response = _call_sagemaker(celebrity_system, user_message)
    except Exception as e:
        logger.error(f"Celebrity SageMaker call failed: {e}")
        celebrity_response = f"[{celebrity_name}]: Sorry, I'm having trouble connecting right now. Go with your gut on this one."

    professor_response = ""
    try:
        professor_response = _call_sagemaker(professor_system, user_message)
    except Exception as e:
        logger.error(f"Professor SageMaker call failed: {e}")
        professor_response = f"[Prof. {professor_name}]: I apologize, but I'm unable to provide analysis at the moment."

    return celebrity_response, professor_response


def get_celebrity_response(state, user_message: str) -> str:
    """Get a response from the Celebrity advisor only."""
    cond = MARKET_CONDITIONS.get(state.market_condition, {})
    market_label = cond.get("label", "Stable")
    event_context = _build_event_context(state)
    history_text = _build_chat_history_text(state)

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
    if history_text:
        celebrity_system += f"\n\nRecent conversation:\n{history_text}"

    try:
        return _call_sagemaker(celebrity_system, user_message)
    except Exception as e:
        logger.error(f"Celebrity SageMaker call failed: {e}")
        return f"[{celebrity_name}]: Sorry, I'm having trouble connecting right now. Go with your gut on this one."


def get_professor_response(state, user_message: str) -> str:
    """Get a response from the Professor advisor only."""
    cond = MARKET_CONDITIONS.get(state.market_condition, {})
    market_label = cond.get("label", "Stable")
    event_context = _build_event_context(state)
    history_text = _build_chat_history_text(state)

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
    if history_text:
        professor_system += f"\n\nRecent conversation:\n{history_text}"

    try:
        return _call_sagemaker(professor_system, user_message)
    except Exception as e:
        logger.error(f"Professor SageMaker call failed: {e}")
        return f"[Prof. {professor_name}]: I apologize, but I'm unable to provide analysis at the moment."


# ═══════════════════════════════════════════════════════════════════
# END-OF-GAME DEBRIEF
# ═══════════════════════════════════════════════════════════════════

def get_game_debrief(state) -> str:
    """Generate a detailed post-game debrief using the full game history."""
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
        return _call_sagemaker(DEBRIEF_PROMPT, user_content, max_new_tokens=800)
    except Exception as e:
        logger.error(f"Debrief SageMaker call failed: {e}")
        return "Unable to generate debrief at this time."


# ═══════════════════════════════════════════════════════════════════
# BOARDROOM VC CHAT
# ═══════════════════════════════════════════════════════════════════

def get_vc_opening(state) -> str:
    """Generate the VC's opening statement for the board review."""
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
        return _call_sagemaker(system, opening_prompt)
    except Exception as e:
        logger.error(f"VC opening SageMaker call failed: {e}")
        return "Let's cut to the chase. Your burn rate concerns me. Walk me through your plan to reach profitability."


def get_vc_response(state, user_message: str):
    """
    Get VC and partner response to founder's message during board review.
    Returns (vc_response, partner_response, verdict_or_none)
    """
    import re as _re

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

    partner_system = PARTNER_BOARDROOM_PROMPT.format(
        partner_name=state.professor.get("name", "Professor"),
        quarter=state.current_quarter,
        sector=state.sector,
        cash=state.cash,
        revenue=state.revenue,
        milestones_completed=state.milestones_completed,
        stats_summary=stats_summary or "No stats yet.",
    )

    # Build history text
    history_lines = []
    for msg in state.board_chat_messages[-8:]:
        if msg.role == "user":
            history_lines.append(f"Founder: {msg.content}")
        elif msg.role == "vc":
            history_lines.append(f"VC: {msg.content}")
        elif msg.role == "partner":
            history_lines.append(f"{state.professor.get('name', 'Professor')}: {msg.content}")
    history_text = "\n".join(history_lines)

    # Determine if final exchange
    founder_msgs = sum(1 for m in state.board_chat_messages if m.role == "user")
    is_final = founder_msgs >= 3

    final_instruction = (
        "\nThis is the final exchange. Give your verdict now. "
        "End your response with [VERDICT: IMPRESSED], [VERDICT: NEUTRAL], or [VERDICT: CONCERNED] on its own line."
        if is_final else ""
    )

    vc_full_system = vc_system + final_instruction
    if history_text:
        vc_full_system += f"\n\nConversation so far:\n{history_text}"

    # VC response
    vc_response = ""
    try:
        vc_response = _call_sagemaker(vc_full_system, user_message)
    except Exception as e:
        logger.error(f"VC SageMaker call failed: {e}")
        vc_response = "Interesting point. But I need to see better numbers before I'm convinced."

    # Extract verdict if present
    verdict = None
    verdict_match = _re.search(r'\[VERDICT:\s*(IMPRESSED|NEUTRAL|CONCERNED)\]', vc_response)
    if verdict_match:
        verdict = verdict_match.group(1)
        vc_response = vc_response[:verdict_match.start()].strip()

    # Partner response
    partner_name = state.professor.get("name", "Professor")
    partner_context = (
        f"The VC just said: '{vc_response[:200]}'. "
        f"The founder said: '{user_message[:200]}'. Add your perspective."
    )
    if history_text:
        partner_system += f"\n\nConversation so far:\n{history_text}"

    partner_response = ""
    try:
        partner_response = _call_sagemaker(partner_system, partner_context)
    except Exception as e:
        logger.error(f"Partner SageMaker call failed: {e}")
        partner_response = "I agree with the VC's assessment. The data speaks for itself."

    return vc_response, partner_response, verdict
