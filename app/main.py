from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.database.connection import Base, engine
from app.routers import clientes, mensalidades, dashboard

# Cria as tabelas no banco automaticamente
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Atletas em Foco API",
    description="API para gerenciamento de mensalidades",
    version="1.0.0"
)

# CORS — permite o Angular (localhost:4200) falar com a API
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:4200"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Registra os routers
app.include_router(clientes.router)
app.include_router(mensalidades.router)
app.include_router(dashboard.router)

@app.get("/")
def root():
    return {"mensagem": "Atletas em Foco API está rodando! 🚀"}