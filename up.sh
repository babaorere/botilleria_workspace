#!/usr/bin/env bash
# ===============================================================================
# up.sh — Levantar el entorno de la Botillería
# ===============================================================================
set -euo pipefail

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
NC='\033[0m'

info()  { echo -e "${CYAN}[INFO]${NC}  $1"; }
ok()    { echo -e "${GREEN}[OK]${NC}    $1"; }
warn()  { echo -e "${YELLOW}[WARN]${NC}  $1"; }
fail()  { echo -e "${RED}[FAIL]${NC}  $1" >&2; exit 1; }

show_help() {
    echo "Uso: $0 [opción]"
    echo ""
    echo "Opciones:"
    echo "  -dev    Levanta el entorno de DESARROLLO (volúmenes montados localmente)"
    echo "  -prov   Levanta el entorno de PRODUCCIÓN (compilación y optimización limpia)"
    echo "  -prod   Equivalente a -prov (entorno de producción)"
    echo "  -h      Muestra esta pantalla de ayuda y uso"
    echo ""
    echo "Ejemplos:"
    echo "  $0 -dev"
    echo "  $0 -prov"
}

if [ $# -eq 0 ]; then
    warn "No se especificó ninguna opción."
    show_help
    exit 1
fi

MODE=""
COMPOSE_FILE=""
case "$1" in
    -dev)
        MODE="DESARROLLO"
        COMPOSE_FILE="docker-compose.botilleria.yml"
        ;;
    -prov|-prod)
        MODE="PRODUCCIÓN"
        COMPOSE_FILE="docker-compose.prod.yml"
        ;;
    -h|--help)
        show_help
        exit 0
        ;;
    *)
        fail "Opción no válida: $1. Usa -h para ver las opciones disponibles."
        ;;
esac

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

info "Deteniendo contenedores activos (si los hay) para asegurar estado limpio..."
docker compose -f "$COMPOSE_FILE" down --remove-orphans || true

info "Compilando y levantando contenedores en modo $MODE..."
docker compose -f "$COMPOSE_FILE" up -d --build

if [ "$MODE" = "PRODUCCIÓN" ]; then
    info "Esperando a que la API esté lista (Health check)..."
    API_HEALTHY=false
    for i in {1..20}; do
        if docker exec botilleria_api python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/health')" &>/dev/null; then
            API_HEALTHY=true
            break
        fi
        info "Esperando inicialización de la API... ($i/20)"
        sleep 3
    done

    if [ "$API_HEALTHY" = false ]; then
        fail "El backend no logró pasar el control de salud después de 60s."
    fi
    ok "¡Backend activo y saludable!"

    info "Sembrando catálogo de productos en PostgreSQL..."
    docker exec botilleria_api python scripts/seed_products.py
    ok "Catálogo de productos sembrado exitosamente."
else
    info "Esperando inicialización rápida de la API de desarrollo..."
    sleep 5
fi

echo ""
echo -e "${GREEN}╔══════════════════════════════════════════════════════════╗${NC}"
echo -e "${GREEN}║  ✓ ¡El entorno de $MODE está activo!                     ║${NC}"
echo -e "${GREEN}╚══════════════════════════════════════════════════════════╝${NC}"
echo ""
echo -e "${CYAN}Enlaces de Acceso en localhost:${NC}"
echo -e "  🏪 Portal de la Botillería: http://localhost:8080/tenant/"
echo -e "  ⚙️  Portal de Administración: http://localhost:8080/admin/"
echo -e "  📖 Swagger Docs:            http://localhost:8080/docs"
echo ""
