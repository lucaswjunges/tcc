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

# Cria o diretório de logs e ajusta as permissões
RUN mkdir -p /home/app/evolux/logs && chown -R app:app /home/app/evolux

# Muda para o usuário não-root
USER app

EXPOSE 8000

CMD ["python", "run.py"]
