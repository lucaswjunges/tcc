# VapeShop - Website de Vendas de Acessórios de Vape

Este repositório contém todos os arquivos necessários para criar um website completo de vendas de vapes e pods funcional, estiloso e completo usando Python.

## Conteúdo

O projeto inclui:
- Frontend responsivo com design moderno
- Backend com funcionalidades de gerenciamento de produtos, carrinho e checkout
- Sistema de autenticação de usuários
- Admin panel para gerenciamento de produtos e pedidos

## Pré-requisitos

Antes de iniciar, você precisará:

- Python 3.8 ou superior
- Node.js (para o frontend)
- Banco de dados preferencialmente PostgreSQL

## Instalação

Siga estas etapas para configurar o projeto:

1. Clone este repositório:
   ```bash
   git clone https://github.com/seu_usuario/vapeshop.git
   cd vapeshop
   ```

2. Crie e ative um ambiente virtual:
   ```bash
   python -m venv venv
   source venv/bin/activate  # Linux/Mac
   venv\Scripts\activate  # Windows
   ```

3. Instale as dependências:
   ```bash
   pip install -r requirements.txt
   npm install
   ```

4. Configure o banco de dados:
   - Crie um arquivo `.env` na raiz do projeto com suas variáveis de ambiente
   - Exemplo do conteúdo do `.env`:
     ```
     DATABASE_URL=postgresql://user:password@localhost:5432/vapeshop_db
     SECRET_KEY=seu_secreto_secreto
     DEBUG=True
     ```

5. Migrate e crie o superusuário:
   ```bash
   python manage.py db init
   python manage.py db upgrade
   python manage.py createsuperuser
   ```

## Executando o Projeto

### Backend (Python)
```bash
python manage.py runserver
```

### Frontend (React)
```bash
cd frontend

npm start
```

## Estrutura do Projeto

```
├── vapeshop/                   # Pasta principal do projeto
│   ├── app/                   # Aplicação Flask
│   │   ├── __init__.py       # Configuração principal
│   │   ├── routes.py         # Rotas da aplicação
│   │   ├── models.py         # Modelos do banco de dados
│   │   └── services.py       # Serviços do backend
│   ├── frontend/              # Frontend React
│   │   ├── public/           # Arquivos estáticos
│   │   ├── src/              # Código da aplicação
│   │   │   ├── components/   # Componentes reutilizáveis
│   │   │   ├── pages/        # Páginas do site
│   │   │   └── store.js       # Configuração do Redux
│   │   └── package.json      # Dependências do frontend
│   ├── static/                # Arquivos estáticos do Flask
│   ├── templates/            # Templates HTML
│   │   ├── base.html         # Template principal
│   │   ├── index.html        # Página inicial
│   │   ├── product.html      # Página de produto
│   │   └── cart.html         # Carrinho de compras
│   └── config.py              # Configurações do projeto
└── requirements.txt          # Dependências do Python
```

## Funcionalidades

### Produtos
- Cadastro completo de produtos
- Filtros por categoria e preço
- Paginação
- Visualização detalhada de cada produto

### Carrinho
- Adicionar/remover produtos
- Atualizar quantidades
- Cálculo automático do total
- Persistência entre sessões

### Checkout
- Formulário de dados do cliente
- Integração com pagamentos (exemplo com Stripe)
- Confirmação de compra

### Admin
- Painel exclusivo para administradores
- Gestão de produtos
- Visualização de pedidos
- Relatórios

## Exemplos Práticos

### Adicionar um produto
No backend:
```python
from app.models import Product

product = Product(
    name="Pod 5%", 
    description="Liquido Premium para Vapes",
    price=29.99, 
    category="Liquidos"
)
product.save()
```

### Renderizar produtos na página inicial
No frontend (React):
```javascript
import { useEffect, useState } from 'react';
import { fetchProducts } from '../../services/api';

function HomePage() {
  const [products, setProducts] = useState([]);

  useEffect(() => {
    async function loadProducts() {
      const data = await fetchProducts();
      setProducts(data);
    }
    loadProducts();
  }, []);

  return (
    <div className="products-grid">
      {products.map(product => (
        <div key={product.id} className="product-card">
          <img src={product.image_url} alt={product.name} />
          <h3>{product.name}</h3>
          <p>{product.description}</p>
          <p>R${product.price}</p>
          <button onClick={() => addToCart(product.id)}>Adicionar ao Carrinho</button>
        </div>
      ))}
    </div>
  );
}
```

## Desenvolvimento

O projeto segue uma metodologia de desenvolvimento ágil com commits frequentes e documentação abrangente.

## Licença

Este projeto está sob a licença MIT. Veja o arquivo LICENSE para mais detalhes.

## Contato

Para dúvidas ou relatos de erros, entre em contato:
- Email: contato@vapeshop.com
- GitHub: https://github.com/seu_usuario/vapeshop

## Versão

Atualmente na versão 1.0.0.