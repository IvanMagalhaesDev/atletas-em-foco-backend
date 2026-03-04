from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class ClienteBase(BaseModel):
    nome: str
    cpf: str
    whatsapp: str
    data_nascimento: Optional[str] = None
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