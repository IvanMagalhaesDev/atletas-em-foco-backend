from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class ClienteBase(BaseModel):
    nome: str
    telefone: str
    dia_vencimento: Optional[int] = None
    ativo: bool = True

class ClienteCreate(ClienteBase):
    pass

class ClienteUpdate(ClienteBase):
    pass

class ClienteResponse(ClienteBase):
    id: int
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True