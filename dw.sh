#!/usr/bin/env bash
# =##############################################################################
# dw.sh
# Detiene todo el entorno de producción (Nginx + Redis + FastAPI Backend)
# ###############################################################################
set -euo pipefail

RED='\033[0;31m'
GREEN='\033[0;32m'
CYAN='\033[0;36m'
NC='\033[0m'

info()  { echo -e "${CYAN}[INFO]${NC}  $1"; }
ok()    { echo -e "${GREEN}[OK]${NC}    $1"; }

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

info "Deteniendo todo el entorno de producción..."
docker compose -f docker-compose.prod.yml down --remove-orphans
ok "Entorno de producción apagado exitosamente."
