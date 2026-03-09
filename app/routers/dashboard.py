from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.database.connection import get_db
from app.models.mensalidade import Mensalidade
from app.models.cliente import Cliente

router = APIRouter(prefix="/dashboard", tags=["Dashboard"])

@router.get("/resumo")
def resumo_dashboard(db: Session = Depends(get_db)):
    from datetime import date
    mes_atual = date.today().strftime("%m/%Y")

    total_clientes = db.query(Cliente).filter(Cliente.ativo == True).count()
    
    pagos = db.query(Mensalidade).filter(
        Mensalidade.status == "pago",
        Mensalidade.mes_referencia == mes_atual
    ).count()
    
    pendentes = db.query(Mensalidade).filter(
        Mensalidade.status == "pendente",
        Mensalidade.mes_referencia == mes_atual
    ).count()
    
    atrasados = db.query(Mensalidade).filter(
        Mensalidade.status == "atrasado",
        Mensalidade.mes_referencia == mes_atual
    ).count()

    receita = db.query(Mensalidade).filter(
        Mensalidade.status == "pago",
        Mensalidade.mes_referencia == mes_atual
    ).all()
    total_receita = sum(m.valor for m in receita)

    return {
        "total_clientes": total_clientes,
        "pagos": pagos,
        "pendentes": pendentes,
        "atrasados": atrasados,
        "receita": total_receita
    }

@router.get("/grafico")
def grafico_dashboard(db: Session = Depends(get_db)):
    from sqlalchemy import func
    
    resultado = db.query(
        Mensalidade.mes_referencia,
        func.count(Mensalidade.id).label("total"),
        func.sum(Mensalidade.valor).label("receita")
    ).filter(
        Mensalidade.status == "pago"
    ).group_by(
        Mensalidade.mes_referencia
    ).order_by(
        Mensalidade.mes_referencia
    ).all()

    return [
        {
            "mes": r.mes_referencia,
            "total": r.total,
            "receita": float(r.receita or 0)
        }
        for r in resultado
    ]