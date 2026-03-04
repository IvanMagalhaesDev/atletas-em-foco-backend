from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database.connection import Base

class Mensalidade(Base):
    __tablename__ = "mensalidades"

    id              = Column(Integer, primary_key=True, index=True)
    cliente_id      = Column(Integer, ForeignKey("clientes.id"), nullable=False)
    mes_referencia  = Column(String, nullable=False)   # ex: "03/2025"
    data_vencimento = Column(String, nullable=False)   # ex: "05/03/2025"
    data_pagamento  = Column(String, nullable=True)    # null se não pago
    valor           = Column(Float, default=150.0)
    status          = Column(String, default="pendente")  # pago | pendente | atrasado
    validado_por    = Column(String, nullable=True)       # auto | admin | null

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    cliente = relationship("Cliente", backref="mensalidades")