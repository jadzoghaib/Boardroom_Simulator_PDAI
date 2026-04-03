import os
import operator
from typing import TypedDict, Annotated, Sequence
from dotenv import load_dotenv
from langchain_groq import ChatGroq
from langchain_core.messages import HumanMessage, SystemMessage, AIMessage
from langgraph.graph import StateGraph, END
from langgraph.checkpoint.memory import MemorySaver

from src.agents.prompts import VC_SYSTEM_PROMPT, AUDITOR_SYSTEM_PROMPT, MENTOR_SYSTEM_PROMPT
from src.agents.tools import check_survival_probability, query_startup_playbook

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


def _get_llm() -> ChatGroq:
    api_key = os.getenv("GROQ_API_KEY", "")
    if not api_key:
        raise RuntimeError("GROQ_API_KEY is not set. Add it to your .env or environment variables.")
    return ChatGroq(model="llama-3.3-70b-versatile", temperature=0.7, api_key=api_key)

def auditor_node(state: BoardroomState):
    # Auditor reads structural state and queries the ML explicitly
    result = check_survival_probability.invoke({
        "budget": state["budget"],
        "burn_rate": state["burn_rate"],
        "revenue": state["revenue"],
        "founder_experience": state["founder_experience"],
        "sector": state["sector"]
    })
    msg = AIMessage(content=f"[Auditor]: I ran the ML physics engine. {result}")
    return {"messages": [msg]}

def vc_node(state: BoardroomState):
    # Pass history to VC LLM to judge
    llm = _get_llm()
    sys_msg = SystemMessage(content=VC_SYSTEM_PROMPT)
    history = state.get("messages", [])
    response = llm.invoke([sys_msg] + history)
    msg = AIMessage(content=f"[Skeptical VC]: {response.content}")
    return {"messages": [msg]}

def mentor_node(state: BoardroomState):
    # Mentor gets the tool to search the Lean Startup playbook
    llm = _get_llm()
    agent = llm.bind_tools([query_startup_playbook])
    sys_msg = SystemMessage(content=MENTOR_SYSTEM_PROMPT + f" The startup is in {state['sector']}.")
    
    # Prompt the LLM using the history
    history = state.get("messages", [])
    response = agent.invoke([sys_msg] + history)
    
    # Resolve tool calls simple logic
    if response.tool_calls:
        # For simplicity, just invoke the first tool call
        tool_res = query_startup_playbook.invoke(response.tool_calls[0]["args"])
        final_history = [sys_msg] + history + [AIMessage(content=f"Playbook says: {tool_res}")]
        final = llm.invoke(final_history)
        msg = AIMessage(content=f"[Pragmatic Mentor]: {final.content}")
    else:
        msg = AIMessage(content=f"[Pragmatic Mentor]: {response.content}")

    return {"messages": [msg]}

# Build Graph with Checkpointing (Memory)
builder = StateGraph(BoardroomState)
builder.add_node("auditor", auditor_node)
builder.add_node("vc", vc_node)
builder.add_node("mentor", mentor_node)

builder.set_entry_point("auditor")
builder.add_edge("auditor", "vc")

# HITL interruption here! It pauses BEFORE reaching the mentor
builder.add_edge("vc", "mentor")
builder.add_edge("mentor", END)

memory = MemorySaver()
# Compile with interrupt so player can respond to the VC
boardroom_graph = builder.compile(
    checkpointer=memory,
    interrupt_before=["mentor"] 
)
