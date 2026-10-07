from sqlalchemy import Column, Integer, String
from database import Base
from pydantic import BaseModel
from typing import Optional

# --- Modelos SQLAlchemy (Banco de Dados) ---
class SwitchDevice(Base):
    __tablename__ = "switches"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)
    host = Column(String, unique=True, index=True)
    port = Column(Integer, default=22)
    default_user = Column(String, default="admin")


class Macro(Base):
    __tablename__ = "macros"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String)
    command = Column(String)


# --- Schemas Pydantic (Validação da API) ---
class SwitchCreate(BaseModel):
    name: str
    host: str
    port: int = 22
    default_user: str = "admin"

class SwitchOut(SwitchCreate):
    id: int
    class Config:
        from_attributes = True

class MacroCreate(BaseModel):
    name: str
    command: str

class MacroOut(MacroCreate):
    id: int
    class Config:
        from_attributes = True