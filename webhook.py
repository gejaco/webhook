from fastapi import FastAPI, Request, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse
import json

app = FastAPI()

# Single global transcript (appends from all Omi webhooks)
transcript = []

# List of connected WebSocket clients
connected_clients = []

@app.post("/webhook")
async def webhook(request: Request):
    global transcript
    body = await request.json()
   
    # Append new segments
    transcript.extend(body)
    print("New segments:", json.dumps(body, indent=2))
   
    # Broadcast to ALL connected clients
    for client in connected_clients[:]:  # Copy to avoid modification during iteration
        try:
            await client.send_json(transcript)
        except:
            connected_clients.remove(client)
   
    return {"status": "received", "added": len(body)}

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

@app.get("/", response_class=HTMLResponse)
async def get_frontend():
    return """
    <!DOCTYPE html>
    <html>
    <head><title>Omi Transcript Viewer</title>
    <style>body{font-family:Arial; max-width:800px; margin:0 auto; padding:20px;}
    button{padding:10px 20px; background:#007bff; color:white; border:none; cursor:pointer;}
    #transcript{max-height:600px; overflow-y:auto; border:1px solid #ddd; padding:10px;}
    .segment{padding:8px; margin:4px 0; border-radius:4px; background:#f8f9fa;}
    .speaker{font-weight:bold; color:#007bff;}
    </style></head>
    <body>
    <h1>🔴 Live Omi Transcript</h1>
    <button onclick="connect()">Connect Live</button>
    <button onclick="clearTranscript()">Clear</button>
    <div id="status">Click Connect to start</div>
    <div id="transcript"></div>
    <script>
    let ws;
    function connect() {
        ws = new WebSocket(`wss://${location.host}/ws`);
        document.getElementById('status').textContent = 'Connected - waiting for Omi...';
        ws.onopen = () => console.log('WebSocket connected');
        ws.onmessage = (event) => {
            const segments = JSON.parse(event.data);
            const transcript = document.getElementById('transcript');
            transcript.innerHTML = segments.map(s =>
                `<div class="segment">
                    <span class="speaker">${s.speaker || 'Unknown'}:</span> ${s.text}
                </div>`
            ).join('');
            transcript.scrollTop = transcript.scrollHeight;
        };
        ws.onerror = () => document.getElementById('status').textContent = 'Connection error';
    }
    function clearTranscript() {
        document.getElementById('transcript').innerHTML = '';
    }
    </script>
    </body>
    </html>
    """