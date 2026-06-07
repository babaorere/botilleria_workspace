# Análisis FODA — Botillería Core (v0.4.0+)

> Fecha: 2026-06-06
> Estado: Post-refactorización (Phase 1–4)
> Autor: Kilo Assistant

---

## 1. FORTALEZAS (Strengths)

| # | Fortaleza | Detalle | Estado |
|---|-----------|---------|--------|
| **S1** | **Autenticación JWT completa** | OAuth2 con `/auth/login`, `/auth/logout`, tokens Bearer, denylist vía Redis | **Mejora reciente** |
| **S2** | **Comparación timing-safe** | `hmac.compare_digest()` en `auth_controller.py` y `security.py` | **Mejora reciente** |
| **S3** | **`jwt_secret` dedicado** | Campo propio en `config/settings.py`, independiente de `admin_api_key` | **Mejora reciente** |
| **S4** | **Split de `tenant_portal_controller.py`** | Monolito de 715 líneas dividido en 3 controladores especializados | **Mejora reciente** |
| **S5** | **Adopción de `JpaRepository`** | `CategoryRepository` y `KBCategoryRepository` heredan de base genérica | **Mejora reciente** |
| **S6** | **Portales frontend con auth JWT** | Admin y tenant usan login JWT con `localStorage` | **Mejora reciente** |
| **S7** | **Alembic para migraciones** | Framework formal reemplaza SQL bootstrap manual | **Mejora reciente** |
| **S8** | **`dependencies.py` centralizado** | `get_current_tenant` extraído a módulo reusable | **Mejora reciente** |
| **S9** | **`get_system_metrics` reparado** | Usa queries SQLAlchemy correctas; eliminado `db.query.__self__.query` | **Mejora reciente** |
| **S10** | **Arquitectura multi-tenant con RLS** | Aislamiento de datos vía `SET app.current_tenant_id` en PostgreSQL | **Base sólida** |
| **S11** | **Sesiones Redis distribuidas** | `RedisSessionService` con TTL, namespace isolation, health check | **Base sólida** |
| **S12** | **Stack de monitoreo completo** | Prometheus + Grafana + Alertmanager con 16 reglas | **Base sólida** |
| **S13** | **Dual engine DB (sync + async)** | `safe_transaction` context manager + `transactional` decorator | **Base sólida** |
| **S14** | **Abstracción LLM por tenant** | API key override, modelo configurable, runner caching | **Base sólida** |
| **S15** | **Seed data realista** | 8 categorías, 20+ productos de botillería chilena | **Base sólida** |

---

## 2. DEBILIDADES (Weaknesses)

