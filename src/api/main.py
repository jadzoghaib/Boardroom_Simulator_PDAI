from fastapi import FastAPI
from pydantic import BaseModel
from langchain_core.messages import HumanMessage
from src.ml.predictor import MarketPredictor
from src.agents.graph import boardroom_graph
import uuid

app = FastAPI(title="Boardroom Sim API")
predictor = MarketPredictor()

@app.get("/")
def read_root():
    return {"status": "online", "message": "The Boardroom Sim FastAPI backend is running! You can now start Streamlit."}

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
