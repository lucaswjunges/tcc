#!/bin/sh
set -e

# Define PUID e PGID padrão se não forem passados
PUID=${PUID:-1000}
PGID=${PGID:-1000}

# Sincroniza o GID do grupo 'app' com o PGID
if [ "$(getent group app | cut -d: -f3)" != "$PGID" ]; then
  echo "Changing 'app' group GID to $PGID"
  groupmod -o -g "$PGID" app
fi

# Sincroniza o UID do usuário 'app' com o PUID
if [ "$(id -u app)" != "$PUID" ]; then
  echo "Changing 'app' user UID to $PUID"
  usermod -o -u "$PUID" app
fi

# Garante que o usuário 'app' seja o dono dos diretórios de volume
echo "Updating ownership of volume directories..."
chown -R app:app /home/app/evolux/project_workspaces
chown -R app:app /home/app/evolux/logs

# Executa o comando passado (CMD) como o usuário 'app'
echo "Permissions are set. Starting application..."
exec gosu app "$@"
