import streamlit as st
import requests
import uuid

API_URL = "http://127.0.0.1:8001"

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

tab1, tab2 = st.tabs(["📊 Phase 1: Market Physics", "💼 Phase 2: The Board Meeting"])

with tab1:
    st.subheader("Query Your Startup's Survival Probability")
    st.markdown("Use this tab to run your current numbers through the Scikit-Learn Model before facing the board.")
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
                
                # Display metrics visually
                m1, m2 = st.columns(2)
                m1.metric(label="Predicted Success Probability", value=f"{prob * 100:.1f}%")
                m2.metric(label="Runway Remaining", value=f"{runway} Months")
        except Exception as e:
            st.error("API Error. Make sure FastAPI is running: uvicorn src.api.main:app --reload")

with tab2:
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
