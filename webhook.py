from typing import Optional
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
import json

app = FastAPI()

@app.post("/webhook")
async def handle_webhook(request: Request, session_id: Optional[str] = Query(None), uid: Optional[str] = Query(None)):
    payload = await request.json()
    # Process the webhook payload
    print("session_id:", session_id, "uid:", uid)
    return JSONResponse({"status": "success"})