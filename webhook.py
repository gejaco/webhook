from fastapi import FastAPI, Request, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse
import json

app = FastAPI()

# Single global transcript (appends from all Omi webhooks)
transcript = []

# List of connected WebSocket clients
connected_clients = []

@app.post("/")
async def webhook_root(request: Request, uid: str | None = None):
    global transcript
    body = await request.json()
    
    print(f"Omi webhook to root: uid={uid}, body={body}")
    
    # Append new segments (same as before)
    transcript.extend(body)
    
    # Broadcast to WebSocket clients
    for client in connected_clients[:]:
        try:
            await client.send_json(transcript)
        except:
            connected_clients.remove(client)
    
    return {"status": "received", "uid": uid, "added": len(body)}


@app.post("/webhook")
async def webhook(request: Request, uid: str = None):  # Accept optional uid query param
    global transcript
    body = await request.json()
    
    print(f"Webhook hit with uid={uid}")  # Log the uid
    print("New segments:", json.dumps(body, indent=2))
    
    # Append new segments
    transcript.extend(body)
    
    # Broadcast to clients...
    for client in connected_clients[:]:
        try:
            await client.send_json(transcript)
        except:
            connected_clients.remove(client)
    
    return {"status": "received", "added": len(body), "uid": uid}

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
    return """<!DOCTYPE html>
<html>
<head>
  <title>Live Omi Transcript</title>
  <style>
    body { font-family: monospace; margin: 20px; background: #f5f5f5; }
    #status { color: green; font-weight: bold; margin-bottom: 10px; }
    #transcript { height: 70vh; border: 1px solid #ddd; padding: 15px; 
                  overflow-y: auto; background: white; white-space: pre-wrap; }
    #debug { font-size: 0.9em; color: #666; margin-top: 10px; }
  </style>
</head>
<body>
  <h1>🔴 Live Omi Transcript</h1>
  <div id="status">Connecting WebSocket...</div>
  <div id="transcript">Waiting for Omi data...</div>
  <div id="debug"></div>

  <script>
    const statusEl = document.getElementById('status');
    const transcriptEl = document.getElementById('transcript');
    const debugEl = document.getElementById('debug');

    // CRITICAL: Use wss:// for Render HTTPS
    const wsUrl = 'wss://' + location.host + '/ws';
    console.log('Connecting to:', wsUrl);

    const ws = new WebSocket(wsUrl);

    ws.onopen = () => {
      statusEl.textContent = '✅ Connected - waiting for Omi...';
      debugEl.textContent = 'WebSocket ready. Send webhook data!';
    };

    ws.onclose = (e) => {
      statusEl.textContent = `❌ Disconnected (code ${e.code})`;
      statusEl.style.color = 'red';
    };

    ws.onerror = (err) => {
      console.error('WebSocket error:', err);
      statusEl.textContent = '❌ Connection failed';
      statusEl.style.color = 'red';
    };

    ws.onmessage = (event) => {
      console.log('📨 Raw WS message:', event.data);
      debugEl.textContent = `Updated at ${new Date().toLocaleTimeString()}`;

      try {
        const data = JSON.parse(event.data);
        console.log('✅ Parsed transcript:', data);

        // Display all segments
        let text = '';
        data.forEach(item => {
          if (typeof item === 'string') text += item + '\\n';
          else if (item.text) text += item.text + '\\n';
          else text += JSON.stringify(item) + '\\n\\n';
        });

        transcriptEl.textContent = text;
        transcriptEl.scrollTop = transcriptEl.scrollHeight;
      } catch (e) {
        console.error('JSON parse error:', e);
      }
    };
  </script>
</body>
</html>"""

