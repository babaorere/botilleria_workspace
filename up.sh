#!/usr/bin/env bash
# =##############################################################################
# up.sh
# Levanta todo el entorno de producción (Nginx + Redis + FastAPI Backend)
# ###############################################################################
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

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# ── 1. Validaciones previas ────────────────##################################
info "Verificando requisitos..."
command -v docker &>/dev/null || fail "Docker no está instalado en el sistema."
command -v docker compose version &>/dev/null || fail "Docker Compose no está disponible."



# ── 2. Apagar contenedores activos de producción ──────────────────────────────
info "Deteniendo contenedores de producción activos (si los hay)..."
docker compose -f docker-compose.prod.yml down --remove-orphans
ok "Contenedores detenidos."

# ── 3. Construir e iniciar contenedores ───────────────────────────────────────
info "Construyendo e iniciando el stack de producción (Nginx + Redis + API)..."
docker compose -f docker-compose.prod.yml up -d --build
ok "Contenedores iniciados en segundo plano."

# ── 4. Esperar a que la API esté lista (Health check) ─────────────────────────
info "Esperando a que el backend de FastAPI esté listo..."
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
    fail "El backend no logró pasar el control de salud después de 60s. Revisa los logs con: docker logs botilleria_api"
fi
ok "¡Backend activo y saludable!"

# ── 5. Sembrar el catálogo de productos reales ────────────────────────────────
info "Sembrando catálogo de productos en PostgreSQL..."
docker exec botilleria_api python scripts/seed_products.py
ok "Catálogo de productos sembrado exitosamente."

# ── 6. Resumen y Enlaces de Acceso ───────────────────────────────────────────
echo ""
echo -e "${GREEN}╔══════════════════════════════════════════════════════════╗${NC}"
echo -e "${GREEN}║  ✓ ¡Todo el entorno de producción está levantado!         ║${NC}"
echo -e "${GREEN}╚══════════════════════════════════════════════════════════╝${NC}"
echo ""
echo -e "${CYAN}Enlaces de Acceso en localhost:${NC}"
echo -e "  🏪 ${GREEN}Portal de la Botillería (CRUD de Productos):${NC} http://localhost:8080/tenant/"
echo -e "  ⚙️  ${GREEN}Portal de Administración Global:${NC}          http://localhost:8080/admin/"
echo -e "  📖 ${GREEN}Documentación de la API (Swagger):${NC}       http://localhost:8080/docs"
echo -e "  📡 ${GREEN}Estado de Salud de la API:${NC}               http://localhost:8080/health"
echo ""
echo -e "${CYAN}Comandos de Utilidad:${NC}"
echo "  Ver Logs en tiempo real: docker logs -f botilleria_api"
echo "  Ver Logs de Nginx:       docker logs -f botilleria_nginx"
echo "  Apagar el entorno:       ./dw.sh"
echo ""
