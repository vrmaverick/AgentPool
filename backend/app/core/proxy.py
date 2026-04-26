import httpx
from fastapi import HTTPException
from app.services import agent_service
from app.db import queries

async def forward_to_groq(real_api_key: str, messages: list, model: str, max_tokens: int) -> dict:
    url = "https://api.groq.com/openai/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {real_api_key}",
        "Content-Type": "application/json"
    }
    payload = {
        "model": model,
        "messages": messages,
        "max_tokens": max_tokens
    }
    
    async with httpx.AsyncClient() as client:
        response = await client.post(url, headers=headers, json=payload, timeout=60.0)
        
    if response.status_code != 200:
        raise HTTPException(status_code=response.status_code, detail=f"Groq API error")
        
    return response.json()

async def proxy_chat(ptk_record: dict, messages: list, model: str, max_tokens: int) -> dict:
    # 2. Check credits_remaining > 0
    if ptk_record.get("credits_remaining", 0) <= 0:
        raise HTTPException(status_code=402, detail="Proxy token exhausted.")
        
    # 3. Determine key
    key_source = ptk_record.get("key_source")
    agent_id = ptk_record.get("agent_id")
        
    real_api_key = await agent_service.get_decrypted_key(agent_id)
    
    # 4. Call forward_to_groq
    response_body = await forward_to_groq(real_api_key, messages, model, max_tokens)
    
    # 5. Extract usage
    usage = response_body.get("usage", {})
    prompt_tokens = usage.get("prompt_tokens", 0)
    completion_tokens = usage.get("completion_tokens", 0)
    tokens_used = prompt_tokens + completion_tokens
    
    # 6. Deduct usage
    await queries.update_proxy_token_credits(ptk_record["id"], -tokens_used)
    
    # 7. Log call to tx_log
    await queries.insert_tx_log(
        event_type="proxy_call",
        actor_user_id=ptk_record["user_id"],
        related_id=ptk_record.get("loan_id") or ptk_record["id"],
        description=f"Proxy call used {tokens_used} tokens. Source: {key_source}"
    )
    
    credits_remaining = max(0, ptk_record.get("credits_remaining", 0) - tokens_used)
    
    return {
        "response_body": response_body,
        "tokens_used": tokens_used,
        "credits_remaining": credits_remaining
    }
