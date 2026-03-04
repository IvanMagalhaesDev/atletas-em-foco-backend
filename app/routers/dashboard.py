from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.database.connection import get_db
from app.models.mensalidade import Mensalidade
from app.models.cliente import Cliente

router = APIRouter(prefix="/dashboard", tags=["Dashboard"])

@router.get("/resumo")
def resumo_dashboard(db: Session = Depends(get_db)):
    total_clientes = db.query(Cliente).filter(Cliente.ativo == True).count()
    pagos     = db.query(Mensalidade).filter(Mensalidade.status == "pago").count()
    pendentes = db.query(Mensalidade).filter(Mensalidade.status == "pendente").count()
    atrasados = db.query(Mensalidade).filter(Mensalidade.status == "atrasado").count()

    receita = db.query(Mensalidade).filter(
        Mensalidade.status == "pago"
    ).all()
    total_receita = sum(m.valor for m in receita)

    return {
        "total_clientes": total_clientes,
        "pagos":     pagos,
        "pendentes": pendentes,
        "atrasados": atrasados,
        "receita":   total_receita
    }