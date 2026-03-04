from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from app.database.connection import get_db
from app.models.cliente import Cliente
from app.schemas.cliente import ClienteCreate, ClienteUpdate, ClienteResponse

router = APIRouter(prefix="/clientes", tags=["Clientes"])

@router.get("/", response_model=List[ClienteResponse])
def listar_clientes(busca: str = "", db: Session = Depends(get_db)):
    query = db.query(Cliente)
    if busca:
        query = query.filter(
            Cliente.nome.ilike(f"%{busca}%") |
            Cliente.cpf.ilike(f"%{busca}%")
        )
    return query.all()

@router.get("/{id}", response_model=ClienteResponse)
def buscar_cliente(id: int, db: Session = Depends(get_db)):
    cliente = db.query(Cliente).filter(Cliente.id == id).first()
    if not cliente:
        raise HTTPException(status_code=404, detail="Cliente não encontrado")
    return cliente

@router.post("/", response_model=ClienteResponse)
def criar_cliente(dados: ClienteCreate, db: Session = Depends(get_db)):
    cpf_existe = db.query(Cliente).filter(Cliente.cpf == dados.cpf).first()
    if cpf_existe:
        raise HTTPException(status_code=400, detail="CPF já cadastrado")
    cliente = Cliente(**dados.model_dump())
    db.add(cliente)
    db.commit()
    db.refresh(cliente)
    return cliente

@router.put("/{id}", response_model=ClienteResponse)
def atualizar_cliente(id: int, dados: ClienteUpdate, db: Session = Depends(get_db)):
    cliente = db.query(Cliente).filter(Cliente.id == id).first()
    if not cliente:
        raise HTTPException(status_code=404, detail="Cliente não encontrado")
    for campo, valor in dados.model_dump().items():
        setattr(cliente, campo, valor)
    db.commit()
    db.refresh(cliente)
    return cliente

@router.delete("/{id}")
def excluir_cliente(id: int, db: Session = Depends(get_db)):
    cliente = db.query(Cliente).filter(Cliente.id == id).first()
    if not cliente:
        raise HTTPException(status_code=404, detail="Cliente não encontrado")
    db.delete(cliente)
    db.commit()
    return {"mensagem": "Cliente excluído com sucesso"}