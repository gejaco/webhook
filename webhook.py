from typing import Optional
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
import json

app = FastAPI()

@app.post("/webhook")
async def handle_webhook(request: Request, session_id: Optional[str] = None, uid: Optional[str] = None):
    payload = await request.json()
    print("=" * 50)
    print("Received webhook payload:", json.dumps(payload, indent=2))
    # Process the webhook payload
    print("session_id:", session_id, "uid:", uid)
    return JSONResponse({"status": "success"})