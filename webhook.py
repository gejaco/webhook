from fastapi import FastAPI, Request, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse
import json

app = FastAPI()

# Single global transcript (appends from all Omi webhooks)
transcript = []

# List of connected WebSocket clients
connected_clients = []

@app.post("/webhook")
async def webhook(request: Request, uid: str = Query(None)):  # Accept optional uid query param
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
    return """
<!DOCTYPE html>
<html>
<head>
  <meta charset="utf-8" />
  <title>Live Transcript</title>
  <style>
    body { font-family: sans-serif; margin: 20px; }
    #status { margin-bottom: 10px; color: green; }
    #transcript { width: 100%; height: 80vh; white-space: pre-wrap;
                  border: 1px solid #ccc; padding: 10px; overflow-y: auto; font-family: monospace; }
    #debug { margin-top: 10px; font-size: 0.8em; color: #666; }
  </style>
</head>
<body>
  <h1>Live Transcript</h1>
  <div id="status">Connecting...</div>
  <div id="transcript">Waiting for data...</div>
  <div id="debug"></div>

  <script>
    const statusEl = document.getElementById('status');
    const transcriptEl = document.getElementById('transcript');
    const debugEl = document.getElementById('debug');

    // Force ws:// for Render
    const wsUrl = 'ws://' + location.host + '/ws';
    const ws = new WebSocket(wsUrl);

    ws.onopen = () => {
      statusEl.textContent = 'Connected to ' + wsUrl;
      debugEl.textContent = 'Ready for webhook data...';
    };

    ws.onclose = (event) => {
      statusEl.textContent = `Disconnected (code: ${event.code})`;
      statusEl.style.color = 'red';
    };

    ws.onerror = (err) => {
      console.error('WebSocket error:', err);
      debugEl.textContent = 'WebSocket error occurred';
      statusEl.style.color = 'red';
    };

    ws.onmessage = (event) => {
      console.log('Raw message received:', event.data);  // Check browser console!
      debugEl.textContent = `Msg at ${new Date().toLocaleTimeString()}`;

      let data;
      try {
        data = JSON.parse(event.data);
        console.log('Parsed data:', data);
      } catch (e) {
        console.error('JSON parse failed:', e);
        return;
      }

      // Build display text from array of strings/objects
      let displayText = '';
      for (const item of data) {
        if (typeof item === 'string') {
          displayText += item + '\n';
        } else if (item && typeof item.text === 'string') {
          displayText += item.text + '\n';
        } else {
          displayText += JSON.stringify(item, null, 2) + '\n\n';
        }
      }

      transcriptEl.textContent = displayText;
      transcriptEl.scrollTop = transcriptEl.scrollHeight;
    };
  </script>
</body>
</html>
"""
