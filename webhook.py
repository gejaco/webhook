from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
import json

app = FastAPI()

@app.post("/webhook")
async def handle_webhook(request: Request, session_id: str, uid: str):
    payload = await request.json()
    # Process the webhook payload
    return JSONResponse({"status": "success"})