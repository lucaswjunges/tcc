from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

app = FastAPI()

# Modelo de dados para Produto
class Produto(BaseModel):
    id: int
    nome: str
    marca: str
    preco: float
    tipo: str  # vape ou pod

# Banco de dados simulado
produtos = [
    Produto(id=1, nome="Vape Classic", marca="VaporTech", preco=129.99, tipo="vape"),
    Produto(id=2, nome="Pod Slim", marca="PodMaster", preco=89.50, tipo="pod")
]

@app.get("/")
def hello_world():
    return {"message": "API de Gerenciamento de Vapes e Pods"}

@app.get("/produtos")
def listar_produtos():
    return produtos

@app.get("/produtos/{produto_id}")
def obter_produto(produto_id: int):
    produto = next((p for p in produtos if p.id == produto_id), None)
    if produto is None:
        raise HTTPException(status_code=404, detail="Produto não encontrado")
    return produto
