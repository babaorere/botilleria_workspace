#!/bin/bash

# Aseguramos que trabajamos en el directorio absoluto correcto
PROJECT_DIR="/home/manager/Sync/python_proyects/botilleria_workspace"
COMPOSE_FILE="docker-compose.botilleria.yml"
MODE_LABEL="DESARROLLO (Por defecto)"

if [ "$1" == "-dev" ]; then
    COMPOSE_FILE="docker-compose.botilleria.yml"
    MODE_LABEL="DESARROLLO"
elif [ "$1" == "-prod" ]; then
    COMPOSE_FILE="docker-compose.prod.yml"
    MODE_LABEL="PRODUCCIÓN"
fi

echo "🛑 Apagando los contenedores de la Botillería en modo $MODE_LABEL..."
cd "$PROJECT_DIR" || exit

docker compose -f $COMPOSE_FILE down

echo ""
echo "✅ Todos los contenedores y redes han sido detenidos correctamente."
