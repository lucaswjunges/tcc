## Blog Flask Simples

Um sistema de blog simples construído com Python Flask.

Este projeto fornece uma base para criar um blog funcional com recursos essenciais como listagem de posts, visualização de detalhes, criação de posts e comentários.

---

## Índice
1. [Instalação](#instalação)
2. [Uso](#uso)
3. [Estrutura do Projeto](#estrutura-do-projeto)
4. [API](#api)
5. [Contribuição](#contribuição)
6. [Licença](#licença)

---

## Instalação

### Pré-requisitos
- Python 3.7 ou superior
- pip (gerenciador de pacotes Python)

### Passos
1. Clone este repositório:
   ```bash
   git clone https://github.com/seu_usuario/blog-flask.git
   cd blog-flask
   ```
2. Crie um ambiente virtual (recomendado):
   ```bash
   python -m venv venv
   source venv/bin/activate  # Linux/MacOS
   venv\Scripts\activate    # Windows
   ```
3. Instale as dependências:
   ```bash
   pip install -r requirements.txt
   ```
4. Configure o banco de dados (inicialização):
   ```bash
   flask db init
   flask db upgrade
   ```

## Uso

### Executando a aplicação
```bash
flask run
```
A aplicação estará disponível em http://localhost:5000

### Funcionalidades
- Homepage: Lista os últimos posts
- Visualização de post: Exibe detalhes de um post específico
- Formulário de criação de post
- Sistema de comentários

## Estrutura do Projeto
```
blog-flask/
├── app.py                  # Ponto de entrada da aplicação
├── config.py               # Configurações do projeto
├── models/                 # Modelos SQLAlchemy
│   ├── __init__.py         # Importação dos modelos
│   ├── post.py             # Modelo Post
│   └── comment.py          # Modelo Comment
├── routes/                 # Rotas da aplicação
│   ├── __init__.py         # Importação das rotas
│   ├── posts.py            # Rotas relacionadas a posts
│   └── comments.py         # Rotas relacionadas a comentários
├── templates/              # Templates HTML
│   ├── base.html           # Template base
│   ├── index.html          # Homepage
│   ├── post.html           # Visualização de post
│   └── create.html         # Formulário de criação de post
├── static/                 # Arquivos estáticos
│   └── style.css           # CSS
└── requirements.txt        # Dependências do projeto
```

## API
A aplicação expõe as seguintes rotas via API:

- `GET /api/posts` - Lista todos os posts
- `GET /api/posts/<int:id>` - Obtém um post específico
- `POST /api/posts` - Cria um novo post
- `GET /api/posts/<int:id>/comments` - Lista comentários de um post
- `POST /api/posts/<int:id>/comments` - Adiciona um comentário a um post

As requisições devem incluir o cabeçalho `Content-Type: application/json`.

Exemplo de criação de post via API:
```bash
curl -X POST -H "Content-Type: application/json" -d '"
    {
        "title": "Novo Post",
        "content": "Conteúdo do novo post"
    }"' http://localhost:5000/api/posts
```

## Contribuição
Contribuições são bem-vindas! Siga estas etapas:

1. Faça fork do repositório
2. Crie uma branch para sua feature (`git checkout -b feature-name`)
3. Faça commits frequentes e significativos
4. Envie um pull request

Certifique-se de seguir o estilo de código existente e adicionar testes para novas funcionalidades.

## Licença
Este projeto está sob a licença MIT. Veja o arquivo [LICENSE](LICENSE) para mais detalhes.
