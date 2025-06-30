# VapeShop - Website de Vendas de Vapes e Pods

> Loja completa para venda de vaporizadores eletrônicos e pods personalizáveis

## Índice
1. [Visão Geral](#visão-geral)
2. [Instalação](#instalação)
3. [Estrutura do Projeto](#estrutura-do-projeto)
4. [Configuração Inicial](#configuração-inicial)
5. [Modelagem do Banco de Dados](#modelagem-do-banco-de-dados)
6. [Rotas e Funcionalidades](#rotas-e-funcionalidades)
7. [Layout e Estilização](#layout-e-estilização)
8. [Adicionando Produtos](#adicionando-produtos)
9. [Pagamentos e Carrinhos](#pagamentos-e-carrinhos)
10. [Deploy](#deploy)

## Visão Geral
O VapeShop é um e-commerce completo desenvolvido em Python utilizando:
- **FastAPI**: Framework para desenvolvimento de APIs
- **React** (via React + Vite): Interface do usuário
- **MongoDB**: Banco de dados NoSQL
- **Stripe**: Processamento de pagamentos

O sistema inclui:
- Catálogo de produtos com filtros
- Carrinho de compras
- Checkout com Stripe
- Administração de produtos
- Estatísticas de vendas

## Instalação
### Pré-requisitos
- Python 3.9+
- Node.js v16+
- MongoDB instalado e rodando

### Instalação do Backend (FastAPI)
```bash
# Clone o repositório
git clone https://github.com/seu_usuario/vapeshop.git

cd vapeshop/backend

# Instale as dependências
pip install -r requirements.txt

# Execute o servidor
uvicorn main:app --reload
```

### Instalação do Frontend (React)
```bash
cd ../frontend
npm install
npm run dev
```

## Estrutura do Projeto
```
├── README.md
├── backend/                # Pasta do backend FastAPI
│   ├── main.py            # Ponto de entrada da API
│   ├── models/            # Modelos de dados
│   ├── routers/           # Rotas da API
│   ├── services/          # Serviços de negócio
│   └── database.py        # Conexão com MongoDB
├── frontend/               # Pasta do frontend React
│   ├── public/            # Arquivos estáticos
│   ├── src/               # Código da aplicação
│   │   ├── components/    # Componentes reutilizáveis
│   │   ├── pages/         # Páginas da aplicação
│   │   ├── services/      # Chamadas API
│   │   └── App.jsx        # Componente principal
└── docker-compose.yml     # Configuração do Docker
```

## Configuração Inicial
### Configuração do MongoDB
Crie um arquivo `.env` na raiz do projeto com as seguintes variáveis:
```.env
MONGO_URI=mongodb://localhost:27017/vapeshop
STRIPE_KEY=chave_da_stripe
ADMIN_EMAIL=admin@vapeshop.com
```

### Configuração do Stripe
1. Crie uma conta no [Stripe](https://stripe.com/)
2. No painel, vá em **Developers > API Keys** e copie as chaves
3. Adicione à variável de ambiente `STRIPE_KEY`

## Modelagem do Banco de Dados
### Estrutura do Produto
```json
{
  "_id": "",
  "name": "Vape XYZ",
  "brand": "Marca",
  "description": "Vape com liquidificador automático",
  "price": 199.99,
  "category": "Vapes",
  "specs": {
    "battery": "3000mAh",
    "resistance": "0.8 ohms",
    "color": "preto"
  },
  "stock": 10
}
```

### Estrutura do Pedido
```json
{
  "_id": "",
  "user": "",
  "products": ["prod1", "prod2"],
  "total": 349.98,
  "status": "pending",
  "payment_intent": "int_1YZX..."
}
```

## Rotas e Funcionalidades
### Backend (FastAPI)
**Rotas de Produtos**
- `GET /products` - Lista produtos
- `POST /products` - Adiciona novo produto
- `PUT /products/:id` - Atualiza produto
- `DELETE /products/:id` - Remove produto

**Rotas de Pedidos**
- `POST /orders` - Cria novo pedido
- `GET /orders` - Lista todos os pedidos
- `GET /orders/:id` - Detalhes do pedido

### Frontend (React)
**Páginas**
- Home: Produtos em destaque
- Catálogo: Todos os produtos filtrados por categoria
- Carrinho: Gerenciamento de itens
- Checkout: Finalização com Stripe

## Adicionando Produtos
1. Acesse a API `/admin/products`
2. Faça um POST com os dados do produto
3. Autenticação (a ser implementada)

Exemplo:
```bash
curl -X POST "http://localhost:8000/products" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Pod XYZ",
    "brand": "XYZ",
    "description": "Pod com 300mg de e-liquido",
    "price": 49.99,
    "category": "Pods",
    "specs": {
      "capacity": "1.5ml",
      "resistance": "1.2 ohms"
    }
  }'
```

## Pagamentos e Carrinhos
### Carrinho de Compras
O carrinho é armazenado no `localStorage` do navegador. Para sincronizar com o backend:
```javascript
// Adicionando item ao carrinho
const addToCart = (product) => {
  const existingItem = cart.find(item => item.product === product._id);
  if (existingItem) {
    existingItem.quantity += 1;
  } else {
    cart.push({ product, quantity: 1 });
  }
  localStorage.setItem('cart', JSON.stringify(cart));
};
```

### Integração com Stripe
1. No checkout, envie a lista de produtos para a API
2. API cria um `payment_intent` via Stripe
3. Redirecione o usuário para a página de pagamento
4. Após aprovação, atualize o pedido no banco de dados

## Deploy
### Usando Docker
```bash
docker-compose build
docker-compose up -d
```

### No Servidor
1. Instale o Docker no servidor
2. Execute o comando de build e up
3. Configure Nginx como proxy reverso
4. Configurar o firewall e SSH

## Exemplos Específicos
### Produtos Populares
```json
[{
  "name": "Vape ProMax",
  "price": 249.99,
  "specs": {
    "battery": "5000mAh",
    "type": "mod"
  }
}, {
  "name": "Pod Mini",
  "price": 39.99,
  "specs": {
    "capacity": "0.7ml",
    "type": "pod"
  }
}]
```

### Estatísticas de Vendas
```python
from datetime import datetime, timedelta
from pymongo import MongoClient

# Conecte ao MongoDB
client = MongoClient(os.getenv('MONGO_URI'))

# Calcule as últimas 7 vendas
today = datetime.now()
last_week = today - timedelta(days=7)

pipeline = [
    {"$match": {"created_at": {"$gte": last_week}}},
    {"$group": {_id: "$category", total_sales: {"$sum": 1}, revenue: {"$sum": "$total"}}}
]

result = client.vapeshop.orders.aggregate(pipeline)
```

## Licença
MIT

## Contato
Email: dev@vapeshop.com
GitHub: https://github.com/seu_usuario/vapeshop
