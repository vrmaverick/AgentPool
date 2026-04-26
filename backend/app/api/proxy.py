from fastapi import APIRouter, Header, HTTPException
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from typing import List, Dict
from app.middleware.auth import validate_proxy_token
from app.core import proxy

router = APIRouter()

class ChatRequest(BaseModel):
    messages: List[Dict[str, str]]
    model: str
    max_tokens: int

@router.post("/chat")
async def proxy_chat_endpoint(req: ChatRequest, authorization: str = Header(...)):
    if not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Invalid Authorization header format. Expected 'Bearer ptk_...'")
    
    ptk = authorization.split("Bearer ")[1]
    ptk_record = await validate_proxy_token(ptk)
    
    result = await proxy.proxy_chat(ptk_record, req.messages, req.model, req.max_tokens)
    
    return JSONResponse(
        content=result["response_body"],
        headers={"X-Credits-Remaining": str(result["credits_remaining"])}
    )
