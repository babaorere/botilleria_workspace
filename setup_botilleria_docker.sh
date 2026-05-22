#!/usr/bin/env bash
###############################################################################
# setup_botilleria_docker.sh
# Integra botilleria_core con el stack Windmill existente
###############################################################################
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
WM_DIR="$SCRIPT_DIR/../booking-titanium-wm"
CORE_DIR="$SCRIPT_DIR/botilleria_core"

# ── Pre-flight ───────────────────────────────────────────────────────────────
command -v docker  &>/dev/null || fail "docker no está instalado."
command -v docker compose version &>/dev/null || fail "docker compose no está disponible."

# ── 1. Crear base de datos 'botilleria' en PostgreSQL compartido ─────────────
info "Creando base de datos 'botilleria' en PostgreSQL compartido..."
docker exec booking-titanium-wm-db-1 \
  psql -U windmill -d windmill -tc \
  "SELECT 1 FROM pg_database WHERE datname = 'botilleria'" | grep -q 1 && \
  warn "La base de datos 'botilleria' ya existe, saltando creación." || \
  docker exec booking-titanium-wm-db-1 \
    psql -U windmill -d windmill -c "CREATE DATABASE botilleria;"
ok "Base de datos 'botilleria' lista."

# ── 2. Reiniciar Windmill workers con nuevo volumen ─────────────────────────
info "Reiniciando workers de Windmill para montar botilleria_core..."
docker compose -f "$WM_DIR/docker-compose.windmill.yml" up -d \
  windmill_worker \
  windmill_worker_interactive \
  windmill_worker_native
ok "Workers reiniciados con volumen /opt/botilleria_core."

# ── 3. Build y start de botilleria_core ─────────────────────────────────────
info "Construyendo imagen de botilleria_core..."
docker compose -f "$SCRIPT_DIR/docker-compose.botilleria.yml" build --no-cache
ok "Imagen construida."

info "Iniciando servicio botilleria_core..."
docker compose -f "$SCRIPT_DIR/docker-compose.botilleria.yml" up -d
ok "Servicio iniciado."

# ── 3b. Conectar a red de Windmill ──────────────────────────────────────────
info "Conectando botilleria_core a red de Windmill..."
docker network connect booking-titanium-wm_default botilleria_core_api 2>/dev/null || true
ok "Red conectada."

# ── 4. Verificar conectividad ───────────────────────────────────────────────
info "Verificando health check de botilleria_core..."
sleep 5
if docker exec botilleria_core_api python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/health')" &>/dev/null; then
  ok "botilleria_core API responding at http://localhost:8001"
else
  warn "Health check pending, retrying in 10s..."
  sleep 10
  docker exec botilleria_core_api python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/health')" &>/dev/null && \
    ok "botilleria_core API responding at http://localhost:8001" || \
    warn "Health check still pending. Check logs: docker logs botilleria_core_api"
fi

# ── 5. Verificar volumen en workers ─────────────────────────────────────────
info "Verificando montaje de volumen en workers..."
if docker exec booking-titanium-wm-windmill_worker-1 ls /opt/botilleria_core/main.py &>/dev/null; then
  ok "Volumen montado correctamente en workers."
else
  fail "El volumen no se montó en los workers. Verifica docker-compose.windmill.yml"
fi

# ── Resumen ─────────────────────────────────────────────────────────────────
echo ""
echo -e "${GREEN}╔══════════════════════════════════════════════════════════╗${NC}"
echo -e "${GREEN}║  ✓ Botilleria Core integrado con Windmill               ║${NC}"
echo -e "${GREEN}╚══════════════════════════════════════════════════════════╝${NC}"
echo ""
echo -e "${CYAN}Endpoints:${NC}"
echo "  FastAPI API:    http://localhost:8001"
echo "  Health check:   http://localhost:8001/health"
echo "  Docs (Swagger): http://localhost:8001/docs"
echo "  Chat:           POST http://localhost:8001/chat"
echo "  Chat Stream:    POST http://localhost:8001/chat/stream (SSE)"
echo ""
echo -e "${CYAN}Volumen en Windmill workers:${NC}"
echo "  Ruta: /opt/botilleria_core (read-only)"
echo "  Uso en scripts: sys.path.insert(0, '/opt/botilleria_core')"
echo ""
echo -e "${CYAN}Comandos útiles:${NC}"
echo "  Logs:          docker logs -f botilleria_core_api"
echo "  Shell API:     docker exec -it botilleria_core_api bash"
echo "  Shell worker:  docker exec -it booking-titanium-wm-windmill_worker-1 bash"
echo "  Restart:       docker compose -f docker-compose.botilleria.yml restart"
echo "  Tests:         docker exec botilleria_core_api pytest /app/tests/ -v"
echo ""
