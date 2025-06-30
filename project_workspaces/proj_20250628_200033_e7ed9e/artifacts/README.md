# VapeShop Website

O VapeShop é um website de e-commerce completo para venda de produtos relacionados a vapes e pods. Este projeto foi desenvolvido para oferecer uma experiência de compra intuitiva, estilosa e responsiva.

## Índice
- [Instalação](#instalação)
- [Uso](#uso)
- [API Docs](#api-docs)
- [Estrutura do Projeto](#estrutura-do-projeto)
- [Contribuição](#contribuição)
- [Licença](#licença)

## Instalação
### Via Docker
Este projeto é facilmente executável através de Docker. Siga os passos abaixo:

1. Clone o repositório:
   ```bash
   git clone https://github.com/seu_usuario/vapeshop.git
   cd vapeshop
   ```

2. Construa e execute o container Docker:
   ```bash
   docker-compose up --build
   ```

Isso irá construir as imagens necessárias e iniciar o serviço web no endereço `http://localhost:3000`

### Instalação Manual
Se preferir uma instalação manual (requer Node.js v14+):

1. Instale as dependências do frontend e backend
2. Configure suas variáveis de ambiente
3. Inicie os serviços

## Uso
### Navegação
- **Homepage**: Exibe produtos em destaque
- **Categorias**: Produtos organizados por categoria (Vapes, Pods, Acessórios)
- **Detalhes do Produto**: Informações completas sobre cada item
- **Carrinho**: Gerenciamento de itens selecionados
- **Checkout**: Processo de finalização da compra

### Funcionalidades
- Busca de produtos
- Filtros por categoria e preço
- Pagamento com cartão
- Histórico de pedidos

## API Docs
A API foi desenvolvida com Node.js e Express. As documentações podem ser encontradas em:

- **Swagger UI**: http://localhost:3001/api-docs
- **OpenAPI JSON**: http://localhost:3001/openapi.json

### Endpoints Principais
```http
GET /api/products
GET /api/products/:id
POST /api/carts
PUT /api/carts/:id
POST /api/orders
GET /api/orders
```

## Estrutura do Projeto
```
projeto-root/              
├── frontend/              
│   ├── public/            
│   ├── src/               
│   │   ├── components/    
│   │   ├── pages/         
│   │   ├── services/      
│   │   └── App.jsx        
│   └── package.json       
├── backend/               
│   ├── config/            
│   ├── controllers/       
│   ├── models/            
│   ├── routes/            
│   └── app.js             
├── docker-compose.yml    
└── README.md              
```

## Contribuição
Contribua melhorando este README e o próprio projeto! Abra issues ou envie pull requests.

## Licença
MIT

---
Este README foi gerado automaticamente. Mantenha-o atualizado conforme o desenvolvimento do projeto avança.