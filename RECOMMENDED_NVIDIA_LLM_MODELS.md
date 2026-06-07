# Modelos NVIDIA Free Endpoint — Recomendación para Botillería Core

> **Contexto**: Sistema multi-tenant de atención conversacional para botillerías, usando Google ADK + LiteLLM + OpenRouter/NVIDIA NIM.

---

## Rankings por Criterio

### Tool Calling (ADK)
1. **nemotron-3-ultra-550b-a55b** — NVIDIA lo promociona explícitamente para "agentic reasoning, coding, planning, **tool calling**"
2. **gemma-4-31b-it** — Google lo entrena con function calling nativo
3. **deepseek-v4-flash** — Bueno para "agents", pero tool calling menos consistente que Nemotron/Gemma

### Soporte de español chileno
1. **mistral-small-4-119b-2603** — Mistral entrena activamente en español europeo/latinoamericano
2. **gemma-4-31b-it** — Google tiene buen coverage de español
3. **deepseek-v4-flash** — Decente, pero sesgado a chino/inglés
4. **nemotron-3-ultra-550b-a55b** — Más orientado a inglés técnico

### Latencia (chat en vivo)
1. **gemma-4-31b-it** — 31B = milisegundos de respuesta
2. **mistral-small-4-119b-2603** — 119B MoE = buen balance
3. **deepseek-v4-flash** — 284B MoE, arquitectura eficiente pero más lento
4. **nemotron-3-ultra-550b-a55b** — 550B, el más lento (pero el más capaz)

---

## Recomendación Final

### Para fase de desarrollo actual
Usa **nemotron-3-ultra-550b-a55b** reemplazando en `agents/constants.py`:

```python
GADK_MODEL: Final[str] = "nvidia/nemotron-3-ultra-550b-a55b:free"
GADK_MODEL_DISPLAY: Final[str] = "nemotron-3-ultra-550b:free"
```

Y en `config/settings.py`:
```python
model_name: str = "nvidia/nemotron-3-ultra-550b-a55b:free"
```

### Antes de ir a producción
Si la latencia del 550B es un problema (lo será con 30+ usuarios concurrentes), migra a:

```python
# Opción A: Velocidad máxima
GADK_MODEL: Final[str] = "nvidia/gemma-4-31b-it:free"

# Opción B: Mejor español
GADK_MODEL: Final[str] = "nvidia/mistral-small-4-119b-2603:free"
```

---

## Cómo cambiar el modelo en tu stack

Actualmente usas OpenRouter como intermediario:

```python
# agents/constants.py (actual)
GADK_MODEL: Final[str] = "openrouter/nvidia/nemotron-3-super-120b-a12b:free"
```

Para usar NVIDIA NIM directamente (free endpoint via build.nvidia.com):

1. **Obtén tu NVIDIA API Key** desde [build.nvidia.com](https://build.nvidia.com)
2. **Guarda la key como secret** (Docker Secrets o env var, no en `.env` commiteado)
3. **Cambia el model string** en `agents/constants.py`.
4. **Actualiza `llm_service.py`** para apuntar al endpoint NIM:

```python
from google.adk.models.lite_llm import LiteLlm

model = LiteLlm(
    model="nvidia/nemotron-3-ultra-550b-a55b",  # o el que elijas
    api_key=settings.nvidia_api_key,  # desde secret, no hardcodeado
    api_base="https://integrate.api.nvidia.com/v1",
)
```

---

## Modelos que Deberías EVITAR para este proyecto

| Modelo | Razón |
|--------|-------|
| `cosmos3-nano` | Generación de video, no relevante para chatbot de texto |
| `nemotron-3-content-safety` | Es un modelo de moderación, no de conversación |
| `chatterbox-multilingual-tts` | Text-to-speech, no text-to-text |
| `synthetic-video-detector` | Detección de video AI, irrelevante |
| `nemotron-3-nano-omni-30b-reasoning` | Omni-modal (imagen/video/audio), overkill para chat de texto |

---

## Crítica Constructiva: Modelo Actual

El modelo que usas actualmente (`nemotron-3-super-120b-a12b:free`) tiene **120B**, pero **no está optimizado para tool calling** (no aparece en la descripción de NVIDIA como tool-calling first). Si ADK genera llamadas a funciones inconsistentes, ese es probablemente el culpable.

**Migra a `nemotron-3-ultra-550b-a55b`** para dev — su descripción explícita menciona "tool calling" — y valida si el agente ahora ejecuta tus tools (`consultar_stock`, `consultar_precio`) con mayor fiabilidad.
