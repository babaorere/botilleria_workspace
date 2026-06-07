#!/usr/bin/env bash
# ===============================================================================
# dw.sh — Detener el entorno de la Botillería
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
    echo "  -dev    Detiene el entorno de DESARROLLO (docker-compose.botilleria.yml)"
    echo "  -prov   Detiene el entorno de PRODUCCIÓN (docker-compose.prod.yml)"
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

COMPOSE_FILE=""
MODE=""
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

info "Apagando contenedores para el entorno de $MODE..."
docker compose -f "$COMPOSE_FILE" down --remove-orphans
ok "Entorno de $MODE detenido exitosamente."
