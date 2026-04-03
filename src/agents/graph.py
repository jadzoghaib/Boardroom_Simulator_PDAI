import os
import operator
from typing import TypedDict, Annotated, Sequence
from dotenv import load_dotenv
from langchain_groq import ChatGroq
from langchain_core.messages import HumanMessage, SystemMessage, AIMessage
from langgraph.graph import StateGraph, END
from langgraph.checkpoint.memory import MemorySaver

from src.agents.prompts import (
    ML_PREDICTOR_PROMPT, 
    get_vc_prompt, 
    get_vc_name, 
    PARTNER_PROMPT
)
from src.agents.tools import check_survival_probability, query_startup_playbook, query_celebrity_background

load_dotenv()

# The State format
class BoardroomState(TypedDict):
    messages: Annotated[Sequence[dict], operator.add]
    budget: float
    burn_rate: float
    revenue: float
    founder_experience: int
    sector: str
    pitch: str
    partner_name: str  # name of the co-founder partner
    partner_style: str  # e.g., 'technical', 'commercial', 'operator'
    synergy_bonus: float  # original synergy bonus from partner
    celebrity_name: str  # selected celebrity cofounder name
    professor_name: str  # selected professor partner name
    vc_cycle: int  # which VC persona (0, 1, or 2)
    partner_satisfaction: float  # 0-1, starts at 1.0
    disagreement_cycles: int  # count of consecutive cycles with disagreement
    partner_departed: bool  # True if partner left
    partner_penalty_applied: bool  # ensure departure stat penalty is applied once


def _get_llm() -> ChatGroq:
    api_key = os.getenv("GROQ_API_KEY", "")
    if not api_key:
        raise RuntimeError("GROQ_API_KEY is not set. Add it to your .env or environment variables.")
    return ChatGroq(model="llama-3.3-70b-versatile", temperature=0.7, api_key=api_key)

def ml_predictor_node(state: BoardroomState):
    # ML Predictor reads structural state and queries the ML explicitly
    result = check_survival_probability.invoke({
        "budget": state["budget"],
        "burn_rate": state["burn_rate"],
        "revenue": state["revenue"],
        "founder_experience": state["founder_experience"],
        "sector": state["sector"]
    })
    msg = AIMessage(content=f"[Data Analyst]: I ran the ML physics engine. {result}")
    return {"messages": [msg]}

def vc_node(state: BoardroomState):
    # VC LLM with rotating persona
    llm = _get_llm()
    vc_name = get_vc_name(state.get("vc_cycle", 0))
    vc_prompt = get_vc_prompt(state.get("vc_cycle", 0))
    sys_msg = SystemMessage(content=vc_prompt)
    history = state.get("messages", [])
    response = llm.invoke([sys_msg] + history)
    msg = AIMessage(content=f"[{vc_name}]: {response.content}")
    # Advance VC cycle for next turn
    next_cycle = (state.get("vc_cycle", 0) + 1) % 3
    return {"messages": [msg], "vc_cycle": next_cycle}

def partner_node(state: BoardroomState):
    # Partner (co-founder with equity stake) provides advice and tracks disagreement
    partner_name = state.get("partner_name", "Partner")
    partner_style = state.get("partner_style", "")
    partner_departed = state.get("partner_departed", False)
    disagreement_cycles = state.get("disagreement_cycles", 0)
    celebrity_name = state.get("celebrity_name", "")
    
    # If partner already left, output departure message
    if partner_departed:
        msg = AIMessage(content=f"[{partner_name}]: (Partner departed - no longer in boardroom)")
        return {"messages": [msg]}
    
    # Partner gives advice using tools and history
    llm = _get_llm()
    agent = llm.bind_tools([query_startup_playbook, query_celebrity_background])
    
    # Fill in partner prompt with their details
    partner_expertise = _get_partner_expertise(partner_style)
    partner_prompt = PARTNER_PROMPT.format(
        partner_name=partner_name,
        partner_style=partner_style,
        partner_expertise=partner_expertise
    )
    sys_msg = SystemMessage(content=partner_prompt + f" The startup is in {state['sector']}.")
    
    history = state.get("messages", [])
    context_messages = []
    if celebrity_name:
        celebrity_context = query_celebrity_background.invoke(
            {
                "celebrity_name": celebrity_name,
                "query": "leadership style, strategic strengths, and decision-making patterns",
            }
        )
        context_messages.append(AIMessage(content=f"Celebrity context: {celebrity_context}"))
    response = agent.invoke([sys_msg] + history + context_messages)
    
    # Resolve tool calls
    if response.tool_calls:
        tool_messages = []
        for tool_call in response.tool_calls:
            tool_name = tool_call.get("name", "")
            args = tool_call.get("args", {})

            if tool_name == "query_startup_playbook":
                tool_res = query_startup_playbook.invoke(args)
                tool_messages.append(AIMessage(content=f"Playbook says: {tool_res}"))
            elif tool_name == "query_celebrity_background":
                tool_res = query_celebrity_background.invoke(args)
                tool_messages.append(AIMessage(content=f"Celebrity context: {tool_res}"))

        final_history = [sys_msg] + history + context_messages + tool_messages
        final = llm.invoke(final_history)
        partner_response = final.content
    else:
        partner_response = response.content
    
    # Detect disagreement signals (simple heuristic)
    disagreement_signals = ["disagree", "not aligned", "concerned about", "shouldn't", "wrong", "objection"]
    has_disagreement = any(signal.lower() in partner_response.lower() for signal in disagreement_signals)
    
    # Track disagreement cycles
    if has_disagreement:
        new_disagreement_cycles = disagreement_cycles + 1
    else:
        new_disagreement_cycles = 0  # Reset if resolved
    
    # Check if partner departs (3 consecutive cycles of disagreement)
    new_partner_departed = False
    departure_msg = ""
    if new_disagreement_cycles >= 3:
        new_partner_departed = True
        departure_msg = f"\n\n[{partner_name}]: I'm leaving. Too many fundamental disagreements. I'm out!"
    
    msg = AIMessage(content=f"[{partner_name}]: {partner_response}{departure_msg}")
    
    return {
        "messages": [msg],
        "disagreement_cycles": new_disagreement_cycles,
        "partner_departed": new_partner_departed
    }

def _get_partner_expertise(partner_style: str) -> str:
    """Map partner style to expertise description."""
    style = (partner_style or "").lower()
    if "tech" in style or "ai" in style or "data" in style:
        return "engineering depth, technical architecture, and AI productization"
    if "finance" in style or "analytics" in style:
        return "capital discipline, KPI design, and financial strategy"
    if "operations" in style or "ops" in style:
        return "operational execution, systems design, and scaling"
    if "innovation" in style or "r&d" in style:
        return "innovation strategy, research translation, and experimentation"
    if "brand" in style or "growth" in style:
        return "market narrative, distribution strategy, and growth loops"
    return "startup strategy"

# Build Graph with Checkpointing (Memory)
builder = StateGraph(BoardroomState)
builder.add_node("ml_predictor", ml_predictor_node)
builder.add_node("vc", vc_node)
builder.add_node("partner", partner_node)

builder.set_entry_point("ml_predictor")
builder.add_edge("ml_predictor", "vc")

# HITL interruption here! It pauses BEFORE reaching the partner
builder.add_edge("vc", "partner")
builder.add_edge("partner", END)

memory = MemorySaver()
# Compile with interrupt so player can respond to the VC
boardroom_graph = builder.compile(
    checkpointer=memory,
    interrupt_before=["partner"] 
)
