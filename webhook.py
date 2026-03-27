from fastapi import FastAPI, Request, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse, FileResponse
from fastapi.staticfiles import StaticFiles
import json
import os

app = FastAPI()

# Mount static files (serves index.html automatically)
app.mount("/static", StaticFiles(directory="."), name="static")

# Single global transcript (appends from all Omi webhooks)
transcript = []

# List of connected WebSocket clients
connected_clients = []

@app.post("/")
@app.post("/webhook")
async def webhook_root(request: Request, uid: str | None = None):
    print("WEBHOOK HIT")    
    global transcript

    raw = await request.body()
    print("=== WEBHOOK HIT ===")
    print("Headers:", dict(request.headers))
    print("Raw body:", raw.decode("utf-8", errors="ignore"))    

    try:
        body = await request.json()
        print("Parsed JSON type:", type(body).__name__)
        print("Parsed JSON:", body)
    except Exception as e:
        print("JSON parse failed:", e)
        return {"ok": False, "error": "invalid json"}
    except Exception as e:
        print("Error parsing JSON:", e)
        body = {}

    print(f"Omi webhook to root: uid={uid}, body={body}")
    
    # FIX: Extract segments, don't extend the dict
    if isinstance(body, dict) and "segments" in body:
        new_segments = body["segments"]
        transcript.extend(new_segments)  # Only append segments array
        print(f"Added {len(new_segments)} segments")
    else:
        transcript.extend(body)  # Curl-style list fallback
    
    # Broadcast full transcript array
    for client in connected_clients[:]:
        try:
            await client.send_json(transcript)
        except:
            connected_clients.remove(client)
    
    return {"status": "received", "uid": uid, "added": len(new_segments) if 'new_segments' in locals() else len(body)}



# @app.post("/webhook")
# async def webhook(request: Request, uid: str = None):  # Accept optional uid query param
#     global transcript
#     body = await request.json()
    
#     print(f"Webhook hit with uid={uid}")  # Log the uid
#     print("New segments:", json.dumps(body, indent=2))
    
#     # Append new segments
#     transcript.extend(body)
    
#     # Broadcast to clients...
#     for client in connected_clients[:]:
#         try:
#             await client.send_json(transcript)
#         except:
#             connected_clients.remove(client)
    
#     return {"status": "received", "added": len(body), "uid": uid}

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    connected_clients.append(websocket)
   
    # Send current transcript immediately
    try:
        await websocket.send_json(transcript)
    except:
        pass
   
    try:
        # Keep connection alive
        await websocket.receive_text()
    except WebSocketDisconnect:
        connected_clients.remove(websocket)

@app.get("/", response_class=FileResponse)
async def get_frontend():
    if os.path.exists("index.html"):
        return FileResponse("index.html")
    else:
        return {"error": "index.html not found"}