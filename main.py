import asyncio
import logging
from pathlib import Path
from typing import List, Optional

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Depends, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from sqlalchemy import create_engine, Column, Integer, String
from sqlalchemy.orm import declarative_base, sessionmaker, Session
from netmiko import ConnectHandler
from fastapi.responses import FileResponse

# --- CONFIGURAÇÃO DE LOGS ---
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("terminal-app")

# --- BASE DE DADOS SQLITE (CAMINHO ABSOLUTO) ---
BASE_DIR = Path(__file__).resolve().parent
DB_PATH = BASE_DIR / "terminal_data.db"
SQLALCHEMY_DATABASE_URL = f"sqlite:///{DB_PATH}"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False}
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# --- MODELOS SQLALCHEMY ---
class SwitchDevice(Base):
    __tablename__ = "switches"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    host = Column(String, unique=True, nullable=False)
    port = Column(Integer, default=22)
    default_user = Column(String, default="admin")

class Macro(Base):
    __tablename__ = "macros"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    command = Column(String, nullable=False)

# Criação automática das tabelas
Base.metadata.create_all(bind=engine)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# --- SCHEMAS PYDANTIC (COMPATÍVEIS COM V1 E V2) ---
class SwitchCreate(BaseModel):
    name: str
    host: str
    port: int = 22
    default_user: str = "admin"

class SwitchOut(SwitchCreate):
    id: int
    class Config:
        orm_mode = True
        from_attributes = True

class MacroCreate(BaseModel):
    name: str
    command: str

class MacroOut(MacroCreate):
    id: int
    class Config:
        orm_mode = True
        from_attributes = True

# --- INICIALIZAÇÃO FASTAPI ---
app = FastAPI(title="Huawei Terminal Gateway")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- ROTAS REST: SWITCHES ---
@app.get("/api/switches", response_model=List[SwitchOut])
def list_switches(db: Session = Depends(get_db)):
    return db.query(SwitchDevice).all()

@app.post("/api/switches", response_model=SwitchOut, status_code=status.HTTP_201_CREATED)
def create_switch(item: SwitchCreate, db: Session = Depends(get_db)):
    exist = db.query(SwitchDevice).filter(SwitchDevice.host == item.host).first()
    if exist:
        raise HTTPException(status_code=400, detail=f"O switch com o IP {item.host} já está registado.")
    
    device = SwitchDevice(
        name=item.name,
        host=item.host,
        port=item.port,
        default_user=item.default_user
    )
    try:
        db.add(device)
        db.commit()
        db.refresh(device)
        logger.info(f"Switch guardado com sucesso: {device.name} ({device.host})")
        return device
    except Exception as e:
        db.rollback()
        logger.error(f"Erro ao guardar switch: {e}")
        raise HTTPException(status_code=500, detail="Erro ao persistir na base de dados.")

@app.delete("/api/switches/{switch_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_switch(switch_id: int, db: Session = Depends(get_db)):
    item = db.query(SwitchDevice).filter(SwitchDevice.id == switch_id).first()
    if not item:
        raise HTTPException(status_code=404, detail="Switch não encontrado.")
    db.delete(item)
    db.commit()

# --- ROTAS REST: MACROS ---
@app.get("/api/macros", response_model=List[MacroOut])
def list_macros(db: Session = Depends(get_db)):
    macros = db.query(Macro).all()
    if not macros:
        defaults = [
            Macro(name="Ver Versão", command="display version"),
            Macro(name="IP Interfaces", command="display ip interface brief"),
            Macro(name="Descrição Interfaces", command="display interface description"),
            Macro(name="VLANs Ativas", command="display vlan"),
            Macro(name="CPU Usage", command="display cpu-usage"),
            Macro(name="System Mode", command="system-view")
        ]
        db.add_all(defaults)
        db.commit()
        macros = db.query(Macro).all()
    return macros

@app.post("/api/macros", response_model=MacroOut, status_code=status.HTTP_201_CREATED)
def create_macro(item: MacroCreate, db: Session = Depends(get_db)):
    macro = Macro(name=item.name, command=item.command)
    try:
        db.add(macro)
        db.commit()
        db.refresh(macro)
        return macro
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail="Erro ao guardar macro.")

@app.delete("/api/macros/{macro_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_macro(macro_id: int, db: Session = Depends(get_db)):
    macro = db.query(Macro).filter(Macro.id == macro_id).first()
    if not macro:
        raise HTTPException(status_code=404, detail="Macro não encontrada.")
    db.delete(macro)
    db.commit()

# --- WEBSOCKET TERMINAL (NETMIKO) ---
async def pipe_netmiko_to_websocket(net_connect, websocket: WebSocket):
    loop = asyncio.get_running_loop()
    try:
        while True:
            data = await loop.run_in_executor(None, net_connect.read_channel)
            if data:
                await websocket.send_text(data)
            else:
                await asyncio.sleep(0.02)
    except Exception as e:
        logger.warning(f"Leitura SSH encerrada: {e}")

async def pipe_websocket_to_netmiko(websocket: WebSocket, net_connect):
    loop = asyncio.get_running_loop()
    try:
        while True:
            text = await websocket.receive_text()
            await loop.run_in_executor(None, net_connect.write_channel, text)
    except WebSocketDisconnect:
        logger.info("Cliente fechou a ligação WebSocket.")
    except Exception as e:
        logger.warning(f"Erro no envio WS -> Netmiko: {e}")

@app.websocket("/ws/terminal")
async def terminal_websocket(
    websocket: WebSocket,
    host: str,
    username: str,
    password: str,
    port: int = 22,
):
    await websocket.accept()

    device_params = {
        "device_type": "huawei",
        "host": host,
        "username": username,
        "password": password,
        "port": port,
        "fast_cli": False,
        "global_delay_factor": 1,
        "conn_timeout": 20,
        "banner_timeout": 20,
        "auth_timeout": 20,
        "disabled_algorithms": {},
    }

    net_connect = None
    try:
        logger.info(f"A ligar ao switch {host}:{port}...")
        loop = asyncio.get_running_loop()
        net_connect = await loop.run_in_executor(
            None, lambda: ConnectHandler(**device_params)
        )
        net_connect.write_channel("\n")
    except Exception as e:
        logger.error(f"Erro ao ligar ao switch: {e}")
        await websocket.send_text(f"\r\n\x1b[31m[Erro de Ligação]: {str(e)}\x1b[0m\r\n")
        await websocket.close()
        return

    read_task = asyncio.create_task(pipe_netmiko_to_websocket(net_connect, websocket))
    write_task = asyncio.create_task(pipe_websocket_to_netmiko(websocket, net_connect))

    done, pending = await asyncio.wait(
        [read_task, write_task],
        return_when=asyncio.FIRST_COMPLETED,
    )

    for task in pending:
        task.cancel()

    if net_connect:
        try:
            await loop.run_in_executor(None, net_connect.disconnect)
        except Exception:
            pass

    try:
        await websocket.close()
    except Exception:
        pass
    logger.info("Sessão finalizada.")
    

@app.get("/")
def serve_index():
    return FileResponse("index.html")


from fastapi.responses import FileResponse

@app.get('/favicon.ico', include_in_schema=False)
async def favicon():
    return FileResponse("app.ico")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000)