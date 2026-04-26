import json
from groq import AsyncGroq
from app.config import GROQ_API_KEY

async def evaluate_loan_request(borrower: dict, candidates: list[dict]) -> dict:
    try:
        client = AsyncGroq(api_key=GROQ_API_KEY)
        system_prompt = (
            "You are the Decision Agent for TokenLend. Evaluate loan requests. "
            "Consider trust scores and token availability. Lenders earn TLC yield. "
            "Respond ONLY with valid JSON. No markdown."
        )
        user_prompt = json.dumps({"borrower": borrower, "candidates": candidates})
        
        response = await client.chat.completions.create(
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            model="llama-3.3-70b-versatile",
            response_format={"type": "json_object"}
        )
        
        content = response.choices[0].message.content
        result = json.loads(content)
        return result
    except Exception as e:
        print(f"Error in decision_agent: {e}")
        # Rule-based fallback
        if not candidates:
            return {"approve": False, "reason": "No candidates available."}
        
        best_candidate = max(candidates, key=lambda c: c.get("token_balance", 0) * c.get("trust_score", 0))
        return {
            "approve": True, 
            "lender_id": best_candidate["id"], 
            "amount": borrower.get("requested_amount", 0), 
            "reason": "Rule-based fallback due to API error."
        }
