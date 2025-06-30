# VapeShop - Loja Online de Acessórios para Vapes e Pods

Website completo para vendas de vapes, pods, e outros acessórios relacionados ao vaporizador de e-liquidos.

Este projeto foi desenvolvido em Python e utiliza um conjunto de tecnologias modernas para criar uma experiência de usuário agradável e funcional.

## Índice

*   [Instalação](#instalação)
*   [Uso](#uso)
*   [Estrutura do Projeto](#estrutura-do-projeto)
*   [Recursos](#recursos)
*   [Exemplos](#exemplos)
*   [Contribuição](#contribuição)

## Instalação

Siga estas etapas para configurar o ambiente de desenvolvimento:

1.  **Clonar o repositório**:
    ```bash
    git clone https://github.com/seu_usuario/vapeshop.git
    cd vapeshop
    ```

2.  **Criar e ativar um ambiente virtual** (recomendado):
    ```bash
    python -m venv venv
    source venv/bin/activate  # Linux/Mac
    venv\Scripts\activate    # Windows
    ```

3.  **Instalar as dependências**:
    ```bash
    pip install -r requirements.txt
    ```

4.  **Configurar variáveis de ambiente**:
    - Crie um arquivo `.env` na raiz do projeto com as seguintes chaves:
        ```
        DATABASE_URL=postgresql://usuario:senha@localhost/vapeshop
        SECRET_KEY=chave_secreta_aqui
        DEBUG=True
        ```

## Uso

Após a instalação, siga estas etapas para executar o projeto:

1.  **Iniciar o servidor de desenvolvimento**:
    ```bash
    python manage.py runserver
    ```
    O servidor estará disponível em `http://localhost:5000` (ou a porta que você especificar).

2.  **Acessar o site**:
    Abra o link no seu navegador para visualizar a aplicação.

3.  **Executar testes** (opcional):
    ```bash
    pytest
    ```

## Estrutura do Projeto

O projeto segue uma estrutura organizada para facilitar o desenvolvimento:

```
├── vapeshop/                      # Pasta principal do projeto
│   ├── app/                       # Módulo de aplicação Flask
│   │   ├── __init__.py           # Configuração do Flask, Blueprints
│   │   ├── routes/                # Controladores/Handlers
│   │   │   ├── home.py            # Rota principal
│   │   │   ├── produtos.py        # Gerenciamento de produtos
│   │   │   ├── carrinho.py        # Lógica do carrinho
│   │   │   └── ...                # Outras rotas
│   │   ├── models/                # Modelo de dados (ORM)
│   │   │   ├── Produto.py         # Modelo de produtos
│   │   │   ├── Usuario.py         # Modelo de usuários
│   │   │   └── ...                # Outros modelos
│   │   ├── templates/             # Arquivos HTML/Blade (exemplo)
│   │   │   ├── home/              # Templates da página inicial
│   │   │   │   ├── index.html
│   │   │   ├── produtos/          # Templates de produtos
│   │   │   │   ├── lista.html
│   │   │   │   └── detalhe.html
│   │   │   ├── carrinho.html
│   │   │   └── ...                # Outras páginas
│   │   │   └── layout/            # Partial templates
│   │   ├── static/                # Arquivos estáticos
│   │   │   ├── css/               # Estilos CSS
│   │   │   ├── js/                # JavaScript
│   │   │   └── img/               # Imagens
│   │   └── ...                    # Outras pastas (forms.py, utils.py)
│   ├── config.py                  # Configurações da aplicação
│   ├── requirements.txt           # Dependências do projeto
│   ├── manage.py                  # Ponto de entrada para comandos
│   └── ...                         # Arquivos de configuração, testes, etc.
└── README.md                       # Este documento
```

## Recursos

O site inclui as seguintes funcionalidades:

*   **Catálogo de Produtos**: Exibição de vapes, pods e acessórios com filtros.
*   **Carrinho de Compras**: Adicionar, remover e atualizar itens.
*   **Páginas de Produtos**: Detalhes completos com imagens, descrição e preços.
*   **Administração**: Painel para gerenciar produtos, usuários e pedidos.
*   **Design Responsivo**: Layout adaptável a dispositivos móveis e desktop.
*   **Integração com Pagamento**: Processamento de pagamentos via API externa.

## Exemplos

### 1. Exemplo de Rota Flask

**app/routes/home.py**:
```python
from flask import Blueprint, render_template
from vapeshop.models.Produto import Produto

home_bp = Blueprint('home', __name__)

@home_bp.route('/\')
def index():
    produtos_populares = Produto.query.filter_by(categoria=\'Popular\').limit(4).all()
    return render_template('home/index.html', produtos=produtos_populares)
```

### 2. Exemplo de Template HTML

**app/templates/home/index.html**:
```html
<!DOCTYPE html>
<html lang="pt-BR">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>VapeShop - Sua Loja de Vapes</title>
    <link rel="stylesheet" href="{{ url_for('static', filename='css/style.css') }}">
</head>
<body>
    <header>
        <!-- Logo e navegação -->
    </header>

    <main>
        <h1>Bem-vindo à VapeShop</h1>
        <p>A sua loja especializada em produtos de vape e pod.</p>
        
        <section class="featured-products">
            <h2>Produtos em Destaque</h2>
            <div class="product-grid">
                {% for produto in produtos %}
                <div class="product-card">
                    <img src="{{ url_for('static', filename='img/' + produto.imagem) }}" alt="{{ produto.nome }}">
                    <h3>{{ produto.nome }}</h3>
                    <p>R$ {{ produto.preco }}</p>
                    <a href="{{ url_for('produtos.detalhe', id=produto.id) }}">Ver detalhes</a>
                </div>
                {% endfor %}
            </div>
        </section>
    </main>

    <footer>
        <!-- Rodapé da página -->
    </footer>
</body>
</html>
```

### 3. Exemplo de Model ORM

**app/models/Produto.py**:
```python
from app import db
from datetime import datetime

class Produto(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(100), nullable=False)
    descricao = db.Column(db.Text, nullable=True)
    preco = db.Column(db.Float, nullable=False)
    imagem = db.Column(db.String(100), nullable=False, default='default.jpg')
    categoria = db.Column(db.String(50), nullable=False)
    estoque = db.Column(db.Integer, default=10)
    data_criacao = db.Column(db.DateTime, default=datetime.utcnow)
    data_atualizacao = db.Column(db.DateTime, onupdate=datetime.utcnow)

    def __repr__(self):
        return f'<Produto {nome}>'

    def to_dict(self):
        return {
            'id': self.id,
            'nome': self.nome,
            'descricao': self.descricao,
            'preco': self.preco,
            'imagem': self.imagem,
            'categoria': self.categoria,
            'estoque': self.estoque
        }
```

## Contribuição

Contribua com este projeto:

1.  Fork este repositório
2.  Crie uma branch para sua feature (`git checkout -b feature/nome-da-feature`)
3.  Faça commit das alterações (`git commit -m 'Add some feature'`)
4.  Envie o push (`git push origin nome-da-feature`)
5.  Envie uma solicitação de pull request

## Licença

Este projeto está sob a licença MIT. Veja o arquivo [LICENÇA](LICENÇA) para mais detalhes.

## Contato

Para dúvidas, sugestões ou problemas, por favor, abra uma issue no repositório ou entre em contato via [email/contato@vapeshop.com](mailto:contato@vapeshop.com).
