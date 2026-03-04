from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import date
from app.database.connection import get_db
from app.models.mensalidade import Mensalidade
from app.models.cliente import Cliente
from app.schemas.mensalidade import MensalidadeCreate, MensalidadeUpdate, MensalidadeResponse

router = APIRouter(prefix="/mensalidades", tags=["Mensalidades"])

@router.get("/", response_model=List[MensalidadeResponse])
def listar_mensalidades(
    mes: Optional[str] = None,
    status: Optional[str] = None,
    db: Session = Depends(get_db)
):
    query = db.query(Mensalidade)
    if mes:
        query = query.filter(Mensalidade.mes_referencia == mes)
    if status:
        query = query.filter(Mensalidade.status == status)
    return query.all()

@router.post("/", response_model=MensalidadeResponse)
def criar_mensalidade(dados: MensalidadeCreate, db: Session = Depends(get_db)):
    cliente = db.query(Cliente).filter(Cliente.id == dados.cliente_id).first()
    if not cliente:
        raise HTTPException(status_code=404, detail="Cliente não encontrado")
    mensalidade = Mensalidade(**dados.model_dump())
    db.add(mensalidade)
    db.commit()
    db.refresh(mensalidade)
    return mensalidade

@router.put("/{id}/confirmar")
def confirmar_pagamento(id: int, db: Session = Depends(get_db)):
    mensalidade = db.query(Mensalidade).filter(Mensalidade.id == id).first()
    if not mensalidade:
        raise HTTPException(status_code=404, detail="Mensalidade não encontrada")
    mensalidade.status = "pago"
    mensalidade.validado_por = "admin"
    mensalidade.data_pagamento = date.today().strftime("%d/%m/%Y")
    db.commit()
    db.refresh(mensalidade)
    return {"mensagem": "Pagamento confirmado com sucesso"}

@router.put("/{id}", response_model=MensalidadeResponse)
def atualizar_mensalidade(id: int, dados: MensalidadeUpdate, db: Session = Depends(get_db)):
    mensalidade = db.query(Mensalidade).filter(Mensalidade.id == id).first()
    if not mensalidade:
        raise HTTPException(status_code=404, detail="Mensalidade não encontrada")
    for campo, valor in dados.model_dump(exclude_none=True).items():
        setattr(mensalidade, campo, valor)
    db.commit()
    db.refresh(mensalidade)
    return mensalidade