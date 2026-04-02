import os

# 1. Requirements
with open('requirements.txt', 'a', encoding='utf-8') as f:
    f.write('\nlangchain-groq\nlanggraph-checkpoint\n')

# 2. vector_db.py
vector_db_code = '''import os
import chromadb

DB_PATH = os.path.join(os.path.dirname(__file__), "chroma_db")

def build_mentor_kb():
    \"\"\"Builds a local vector database of startup playbooks for the Mentor Agent.\"\"\"
    client = chromadb.PersistentClient(path=DB_PATH)
    collection = client.get_or_create_collection(name="startup_playbooks")
    
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
    \"\"\"Searches the ChromaDB vector store for relevant business advice.\"\"\"
    client = chromadb.PersistentClient(path=DB_PATH)
    collection = client.get_or_create_collection(name="startup_playbooks")
    
    results = collection.query(query_texts=[query], n_results=n_results)
    if results and results['documents'] and len(results['documents'][0]) > 0:
        return results['documents'][0][0]
    return "No specific playbook strategy found."

if __name__ == "__main__":
    build_mentor_kb()
    print("Vector database populated successfully.")
'''
with open('src/data/vector_db.py', 'w', encoding='utf-8') as f:
    f.write(vector_db_code)

# 3. predictor.py update
predictor_code = '''import joblib
import pandas as pd
import os
import logging

logger = logging.getLogger(__name__)

class MarketPredictor:
    def __init__(self, model_path: str = "src/ml/models/gb_startup_model.pkl"):
        self.model_path = model_path
        self.model = None
        self._load_model()

    def _load_model(self):
        if os.path.exists(self.model_path):
            self.model = joblib.load(self.model_path)
            logger.info("Model loaded successfully.")
        else:
            logger.warning(f"Model not found at {self.model_path}. Train the model first.")

    def predict_success_probability(self, burn_rate: float, revenue: float, founder_experience: int, sector: str) -> float:
        if not self.model:
            return 0.5 
            
        sector_encoded = hash(sector) % 10 
        burn_to_rev = 0 if revenue == 0 else burn_rate / revenue

        features = pd.DataFrame([{
            'burn_rate': burn_rate,
            'revenue': revenue,
            'founder_experience': founder_experience,
            'sector': sector_encoded,
            'burn_to_revenue_ratio': burn_to_rev
        }])
        
        prob = self.model.predict_proba(features)[0][1]
        return round(float(prob), 2)

    def calculate_runway(self, budget: float, burn_rate: float, revenue: float) -> int:
        \"\"\"Calculates survival months before bankruptcy.\"\"\"
        net_burn = burn_rate - revenue
        if net_burn <= 0:
            return 999 # Infinite runway / Profitable
        return int(budget / net_burn)
'''
with open('src/ml/predictor.py', 'w', encoding='utf-8') as f:
    f.write(predictor_code)

# 4. tools.py update
tools_code = '''from langchain_core.tools import tool
from src.ml.predictor import MarketPredictor
from src.data.vector_db import search_playbook

predictor = MarketPredictor()

@tool
def check_survival_probability(budget: float, burn_rate: float, revenue: float, founder_experience: int, sector: str) -> str:
    \"\"\"Uses the custom ML model to predict the startup's chance of success and runway.\"\"\"
    prob = predictor.predict_success_probability(burn_rate, revenue, founder_experience, sector)
    runway = predictor.calculate_runway(budget, burn_rate, revenue)
    
    variance = "high" if runway < 12 else "low"
    chance = prob * 100
    
    return f"The ML model predicts a {chance:.1f}% chance of success. Your runway is {runway} months. Risk variance: {variance}."

@tool
def query_startup_playbook(query: str) -> str:
    \"\"\"Searches the vector database for business frameworks and pivot strategies.\"\"\"
    return search_playbook(query)
'''
with open('src/agents/tools.py', 'w', encoding='utf-8') as f:
    f.write(tools_code)

