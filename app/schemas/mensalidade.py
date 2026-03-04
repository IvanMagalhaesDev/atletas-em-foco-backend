from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class MensalidadeBase(BaseModel):
    cliente_id: int
    mes_referencia: str
    data_vencimento: str
    valor: float = 150.0
    status: str = "pendente"

class MensalidadeCreate(MensalidadeBase):
    pass

class MensalidadeUpdate(BaseModel):
    status: Optional[str] = None
    data_pagamento: Optional[str] = None
    validado_por: Optional[str] = None

class MensalidadeResponse(MensalidadeBase):
    id: int
    data_pagamento: Optional[str] = None
    validado_por: Optional[str] = None
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True