| # | Debilidad | Severidad | Ubicación | Riesgo |
|---|-----------|-----------|-----------|--------|
| **W1** | **`.env` con secretos REALES en workspace** | **CRÍTICA** | `botilleria_core/.env` (líneas 8–9, 26) | `NVIDIA_API_KEY`, `OPENROUTER_API_KEY`, `ADMIN_API_KEY` son credenciales reales. Aunque gitignored, el archivo existe en disco (backups, snapshots, rsync, scp, IDE uploads). |
| **W2** | **CORS `allowed_origins: str = "*"`** | **CRÍTICA** | `config/settings.py:49` | Permite cualquier origen. Combinado con `allow_credentials=True`, cualquier sitio malicioso puede hacer requests autenticados cross-origin. |
| **W3** | **JWT secret fallback a `"unsafe-temporary-secret"`** | **CRÍTICA** | `services/auth_service.py:22` | Secret hardcodeado publicado en source code. Cualquiera con acceso al repo puede forjar tokens. |
| **W4** | **`import hmac` dentro de función (hot path)** | **ALTA** | `controllers/auth_controller.py:30` | Import inline en path hot = latencia innecesaria + smell de código. |
| **W5** | **`AgentFactory._registry` dict sin límite — memory leak** | **ALTA** | `services/agent_factory.py:27` | Cada sesión de usuario añade una entrada que **nunca se evicta** (solo vía `.evict()`, que nadie llama). En producción con tráfico real, OOM garantizado. |
| **W6** | **`__get_llm` con import dinámico en dependency** | **MEDIA** | `controllers/session_controller.py:41–43` | `from main import get_llm_service` dentro de función de dependencia = antipattern. Falla opaco en runtime si hay dependencias circulares. |
| **W7** | **`dependencies.py` rompe patrón FastAPI DI** | **MEDIA** | `controllers/dependencies.py:15` | `get_current_tenant` recibe `Request` y `Session` directamente en vez de usar `Depends()`. No reusable con `TestClient`. |
| **W8** | **`_in_memory_denylist` es mutable class variable compartida** | **MEDIA** | `services/auth_service.py:31` | Dict compartido entre todos los workers. `_lock` solo protege algunas operaciones. `revoke_token` + `is_token_revoked` corren en workers distintos sin coherencia. |
| **W9** | **`JWT_SECRET` set en import time** | **MEDIA** | `services/auth_service.py:22` | Si `.env` cambia, requiere restart del servicio. No hay rotación sin downtime. |
| **W10** | **`allowed_origins` default permite cualquier origen** | **ALTA** | `config/settings.py:49` | Default fail-open. Cualquier dev/CI sin variable configurada queda expuesto. |
| **W11** | **`_save_message_background` sin rollback explícito** | **MEDIA** | `services/chat_service.py` | `SessionLocal()` con `with` solo hace `close()` en exit, no `commit()` ni `rollback()` garantizado en error. |
| **W12** | **Root agent tools abren sesiones DB propias** | **MEDIA** | `agents/root_agent.py` | 8+ tool functions, cada uno con `with SessionLocal()`. Sin pool sharing, sin rollback guaranteed en error. |
| **W13** | **API keys de tenant en plaintext en DB** | **MEDIA** | `models/tenant.py` | Campo `config` JSON con `api_key` en texto plano. Si hay leak de backup, están expuestas. |
| **W14** | **Sin scripts de rollback para migraciones SQL** | **MEDIA** | `scripts/migrations/` | Alembic tiene `downgrade`, pero los SQL originales no. Si algo falla en prod, no hay rollback fácil. |
| **W15** | **`resolve_tenant` sigue duplicado** | **MEDIA** | `chat_controller.py`, `session_controller.py`, `tenant_portal_controller.py` (ahora 3 controllers) | Lógica UUID validation + tenant lookup + error handling repetida con sutiles diferencias. |

---

## 3. AMENAZAS (Threats)

| # | Amenaza | Riesgo | Ubicación |
|---|---------|--------|-----------|
| **T1** | **`.env` con secretos reales en workspace** | Robo de credenciales, uso no autorizado de LLM, costos inesperados | `botilleria_core/.env` |
| **T2** | **Sin HTTPS en producción** | MITM, interceptación de JWTs y API keys | `nginx.conf:35` (SSL comentado) |
| **T3** | **Alertmanager descarta todas las alertas** | Fallas silenciosas, outages no detectados | `monitoring/alertmanager/alertmanager.yml:9` |
| **T4** | **Password DB `windmill` hardcodeado** | Acceso no autorizado a PostgreSQL | `docker-compose.prod.yml:22` |
| **T5** | **Red Docker compartida con Windmill** | Movimiento lateral entre contenedores | `docker-compose.botilleria.yml` |
| **T6** | **JWT secret fallback publicado** | Forgery de tokens, escalada de privilegios | `services/auth_service.py:22` |
| **T7** | **Sin rate limiting en API admin** | Brute-force, enumeración de tenants | `nginx.conf` |
| **T8** | **Memory leak en AgentFactory** | Degradación de servicio, OOM kills | `services/agent_factory.py:27` |
| **T9** | **CORS wildcard default** | Ataques cross-origin desde cualquier dominio | `config/settings.py:49` |
| **T10** | **Pool de conexiones DB sin límites** | Agotamiento de conexiones bajo carga | `config/database.py` |

---

## 4. OPORTUNIDADES (Opportunities)

| # | Oportunidad | Impacto | Esfuerzo |
|---|-------------|---------|----------|
| **O1** | **Secret Management centralizado** | Rotar secrets sin redeploy, auditar acceso, eliminar `.env` drift | Medio |
| **O2** | **LRU Cache con TTL para `AgentFactory`** | Eliminar memory leak, TTL para sesiones stale | Bajo |
| **O3** | **CORS fail-closed en producción** | Rechazar arranque si `allowed_origins == "*"` | Bajo |
| **O4** | **Limpiar DI en `session_controller.py`** | Remover `__get_llm` dinámico, usar `Depends(get_llm_service)` | Bajo |
| **O5** | **HTTPS enforcement** | Redirect HTTP→HTTPS, HSTS, secure cookies | Medio |
| **O6** | **Wiring real de Alertmanager** | Slack/Email/PagerDuty para incident response | Bajo |
| **O7** | **JWT secret sin restart** | Cache TTL o file watcher para rotación sin downtime | Medio |
| **O8** | **Cifrar API keys de tenant** | Fernet para at-rest encryption | Medio |
| **O9** | **Centralizar `resolve_tenant`** | Un solo `Depends()` en `middleware/tenant_deps.py` | Bajo |

