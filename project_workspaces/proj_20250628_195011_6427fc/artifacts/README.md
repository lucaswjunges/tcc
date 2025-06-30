# Loja Virtual de Eletrônicos

Projeto completo para uma loja virtual de venda de eletrônicos

## Objetivo
Criar uma plataforma de e-commerce completa para venda de produtos eletrônicos, incluindo:
- Catálogo de produtos
- Carrinho de compras
- Processamento de pagamentos
- Sistema de administração

## Tecnologias Utilizadas
- Frontend: React, Tailwind CSS, TypeScript
- Backend: Node.js, Express, MongoDB
- Banco de Dados: MongoDB
- Testes: Jest, Supertest
- Ferramentas: Docker, ESLint, Prettier

## Instalação
### Pré-requisitos
- Node.js v16 ou superior
- MongoDB

### Clone o repositório
```bash
https://github.com/seu_usuario/loja-virtual.git
```

### Instale as dependências
```bash
npm install
```

### Configurações
1. Crie um arquivo `.env` na raiz do projeto com as seguintes variáveis de ambiente:
```env
MONGODB_URI=seu_uri_mongodb
PORT=3000
JWT_SECRET=seu_secreto
```

### Execução
```bash
# Executar o backend
npm run server

# Executar o frontend
npm run client
```

## Uso
### Navegação
1. Acesse `http://localhost:3000`
2. Explore o catálogo de produtos
3. Adicione itens ao carrinho
4. Faça login para ver seu histórico de compras

### Funcionalidades
- Filtrar produtos por categoria
- Ordenar produtos por preço
- Adicionar/remover produtos do carrinho
- Atualizar quantidade de produtos
- Finalizar compra com integração à API de pagamentos

## API Documentação
### Endpoints
#### Produtos
- `GET /api/products` - Lista todos os produtos
- `GET /api/products/:id` - Obtém um produto específico
- `POST /api/products` - Adiciona um novo produto (admin)

#### Categorias
- `GET /api/categories` - Lista todas as categorias

#### Carrinho
- `GET /api/cart` - Obtém o carrinho do usuário
- `PUT /api/cart` - Atualiza o carrinho do usuário

#### Autenticação
- `POST /api/auth/login` - Login do usuário
- `POST /api/auth/register` - Registro de novo usuário

## Estrutura do Projeto
```
├── /client
│   ├── public
│   ├── src
│   │   ├── components
│   │   ├── pages
│   │   ├── services
│   │   ├── utils
│   │   └── App.tsx
├── /server
│   ├── controllers
│   ├── models
│   ├── routes
│   └── app.js
└── /tests
    ├── api
    └── components
```

## Contribuição
Contribua com o projeto aberto issues, reportando bugs ou solicitando features. Siga as diretrizes de contribuição em `CONTRIBUTING.md`

## Licença
Este projeto está sob a licença MIT. Veja o arquivo `LICENSE` para mais detalhes.

## Contato
Para dúvidas ou sugestões, entre em contato pelo e-mail: contato@lojavirtual.com
