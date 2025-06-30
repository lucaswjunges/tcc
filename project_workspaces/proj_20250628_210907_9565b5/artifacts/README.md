# BlogApp - Sistema de Blog Simples com Flask

Este é um sistema de blog simples construído com Python Flask. O projeto foi desenvolvido para demonstrar as habilidades de backend e criação de APIs.

## Índice
1. [Instalação](#instalação)
2. [Uso](#uso)
3. [Estrutura do Projeto](#estrutura-do-projeto)
4. [API](#api)
5. [Contribuição](#contribuição)

## Instalação
### Pré-requisitos
- Python 3.6 ou superior
- pip (gerenciador de pacotes do Python)

### Passos para instalação
1. Clone este repositório:
```bash
git clone https://github.com/seu_usuario/BlogApp.git
```
2. Navegue até o diretório do projeto:
```bash
cd BlogApp
```
3. Crie e ative um ambiente virtual (opcional, mas recomendado):
```bash
python -m venv venv
source venv/bin/activate  # Linux/Mac
venv\Scripts\activate  # Windows
```
4. Instale as dependências:
```bash
pip install -r requirements.txt
```
5. Configure as variáveis de ambiente. Crie um arquivo `.env` na raiz do projeto com o seguinte conteúdo:
```env
FLASK_APP=app.py
FLASK_ENV=development
SECRET_KEY=your_secret_key_here
```

## Uso
### Executando o servidor
```bash
flask run --port=5000
```
O servidor estará disponível em http://localhost:5000

### Comandos úteis
- **Desativar ambiente virtual:** `deactivate`
- **Recriar ambiente virtual:** `rm -rf venv && python -m venv venv && source venv/bin/activate`
- **Reinstalar dependências:** `pip install -r requirements.txt`

## Estrutura do Projeto
```
BlogApp/    
├── app.py        # Arquivo principal da aplicação Flask
├── config.py     # Configurações do projeto
├── models.py     # Definições dos modelos de dados
├── requirements.txt # Dependências do projeto
├── .env          # Arquivo de variáveis de ambiente (exemplo)
└── README.md     # Documentação do projeto
```

## API
### Endpoints
- **GET /posts** - Lista todos os posts
- **GET /posts/<int:id>** - Obtém um post específico pelo ID
- **POST /posts** - Cria um novo post (requer autenticação)
- **PUT /posts/<int:id>** - Atualiza um post existente (requer autenticação)
- **DELETE /posts/<int:id>** - Exclui um post (requer autenticação)

### Parâmetros
Os posts possuem os seguintes campos:
- `id` (int): ID único do post
- `title` (str): Título do post
- `content` (str): Conteúdo do post
- `author` (str): Autor do post
- `created_at` (str): Data de criação

### Autenticação
A API utiliza tokens JWT para autenticação. Para obter um token, envie uma solicitação POST para `/auth/login` com um JSON contendo:
```json
{
  "username": "seu_usuario",
  "password": "sua_senha"
}
```

## Contribuição
Este projeto é open-source e contribuições são bem-vindas. Para contribuir:
1. Crie uma branch do seu repositório
2. Faça as alterações desejadas
3. Envie um pull request

## Licença
Este projeto está sob a licença MIT. Veja o arquivo `LICENSE` para mais detalhes.