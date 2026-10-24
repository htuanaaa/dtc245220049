import os
import html
import asyncpg
from datetime import datetime
from contextlib import asynccontextmanager
from prometheus_client import Counter, Gauge
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from prometheus_fastapi_instrumentator import Instrumentator


DATABASE_URL = os.getenv("DATABASE_URL")
db_pool: asyncpg.Pool | None = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    global db_pool
    db_pool = await asyncpg.create_pool(dsn=DATABASE_URL, min_size=2, max_size=10)
    async with db_pool.acquire() as conn:
        await conn.execute("""
            create table if not exists messages (
                id serial primary key,
                room_id varchar(50) not null,
                sender varchar(100) not null,
                content text not null,
                created_at timestamp with time zone default now()
            );
            create index if not exists idx_messages_room_id on messages (room_id);
        """)
    yield
    await db_pool.close()

app = FastAPI(lifespan=lifespan)

ws_active_connections = Gauge(
    "websocket_active_connections",
    "so luong client websocket dang duy tri ket noi thuc te"
)

ws_messages_total = Counter(
    "websocket_messages_total",
    "tong so tin nhan chat xu ly qua websocket",
    ["direction"]
)

ws_connection_events_total = Counter(
    "websocket_connection_events_total",
    "tong so su kien ket noi hoac ngat ket noi",
    ["event"]
)

Instrumentator().instrument(app).expose(app)

class ConnectionManager:
    def __init__(self):
        self.rooms: dict[str, dict[WebSocket, str]] = {}

    async def connect(self, room_id: str, websocket: WebSocket, username: str):
        await websocket.accept()
        if room_id not in self.rooms:
            self.rooms[room_id] = {}
        self.rooms[room_id][websocket] = username

    def disconnect(self, room_id: str, websocket: WebSocket):
        if room_id in self.rooms and websocket in self.rooms[room_id].keys():
            del self.rooms[room_id][websocket]
            if not self.rooms[room_id]:
                del self.rooms[room_id]

    async def broadcast(self, room_id: str, data: dict, exclude: WebSocket | None = None):
        if room_id in self.rooms:
            for client in list(self.rooms[room_id].keys()):
                if client != exclude:
                    await client.send_json(data)

manager = ConnectionManager()

@app.websocket("/ws/{room_id}")
async def websocket_endpoint(websocket: WebSocket, room_id: str, username: str):
    await manager.connect(room_id, websocket, username)
    async with db_pool.acquire() as conn:
        rows = await conn.fetch(
            """
                select sender, content, to_char(created_at, 'HH24:MI') as time
                from messages
                where room_id = $1
                order by id desc
                limit 50
            """,
            room_id
        )
        history = [dict(row) for row in reversed(rows)]
        await websocket.send_json({"type": "history", "messages": history})

    await manager.broadcast(room_id, {
        "type": "system",
        "content": f"{username} đã tham gia phòng {room_id}"
    }, exclude=websocket)

    ws_active_connections.inc()
    ws_connection_events_total.labels(event="connect").inc()

    try:
        while True:
            data = await websocket.receive_json()
            ws_messages_total.labels(direction="in").inc()
            event_type = data.get("type")

            if event_type == "chat":
                raw_text = data.get("content", "").strip()
                # clean_content = html.escape(raw_text)[:1000]
                current_time = datetime.now().strftime("%H:%M")
                async with db_pool.acquire() as conn:
                    row = await conn.fetchrow(
                        """
                            insert into messages (room_id, sender, content)
                            values ($1, $2, $3)
                            returning to_char(created_at, 'HH24:MI') as time
                        """,
                        room_id,
                        username,
                        raw_text    # clean_content
                    )
                await manager.broadcast(room_id, {
                    "type": "chat",
                    "sender": username,
                    "content": raw_text,    # clean_content
                    "time": current_time
                })
                ws_messages_total.labels(direction="out").inc()
            elif event_type == "typing":
                await manager.broadcast(room_id, {
                    "type": "typing",
                    "sender": username
                }, exclude=websocket)
    except WebSocketDisconnect:
        manager.disconnect(room_id, websocket)
        await manager.broadcast(room_id, {
            "type": "system",
            "content": f"{username} đã rời khỏi phòng {room_id}"
        })
        ws_active_connections.dec()
        ws_connection_events_total.labels(event="disconnect").inc()
    except Exception as e:
        manager.disconnect(room_id, websocket)
