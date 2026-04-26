import asyncio
import json
from fastapi import APIRouter
from fastapi.responses import StreamingResponse
from app.services import user_service, agent_service, token_service, loan_service
from app.db import queries
from app.config import GROQ_API_KEY

router = APIRouter()

# Global state to track agents for the demo
demo_state = {}

@router.post("/seed")
async def seed_demo():
    vedant_email = "vedant@demo.com"
    priya_email = "priya@demo.com"
    
    async def setup_user(name, email):
        existing = await queries.get_user_by_email(email)
        if not existing:
            return await user_service.register_user(name, email, "demo123")
        return existing["id"]

    vedant_id = await setup_user("Vedant", vedant_email)
    priya_id = await setup_user("Priya", priya_email)
        
    v_login = await user_service.login_user(vedant_email, "demo123")
    p_login = await user_service.login_user(priya_email, "demo123")
    
    r_agent = await agent_service.register_agent(vedant_id, "ResearchAgent", "pipeline", GROQ_API_KEY, 500)
    s_agent = await agent_service.register_agent(vedant_id, "SummaryAgent", "pipeline", GROQ_API_KEY, 500)
    a_agent = await agent_service.register_agent(priya_id, "IdleAgent-Alpha", "lender", "gsk_priya123", 900)
    b_agent = await agent_service.register_agent(priya_id, "IdleAgent-Beta", "lender", "gsk_priya456", 600)
    
    demo_state["vedant_id"] = vedant_id
    demo_state["priya_id"] = priya_id
    demo_state["r_agent_id"] = r_agent["id"]
    demo_state["a_agent_id"] = a_agent["id"]
    
    return {
        "vedant_token": v_login["access_token"],
        "priya_token": p_login["access_token"],
        "agent_ids": [r_agent["id"], s_agent["id"], a_agent["id"], b_agent["id"]],
        "message": "Demo seeded"
    }

@router.post("/run")
async def run_demo():
    async def event_generator():
        def emit(step, label, detail, state):
            payload = json.dumps({"step": step, "label": label, "detail": detail, "state": state})
            return f"data: {payload}\n\n"
            
        r_agent_id = demo_state.get("r_agent_id")
        a_agent_id = demo_state.get("a_agent_id")
        vedant_id = demo_state.get("vedant_id")
        
        if not r_agent_id:
            yield emit(0, "Error", "Please seed demo first", {})
            return
            
        yield emit(1, "Pipeline starts", "ResearchAgent active", {})
        await asyncio.sleep(0.8)
        
        await token_service.consume_tokens(r_agent_id, 200)
        yield emit(2, "Tokens draining", "use_tokens 200 on ResearchAgent", {})
        await asyncio.sleep(0.8)
        
        await token_service.consume_tokens(r_agent_id, 250)
        yield emit(3, "Tokens critical", "use_tokens 250 more (50 left)", {})
        await asyncio.sleep(0.8)
        
        await token_service.consume_tokens(r_agent_id, 50)
        yield emit(4, "TOKEN CRISIS", "use_tokens 50 (hits 0)", {})
        await asyncio.sleep(0.8)
        
        yield emit(5, "Decision Agent fires", "call evaluate_loan_request", {})
        await asyncio.sleep(0.8)
        
        loan_res = await loan_service.request_loan(r_agent_id, vedant_id, 200)
        loan_id = loan_res["loan_id"]
        yield emit(6, "Loan approved", f"request_loan 200 tokens from {loan_res['lender_name']}", {"tlc_yield_pending": 10})
        await asyncio.sleep(0.8)
        
        yield emit(7, "Proxy call 1", "mock proxy call", {"key_used": "Priya's (masked)", "tokens": 80})
        await asyncio.sleep(0.8)
        
        yield emit(8, "Proxy call 2", "mock proxy call", {"key_used": "Priya's (masked)", "tokens": 70})
        await asyncio.sleep(0.8)
        
        yield emit(9, "Pipeline complete", "SummaryAgent and ReportAgent finish", {})
        await asyncio.sleep(0.8)
        
        # Grant vedant some tokens to repay the loan for the demo
        await queries.update_agent_token_balance(r_agent_id, 200)
        
        yield emit(10, "Auto-repaying", "repay_loan fires", {})
        await loan_service.repay_loan(loan_id, vedant_id)
        await asyncio.sleep(0.8)
        
        yield emit(11, "TLC minted", "Priya earned 10 TLC, platform earned 1 TLC", {})
        await asyncio.sleep(0.8)
        
        yield emit(12, "Done", "final state: balances, TLC wallets", {})
        
    return StreamingResponse(event_generator(), media_type="text/event-stream")

@router.get("/state")
async def get_demo_state():
    agents = await queries.get_all_agents()
    loans = await queries.get_all_loans()
    return {"agents": agents, "loans": loans}
