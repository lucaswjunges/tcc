# Sistema de Blog Simples com Flask

Este projeto implementa um sistema de blog básico usando Python Flask. O sistema permite criar, visualizar, editar e excluir posts de blog em uma interface web.

## Pré-requisitos
Antes de usar este projeto, você precisa ter instalado:
- Python 3.6 ou superior
- pip
- um navegador web

## Instalação
1. Clone este repositório ou baixe-o como um arquivo ZIP:
```bash
https://github.com/seu-username/blog-flask.git
```

2. Navegue até o diretório do projeto:
```bash
cd blog-flask
```

3. Crie e ative um ambiente virtual (opcional, mas recomendado):
```bash
python -m venv venv
source venv/bin/activate  # No Windows use: venv\Scripts\activate
```

4. Instale as dependências:
```bash
pip install -r requirements.txt
```

5. Configure as variáveis de ambiente (crie um arquivo `.env`):
```bash
FLASK_DEBUG=1
DATABASE_URL=postgresql://usuario:senha@localhost/blog
```

## Execução
1. Inicie o servidor Flask:
```bash
flask run --host=0.0.0.0
```

2. Acesse o blog em seu navegador:
```
http://localhost:5000
```

## Estrutura do Projeto
```
blog-flask/\
├── app.py                  # Arquivo principal da aplicação
├── config.py               # Configurações do projeto
├── models/                 # Modelo de dados
│   └── post.py             # Modelo Post
├── routes/                 # Rotas da aplicação
│   ├── __init__.py        # Inicialização das rotas
│   ├── posts.py           # Rotas relacionadas a posts
│   └── users.py           # Rotas relacionadas a usuários
├── templates/              # Templates HTML
│   ├── base.html           # Template base
│   ├── index.html          # Página inicial
│   ├── post.html           # Detalhes do post
│   ├── create.html         # Formulário de criação
│   └── edit.html           # Formulário de edição
├── static/                 # Arquivos estáticos
│   └── styles.css          # CSS para o site
└── .env                    # Variáveis de ambiente
```

## Uso
### Funcionalidades
- **Listagem de Posts**: Veja todos os posts publicados
- **Criação de Post**: Adicione um novo post ao blog
- **Visualização de Post**: Leia posts completos
- **Edição de Post**: Modifique posts existentes
- **Exclusão de Post**: Remova posts indesejados

### Fluxo de Uso
1. Acesse a página inicial para ver todos os posts
2. Para criar um novo post, clique em "Criar Novo Post"
3. Preencha o formulário com título e conteúdo
4. Para ver um post completo, clique no link do post
5. Para editar ou excluir, use os botões nas ações

## Exemplos
### Criar um Post
```python
# No terminal, após a execução do servidor
# Preencha o formulário disponível na página de criação
```

### Atualizar um Post
```python
# Acesse a página de edição através do link
# Modifique o título e/ou conteúdo e clique em salvar
```

## Desenvolvimento Futuro
- Implementação de autenticação de usuários
- Adição de comentários aos posts
- Sistema de administração
- Migração para banco de dados SQLite

## Licença
Este projeto está sob a licença MIT. Veja o arquivo LICENSE para mais detalhes.