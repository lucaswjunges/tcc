# Sistema de Login com Flask

Este repositório contém um exemplo de um sistema de login simples desenvolvido com Flask.

## Pré-requisitos
- Python 3.6 ou superior
- pip (gerenciador de pacotes do Python)

## Instalação
1. Clone o repositório:
```bash
 git clone https://github.com/SEU_USUARIO/seu_projeto.git
```

2. Navegue até o diretório do projeto:
```bash
 cd seu_projeto
```

3. Crie um ambiente virtual (opcional, mas recomendado):
```bash
 python -m venv venv
 source venv/bin/activate  # No Windows, use `venv\Scripts\activate`
```

4. Instale as dependências:
```bash
 pip install -r requirements.txt
```

5. Inicie a aplicação:
```bash
 python app.py
```

## Uso
A aplicação será executada na porta 5000 por padrão.

- **Registro**: Acesse `http://localhost:5000/register` para registrar um novo usuário.
- **Login**: Acesse `http://localhost:5000/login` para fazer login.

Após o login, você será redirecionado para a página principal. A página principal exibe uma mensagem de boas-vindas e informações de usuário.

## API
### Rotas de Autenticação
- `POST /register`
  - **Descrição**: Registra um novo usuário.
  - **Parâmetros no corpo (JSON)**:
    - `username` (string): Nome de usuário.
    - `password` (string): Senha.
  - **Retorno**: Mensagem de sucesso ou erro.

- `POST /login`
  - **Descrição**: Efetua o login do usuário.
  - **Parâmetros no corpo (JSON)**:
    - `username` (string): Nome de usuário.
    - `password` (string): Senha.
  - **Retorno**: Token de autenticação ou erro.

### Rota Protegida
- `GET /protected`
  - **Descrição**: Protegida por autenticação.
  - **Retorno**: Informações do usuário ou erro.

## Estrutura do Projeto
```
seu_projeto/
├── app.py
├── requirements.txt
├── .gitignore
└── README.md
```

- `app.py`: Arquivo principal da aplicação Flask.
- `requirements.txt`: Lista das dependências do projeto.
- `.gitignore`: Arquivo para ignorar arquivos e diretórios no Git.

## Desenvolvimento Futuro
Este projeto é um exemplo básico. Em um ambiente de produção, você deve:
- Armazenar senhas criptografadas.
- Usar um banco de dados para armazenar usuários.
- Implementar HTTPS.

## Licença
Este projeto está sob a licença MIT. Veja o arquivo `LICENSE` para mais detalhes.