# 5. graph.py update
graph_code = '''import os
import operator
from typing import TypedDict, Annotated, Sequence
from langchain_groq import ChatGroq
from langchain_core.messages import HumanMessage, SystemMessage, AIMessage
from langgraph.graph import StateGraph, END
from langgraph.checkpoint.memory import MemorySaver

from src.agents.prompts import VC_SYSTEM_PROMPT, AUDITOR_SYSTEM_PROMPT, MENTOR_SYSTEM_PROMPT
from src.agents.tools import check_survival_probability, query_startup_playbook

# The State format
class BoardroomState(TypedDict):
    messages: Annotated[Sequence[dict], operator.add]
    budget: float
    burn_rate: float
    revenue: float
    founder_experience: int
    sector: str
    pitch: str

# Set Groq API Key explicitly
os.environ["GROQ_API_KEY"] = "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"

# Use ChatGroq with a fast model
llm = ChatGroq(model="llama-3.3-70b-versatile", temperature=0.7)

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
    sys_msg = SystemMessage(content=VC_SYSTEM_PROMPT)
    history = state.get("messages", [])
    response = llm.invoke([sys_msg] + history)
    msg = AIMessage(content=f"[Skeptical VC]: {response.content}")
    return {"messages": [msg]}

def mentor_node(state: BoardroomState):
    # Mentor gets the tool to search the Lean Startup playbook
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
'''
with open('src/agents/graph.py', 'w', encoding='utf-8') as f:
    f.write(graph_code)

# 6. main.py update (FastAPI)
main_code = '''from fastapi import FastAPI
from pydantic import BaseModel
from langchain_core.messages import HumanMessage
from src.ml.predictor import MarketPredictor
from src.agents.graph import boardroom_graph
import uuid

app = FastAPI(title="Boardroom Sim API")
predictor = MarketPredictor()

class BoardroomRequest(BaseModel):
    thread_id: str
    budget: float
    burn_rate: float
    revenue: float
    founder_experience: int
    sector: str
    pitch: str
    action: str = "start"  # "start" or "resume"

@app.post("/api/predict")
def predict_success(req: BoardroomRequest):
    prob = predictor.predict_success_probability(req.burn_rate, req.revenue, req.founder_experience, req.sector)
    runway = predictor.calculate_runway(req.budget, req.burn_rate, req.revenue)
    return {"success_probability": prob, "runway_months": runway}

@app.post("/api/boardroom_turn")
def run_boardroom(req: BoardroomRequest):
    config = {"configurable": {"thread_id": req.thread_id}}
    
    if req.action == "start":
        initial_state = {
            "messages": [HumanMessage(content=f"[Founder Pitch]: {req.pitch}")],
            "budget": req.budget,
            "burn_rate": req.burn_rate,
            "revenue": req.revenue,
            "founder_experience": req.founder_experience,
            "sector": req.sector,
            "pitch": req.pitch
        }
        # Runs until the breakpoint (before mentor)
        boardroom_graph.invoke(initial_state, config)
        
    elif req.action == "resume":
        # Provide the player's counter-argument and resume graph!
        # First update the state with the human's new message
        boardroom_graph.update_state(config, {"messages": [HumanMessage(content=f"[Founder Counter-Argument]: {req.pitch}")]})
        # Then continue invocation
        boardroom_graph.invoke(None, config)
        
    # Return everything in memory
    current_state = boardroom_graph.get_state(config)
    messages_out = []
    for msg in current_state.values.get("messages", []):
        content = msg.content if hasattr(msg, "content") else str(msg)
        messages_out.append(content)
    
    next_nodes = current_state.next
    status = "paused" if len(next_nodes) > 0 else "done"
    
    return {
        "status": status,
        "messages": messages_out
    }
'''
with open('src/api/main.py', 'w', encoding='utf-8') as f:
    f.write(main_code)