---

## 5. LISTADO DE MEJORAS SUGERIDAS

### P0 — CRÍTICO (Blockers de producción)

| # | Mejora | Justificación | Archivos |
|---|--------|-------------|----------|
| **1** | **Eliminar `botilleria_core/.env` del workspace y rotar TODAS las keys** | Contiene NVIDIA_API_KEY, OPENROUTER_API_KEY, ADMIN_API_KEY reales. Gitignore no es suficiente; el file en disk es riesgo de fuga (backups, snapshots, rsync, IDE uploads, accidental `git add -f`). | `botilleria_core/.env` |
| **2** | **Rechazar arranque si `jwt_secret` es vacío en producción** | El fallback `"unsafe-temporary-secret"` es un secret hardcodeado publicado. Cualquiera que lea el repo puede forjar tokens de admin. | `services/auth_service.py:19–22`, `config/settings.py` |
| **3** | **Rechazar arranque si `allowed_origins == "*"` en producción** | Default fail-open. Cualquier dev/CI sin variable configurada queda expuesto a CORS attacks. | `config/settings.py:49` |
| **4** | **Habilitar HTTPS en Nginx** | SSL sigue comentado. Todo el tráfico incluyendo JWT tokens y credenciales va en plaintext HTTP. | `nginx.conf:35`, `docker-compose.prod.yml` |

### P1 — ALTO (Seguridad y estabilidad)

| # | Mejora | Justificación | Archivos |
|---|--------|-------------|----------|
| **5** | **Agregar evicción a `AgentFactory._registry`** | Dict sin límite = memory leak garantido. N uniques `(user_id, session_id)` → N entries sin borrar. En bot conversacional, esto crece indefinidamente. Usar `cachetools.TTLCache(maxsize=500, ttl=3600)`. | `services/agent_factory.py:27` |
| **6** | **Mover `import hmac` al toplevel** | Import inline en hot path = latencia innecesaria. No hay justificación de lazy load. | `controllers/auth_controller.py:30` |
| **7** | **Refactorizar `dependencies.py` a patrón FastAPI DI** | `get_current_tenant` recibe `Request` y `Session` directamente. Rompe reusabilidad y testing con `TestClient`. Convertir a `Depends()` standard. | `controllers/dependencies.py` |
| **8** | **Eliminar `__get_llm` dynamic import** | `import main` dentro de función dependency es antipattern. Usar `Depends(get_llm_service)` desde `main.py` (ya existe). | `controllers/session_controller.py:41–43` |
| **9** | **Configurar receiver real en Alertmanager** | `receiver: 'null'` descarta todas las alertas. Prometheus puede estar perfecto, pero nunca sabrás de un incidente. | `monitoring/alertmanager/alertmanager.yml:9` |
| **10** | **Añadir pool size y max_overflow a SQLAlchemy** | Sin límites, background threads + agent tools abren sesiones sin control. `pool_size=10`, `max_overflow=20`, `pool_pre_ping=True`. | `config/database.py` |

### P2 — MEDIO (Arquitectura)

| # | Mejora | Justificación | Archivos |
|---|--------|-------------|----------|
| **11** | **Implementar TTLCache para `AgentFactory`** | Drop-in replacement con eviction automático. Elimina W5 por completo. | `services/agent_factory.py` |
| **12** | **Agregar scripts de rollback SQL** | Los SQL originales no tienen `*_down.sql`. Si Alembic no está listo, necesitas rollback manual para prod. | `scripts/migrations/` |
| **13** | **Rate limiting real en admin API** | El zone `admin_limit` en Nginx solo aplica a archivos estáticos, no a la API. Cualquier bot puede brute-forcear admin endpoints. | `nginx.conf` |
| **14** | **Centralizar `resolve_tenant` en `middleware/tenant_deps.py`** | La misma lógica de UUID validation + tenant lookup está en 3 controladores con sutiles diferencias. Un solo `Depends()` consistente. | `chat_controller.py`, `session_controller.py`, `tenant_*_controller.py` |
| **15** | **Cifrar API keys de tenant en reposo** | Campo `config.api_key` en plaintext JSON. Un DB dump = exposición completa. Usar `cryptography.fernet.Fernet` con `ENCRYPTION_KEY` en env. | `models/tenant.py` |

