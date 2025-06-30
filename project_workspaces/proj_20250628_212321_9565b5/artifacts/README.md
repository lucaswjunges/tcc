# Sistema de Blog Simples com Flask

Este projeto implementa um sistema de blog simples usando Python Flask. O sistema permite criar, ler, atualizar e excluir posts de blog.

## Requisitos
- Python 3.7 ou superior
- Flask
- Jinja2 (template engine)
- Python-pip

## Instalação
1. Clone este repositório ou crie um novo diretório para o projeto:

```bash
mkdir blog-flask
cd blog-flask
```

2. Crie um ambiente virtual (opcional, mas recomendado):

```bash
python -m venv venv
source venv/bin/activate  # Linux/Mac
venv\Scripts\activate  # Windows
```

3. Instale as dependências:

```bash
pip install flask
```

## Estrutura do Projeto
O projeto terá a seguinte estrutura:

```
nome_projeto/          # Raiz do projeto
├── app.py             # Aplicação principal
├── templates/         # Pasta para arquivos HTML
│   ├── base.html      # Template base
│   ├── index.html     # Página inicial
│   ├── post.html      # Template para detalhes do post
│   └── create.html    # Template para criar novo post
├── static/            # Pasta para arquivos estáticos (CSS, JS)
│   └── style.css      # Arquivo CSS
└── README.md          # Documentação atual
```

## Uso
### Iniciar o servidor
```bash
python app.py
```
Acesse `http://localhost:5000` no seu navegador.

### Funcionalidades
1. **Visualizar posts**: Lista todos os posts na página inicial.
2. **Criar post**: Página de formulário para adicionar um novo post.
3. **Detalhes do post**: Exibe um post específico.
4. **Atualizar post**: Edita um post existente.
5. **Excluir post**: Remove um post do sistema.

### Exemplo de post
Um post pode ter:
- Título
- Conteúdo
- Data de criação
- Autor (opcional)

## Exemplos de Código
### app.py
```python
from flask import Flask, render_template, request, redirect, url_for

app = Flask(__name__)

# Lista de posts (em um sistema real, isso viria de um banco de dados)
posts = [
    {
        'id': 1,
        'title': 'Primeiro Post',
        'content': 'Este é o primeiro post do meu blog.'
    },
    {
        'id': 2,
        'title': 'Segundo Post',
        'content': 'Este é o segundo post do meu blog.'
    }
]

@app.route('/')
def index():
    return render_template('index.html', posts=posts)

@app.route('/post/<int:post_id>')
def post(post_id):
    post = next((p for p in posts if p['id'] == post_id), None)
    return render_template('post.html', post=post)

if __name__ == '__main__':
    app.run(debug=True)
```

### templates/index.html
```html
{% extends 'base.html' %}

{% block content %}
<h1>Meu Blog</h1>
<ul>
    {% for post in posts %}
    <li>
        <h2>{{ post.title }}</h2>
        <a href={{ url_for('post', post_id=post.id) }}>Ler mais</a>
    </li>
    {% endfor %}
</ul>
{% endblock %}
```

## Desenvolvimento
Para adicionar funcionalidades ao seu blog, você pode:
1. Expansão do banco de dados (usando SQLite ou outra solução)
2. Adicionar sistema de comentários
3. Implementar autenticação de usuários
4. Melhorar a interface com CSS
5. Adicionar temas/paginação

Este README foi gerado automaticamente. Para contribuir ou obter mais informações, consulte a documentação do Flask e do Jinja2.