from sqlalchemy import Column, Integer, String, Boolean, DateTime
from sqlalchemy.sql import func
from app.database.connection import Base

class Cliente(Base):
    __tablename__ = "clientes"

    id              = Column(Integer, primary_key=True, index=True)
    nome            = Column(String, nullable=False)
    cpf             = Column(String, unique=True, nullable=False)
    whatsapp        = Column(String, nullable=False)
    data_nascimento = Column(String, nullable=True)
    dia_vencimento  = Column(Integer, nullable=True)
    ativo           = Column(Boolean, default=True)
    created_at      = Column(DateTime(timezone=True), server_default=func.now())
    updated_at      = Column(DateTime(timezone=True), onupdate=func.now())