### P3 — BAJO (Refinamiento)

| # | Mejora | Justificación | Archivos |
|---|--------|-------------|----------|
| **16** | **JWT secret sin restart** | Usar `lru_cache` TTL o file watcher para rotar secret sin downtime. Útil para incident response. | `services/auth_service.py` |
| **17** | **Reducir info en `/health`** | Exponer `worker_pid`, `session_backend`, `multi_tenant` es reconocimiento gratuito para atacantes. | `controllers/health_controller.py` |
| **18** | **Agregar `pool_pre_ping=True`** a engines | Detecta conexiones stale antes de usarlas. Previene errores silenciosos de "conexión cerrada". | `config/database.py` |

---

## 6. Anexo: Alternativas de Manejo de Secretos (.env no es suficiente)

### ¿Por qué `.env` no es seguro?

Aunque `.env` está en `.gitignore`, sigue siendo un **archivo en texto plano en el filesystem** con:

- **Permisos poco restrictivos** (normalmente `644` o `664`)
- **Sin encriptación en reposo**
- **Riesgo de fuga por backups, snapshots, rsync, scp, IDE uploads, accidental `git add -f`**
- **Sin audit trail** — no sabes quién leyó el archivo ni cuándo
- **Sin rotación automática** — si se compromete, hay que editar manualmente y hacer deploy

### Alternativas por nivel de madurez

#### 1. Docker Secrets (mínimo viable para Docker)

```yaml
# docker-compose.prod.yml
secrets:
  openrouter_api_key:
    file: ./secrets/openrouter_api_key.txt  # nunca commiteado
  admin_api_key:
    file: ./secrets/admin_api_key.txt

services:
  api:
    secrets:
      - openrouter_api_key
      - admin_api_key
```

En la app:
```python
def read_secret(name: str) -> str:
    with open(f"/run/secrets/{name}") as f:
        return f.read().strip()

OPENROUTER_API_KEY = read_secret("openrouter_api_key")
```

**Ventaja**: El secret no está en `.env` ni en variables de entorno. Solo el contenedor puede leerlo.

#### 2. Variables de entorno inyectadas en runtime (mejor que `.env` en repo)

```yaml
services:
  api:
    environment:
      - OPENROUTER_API_KEY=${OPENROUTER_API_KEY}  # Del shell host, no del repo
```

**Ventaja**: El secret nunca toca el disco del repo. Solo existe en memoria del contenedor.

#### 3. Cloud Secret Manager (AWS / Azure / GCP)

```python
import boto3

def get_secret(secret_name: str) -> str:
    client = boto3.client("secretsmanager", region_name="us-east-1")
    resp = client.get_secret_value(SecretId=secret_name)
    return resp["SecretString"]

OPENROUTER_API_KEY = get_secret("botilleria/openrouter_api_key")
```

**Ventajas**: Audit trail, rotación automática, encriptación KMS, IAM policies.

#### 4. HashiCorp Vault (estándar enterprise)

```python
import hvac

client = hvac.Client(url="https://vault.botilleria.com")
client.auth.approle.login(role_id="botilleria-api", secret_id="...")

secret = client.secrets.kv.v2.read_secret_version(path="botilleria/prod/openrouter")
OPENROUTER_API_KEY = secret["data"]["data"]["api_key"]
```

**Ventajas**: Dynamic secrets, lease TTL, audit log, secret engines para DB.

#### 5. 1Password / Bitwarden Secrets (práctico para equipos pequeños)

```bash
export OPENROUTER_API_KEY=$(op read "op://Botilleria/OpenRouter/credential")
```

**Ventajas**: UI familiar, service accounts con permisos granulares, rotación sencilla.

### Comparativa rápida

