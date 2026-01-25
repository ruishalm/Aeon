import os
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse

# --- CRIAÇÃO DO APP (O UVICORN PROCURA ISSO AQUI) ---
app = FastAPI(title="Aeon API Core")

# Permissões de Rede
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Gerenciador de Conexões WebSocket
class ConnectionManager:
    def __init__(self):
        self.active_connections: list[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)
        print(f"✅ Novo dispositivo conectado.")

    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)
        print(f"❌ Dispositivo desconectado.")

    async def broadcast(self, message: str):
        for connection in self.active_connections:
            await connection.send_text(message)

manager = ConnectionManager()

# --- ROTAS ---

@app.get("/")
async def get_interface():
    # Garante que acha o arquivo mesmo se rodar de fora
    return FileResponse(os.path.join("interface", "index.html"))

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        while True:
            data = await websocket.receive_text()
            print(f"📩 Recebido: {data}")
            
            # Lógica simples de resposta
            if "tarot" in data.lower():
                resp = "🔮 Aeon: As cartas estão sendo embaralhadas..."
            else:
                resp = f"Aeon Ouviu: {data}"
                
            await manager.broadcast(resp)
    except WebSocketDisconnect:
        manager.disconnect(websocket)

# Serve os arquivos da pasta interface (CSS, JS)
app.mount("/", StaticFiles(directory="interface"), name="static")