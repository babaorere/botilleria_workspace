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

echo "🔄 Reiniciando el sistema de la Botillería en modo $MODE_LABEL..."
cd "$PROJECT_DIR" || exit

# 1. Bajar los servicios
echo "🛑 Deteniendo servicios actuales..."
docker compose -f $COMPOSE_FILE down

# 2. Esperar 3 segundos para liberar la caché y los puertos de red
echo "⏳ Esperando 3 segundos..."
sleep 3

# 3. Levantar servicios en segundo plano y reconstruir la imagen si hubieron cambios en el código
echo "🚀 Levantando y construyendo los contenedores..."
docker compose -f $COMPOSE_FILE up -d --build

echo ""
echo "✅ ¡Sistema en línea!"
echo "👉 Dashboard: http://localhost:8080/tenant/"
