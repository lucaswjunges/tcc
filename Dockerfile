# Dockerfile Otimizado

# --- Estágio de Build ---
FROM python:3.11-slim-bookworm AS builder

ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

WORKDIR /opt/venv
COPY requirements.txt .
RUN python -m venv . && \
    . bin/activate && \
    pip install --no-cache-dir -r requirements.txt

# --- Estágio Final ---
FROM python:3.11-slim-bookworm AS final

ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1
ENV VIRTUAL_ENV=/opt/venv
ENV PATH="$VIRTUAL_ENV/bin:$PATH"

# Cria o grupo e o usuário da aplicação primeiro
RUN addgroup --system app && adduser --system --group app

# Copia o ambiente virtual do estágio de build com a permissão correta
COPY --from=builder --chown=app:app /opt/venv /opt/venv

# Define o diretório de trabalho
WORKDIR /home/app/evolux

# Copia primeiro os arquivos de código da aplicação com a permissão correta
# Graças ao .dockerignore, apenas os arquivos necessários serão copiados.
COPY --chown=app:app . .

# Instala gosu para manipulação de permissões no entrypoint
# e depois limpa o cache do apt para manter a imagem pequena.
RUN apt-get update && apt-get install -y --no-install-recommends gosu \
    && rm -rf /var/lib/apt/lists/*

# Copia o script de entrypoint e o torna executável
COPY --chown=app:app entrypoint.sh /usr/local/bin/entrypoint.sh
RUN chmod +x /usr/local/bin/entrypoint.sh

# A criação do diretório de logs e o ajuste de permissões
# agora são gerenciados pelo entrypoint.sh para maior flexibilidade.
RUN mkdir -p /home/app/evolux/logs

# A mudança para o usuário não-root agora é gerenciada
# pelo entrypoint.sh usando gosu para maior segurança e flexibilidade.

EXPOSE 8000

# Define o entrypoint para executar nosso script de inicialização
ENTRYPOINT ["/usr/local/bin/entrypoint.sh"]

# O comando padrão que será passado para o entrypoint
CMD ["python", "run.py"]
