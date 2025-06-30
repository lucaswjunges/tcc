from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List

app = FastAPI(title='VapeCannabis API', description='API para gerenciamento de produtos de vapes e pods')

# Modelo de Produto
class Produto(BaseModel):
    id: int
    nome: str
    tipo: str  # vape, pod, atomizador
    preco: float
    descricao: str
    estoque: int
    thc_percentual: float = 0.0
    cbd_percentual: float = 0.0

# Banco de dados simulado
produtos = [
    Produto(
        id=1, 
        nome='VapePro Canabis X1', 
        tipo='vape', 
        preco=299.90, 
        descricao='Vaporizador premium para óleos canábicos', 
        estoque=50,
        thc_percentual=0.3,
        cbd_percentual=15.0
    ),
    Produto(
        id=2, 
        nome='PodCann Intense', 
        tipo='pod', 
        preco=149.90, 
        descricao='Pod compacto para extratos medicinais', 
        estoque=75,
        thc_percentual=0.2,
        cbd_percentual=20.0
    )
]

# Rotas de Produtos
@app.get('/produtos', response_model=List[Produto])
def listar_produtos():
    return produtos

@app.get('/produtos/{produto_id}', response_model=Produto)
def buscar_produto(produto_id: int):
    produto = next((p for p in produtos if p.id == produto_id), None)
    if not produto:
        raise HTTPException(status_code=404, detail='Produto não encontrado')
    return produto

@app.post('/produtos', response_model=Produto)
def criar_produto(produto: Produto):
    produto.id = len(produtos) + 1
    produtos.append(produto)
    return produto

@app.put('/produtos/{produto_id}', response_model=Produto)
def atualizar_produto(produto_id: int, produto: Produto):
    for index, p in enumerate(produtos):
        if p.id == produto_id:
            produto.id = produto_id
            produtos[index] = produto
            return produto
    raise HTTPException(status_code=404, detail='Produto não encontrado')

@app.delete('/produtos/{produto_id}', status_code=204)
def remover_produto(produto_id: int):
    global produtos
    produtos = [p for p in produtos if p.id != produto_id]
    return None

# Inicialização do servidor
if __name__ == '__main__':
    import uvicorn
    uvicorn.run(app, host='0.0.0.0', port=8000)