# 7. app.py update (Frontend)
app_code = '''import streamlit as st
import requests
import uuid

API_URL = "http://127.0.0.1:8000"

st.set_page_config(page_title="The Boardroom Sim", layout="wide")
st.title("📊 The Boardroom Sim: CEO Dashboard")

# Session State for Thread ID to maintain memory
if "thread_id" not in st.session_state:
    st.session_state.thread_id = str(uuid.uuid4())
if "meeting_status" not in st.session_state:
    st.session_state.meeting_status = "idle" # idle, paused, done

st.sidebar.header("Startup Physics")
budget = st.sidebar.number_input("Current Budget ($)", value=300000, step=50000)
burn_rate = st.sidebar.number_input("Monthly Burn Rate ($)", value=50000, step=5000)
revenue = st.sidebar.number_input("Monthly Revenue ($)", value=10000, step=1000)
experience = st.sidebar.slider("Founder Experience (Years)", 1, 20, 3)
sector = st.sidebar.selectbox("Sector", ["AI", "Fintech", "Healthtech", "SaaS"])

col1, col2 = st.columns([1, 2])

with col1:
    st.subheader("Market Math")
    if st.button("Query Market Physics"):
        try:
            res = requests.post(f"{API_URL}/api/predict", json={
                "thread_id": st.session_state.thread_id,
                "budget": budget,
                "burn_rate": burn_rate,
                "revenue": revenue,
                "founder_experience": experience,
                "sector": sector,
                "pitch": ""
            })
            if res.status_code == 200:
                data = res.json()
                prob = data.get("success_probability", 0)
                runway = data.get("runway_months", 0)
                st.metric(label="Predicted Success Probability", value=f"{prob * 100:.1f}%")
                st.metric(label="Runway Remaining", value=f"{runway} Months")
        except Exception as e:
            st.error("API Error. Make sure FastAPI is running: uvicorn src.api.main:app --reload")

with col2:
    st.subheader("The Boardroom Multi-Agent Simulation")
    
    if st.session_state.meeting_status == "idle":
        pitch = st.text_area("Your Initial Pitch:", "We are going to focus heavily on marketing this quarter to increase revenue.")
        if st.button("Start Board Meeting"):
            with st.spinner("The Board is convening..."):
                try:
                    res = requests.post(f"{API_URL}/api/boardroom_turn", json={
                        "thread_id": st.session_state.thread_id,
                        "budget": budget,
                        "burn_rate": burn_rate,
                        "revenue": revenue,
                        "founder_experience": experience,
                        "sector": sector,
                        "pitch": pitch,
                        "action": "start"
                    })
                    if res.status_code == 200:
                        data = res.json()
                        st.session_state.meeting_status = data["status"]
                        st.session_state.messages = data["messages"]
                        st.rerun()
                except Exception as e:
                    st.error("API Error. Make sure FastAPI is running.")

    elif st.session_state.meeting_status == "paused":
        st.warning("⚠️ The Skeptical VC has challenged you! You must counter-argue to unlock the Mentor's advice and continue.")
        
        # Display transcript so far
        st.markdown("### Transcript")
        for msg in st.session_state.get("messages", []):
            if "[Founder" in msg:
                st.info(msg)
            elif "[Auditor]" in msg:
                st.markdown(f"📊 **{msg}**")
            elif "[Skeptical VC]" in msg:
                st.error(f"😠 **{msg}**")
                
        counter_pitch = st.text_area("Your Counter-Argument:", "I understand the risks, but our strategic pivot to enterprise B2B will lower CAC immediately.")
        
        if st.button("Submit Counter-Argument & Resume Graph"):
            with st.spinner("The Mentor is reviewing the playbook..."):
                res = requests.post(f"{API_URL}/api/boardroom_turn", json={
                    "thread_id": st.session_state.thread_id,
                    "budget": budget,
                    "burn_rate": burn_rate,
                    "revenue": revenue,
                    "founder_experience": experience,
                    "sector": sector,
                    "pitch": counter_pitch,
                    "action": "resume"
                })
                if res.status_code == 200:
                    data = res.json()
                    st.session_state.meeting_status = data["status"]
                    st.session_state.messages = data["messages"]
                    st.rerun()

    elif st.session_state.meeting_status == "done":
        st.success("✅ The Board Meeting Concluded.")
        
        st.markdown("### Final Transcript")
        for msg in st.session_state.get("messages", []):
            if "[Founder" in msg:
                st.info(msg)
            elif "[Skeptical VC]" in msg:
                st.error(f"😠 **{msg}**")
            elif "[Pragmatic Mentor]" in msg:
                st.success(f"💡 **{msg}**")
            else:
                st.markdown(f"**{msg}**")
                
        if st.button("Reset Simulation (New Thread)"):
            st.session_state.thread_id = str(uuid.uuid4())
            st.session_state.meeting_status = "idle"
            st.session_state.messages = []
            st.rerun()
'''
with open('frontend/app.py', 'w', encoding='utf-8') as f:
    f.write(app_code)

print("All Sophistication features successfully deployed!")