| Solución | Encriptación | Audit | Rotación | Complejidad | Costo |
|----------|-------------|-------|----------|-------------|-------|
| `.env` en repo | ❌ No | ❌ No | ❌ Manual | Baja | Gratis |
| `.env` gitignored | ❌ No | ❌ No | ❌ Manual | Baja | Gratis |
| Docker Secrets | ✅ Sí (en reposo) | ❌ No | ❌ Manual | Media | Gratis |
| Env vars runtime | ✅ En memoria | ❌ No | ❌ Manual | Baja | Gratis |
| AWS/GCP/Azure SM | ✅ Sí (KMS) | ✅ Sí | ✅ Automática | Media | $ |
| HashiCorp Vault | ✅ Sí | ✅ Sí | ✅ Automática | Alta | $$$ |
| 1Password Secrets | ✅ Sí | ✅ Sí | ✅ Manual | Baja | $$ |

### Recomendación para tu stack actual

Dado que estás en **Docker Compose con un solo VPS**, el **mínimo viable** es:

1. **Eliminar `botilleria_core/.env` del workspace** (no del `.env.example`)
2. **Crear `secrets/` en el servidor prod** (nunca en el repo):
   ```bash
   mkdir -p /opt/botilleria/secrets
   echo "sk-or-v1-xxxxx" > /opt/botilleria/secrets/openrouter_api_key
   chmod 600 /opt/botilleria/secrets/openrouter_api_key
   ```
3. **Montar secrets en `docker-compose.prod.yml`**:
   ```yaml
   services:
     api:
       secrets:
         - openrouter_api_key
   ```
4. **Leer desde `/run/secrets/` en la app**
5. **Para el repo**, solo commitear `.env.example` con placeholders

**Próximo paso (si crece el proyecto):** Migrar a **AWS Secrets Manager** o **HashiCorp Vault** para audit trail y rotación automática. Docker Secrets es 100× mejor que `.env` con claves reales.

---

## 7. Crítica Constructiva (lo que NO ha funcionado)

1. **Las 4 fases de refactor fallaron en atender los fundamentos de seguridad más básicos**
   - Se invertió esfuerzo en Alembic, split de controllers, JWT auth... pero el `.env` con secretos reales sigue en el workspace.
   - Es como instalar una puerta blindada (JWT auth) mientras la ventana está abierta (`.env` con keys reales).

2. **`"unsafe-temporary-secret"` es anti-patrón crítico**
   - Un fallback por conveniencia de desarrollo es una brecha de seguridad en producción.
   - La aplicación DEBE fallar (raise RuntimeError) si `jwt_secret` no está configurado en env=production.

3. **Memory leak de AgentFactory no es teórico**
   - Supón 100 usuarios/día, 5 sesiones cada uno. En 1 mes: ~15,000 entries en `_registry`.
   - Cada entry es un dict con datos del agente. Si el agente tiene modelo LLM en memoria, el leak es exponencial.
   - Esto matará el proceso. No es "posible": es **inevitable** con tráfico real.

4. **Alertmanager `receiver: 'null'` es indiferente**
   - Tienes 16 reglas de alerta bien escritas que terminan en `/dev/null`.
   - Es equivalente a tener un detector de humo sin batería.

---

## 7. Recomendación de Ejecución

```
Semana 1 (P0):
  [1] Eliminar .env real → rotar keys → usar .env.example
  [2] Agregar validación: if not jwt_secret and is_production: raise
  [3] Agregar validación: if allowed_origins == "*" and is_production: raise
  [4] Habilitar SSL en nginx.conf + docker-compose.prod.yml

Semana 1–2 (P1):
  [5] TTLCache en AgentFactory
  [6] Mover import hmac al toplevel
  [7] Refactorizar dependencies.py a FastAPI DI
  [8] Wire Alertmanager (Slack webhook mínimo)
  [10] Pool size en SQLAlchemy

Semana 2–3 (P2):
  [11] Centralizar resolve_tenant
  [13] Rate limiting admin API
  [15] Cifrar API keys tenant
```

---

## 8. Métricas de Git

| Metric | Value |
|--------|-------|
| Total commits | ~10 |
| Branches | 1 (main) |
| Pull requests | 0 |
| CI/CD pipeline | No existe |
| Branch protection | No existe |
| Pre-commit hooks | No existen |

**Recomendación**: Antes de cualquier nuevo feature, abrir PRs con branch protection + CI (ruff + pytest + bandit/security scan). Los 4 P0 deben pasar antes de mergear cualquier otra cosa.

---

*Este informe fue generado por Kilo Assistant como análisis crítico post-refactorización. Las mejoras identificadas priorizan seguridad (P0) sobre funcionalidad o arquitectura.*
