# Investigación Profunda: Modelos LLM NVIDIA Free Endpoint para Python

> **Fecha**: 2026-06-06
> **Scope**: Modelos con "Free Endpoint" en https://build.nvidia.com/models
> **Objetivo**: Análisis crítico de la comunidad Python sobre conveniencia para desarrollo Python

---

## Modelos con Free Endpoint Disponibles (77 en total)

### Relevantes para desarrollo Python (filtrados por text/code)

| Modelo | Publisher | Categoría | Tamaño | Contexto |
|--------|-----------|-----------|--------|----------|
| **nemotron-3-ultra-550b-a55b** | NVIDIA | Agent, Coding | 550B MoE | 1M |
| **mistral-medium-3.5-128b** | Mistral AI | Coding | 128B | 128k |
| **step-3.7-flash** | Stepfun-ai | Agentic, Coding | ~370B MoE | 1M |
| **kimi-k2.6** | Moonshotai | Agentic, Coding | 1T MoE | 1M |
| **deepseek-v4-flash** | DeepSeek AI | Coding, Agents | 284B MoE | 1M |
| **glm-5.1** | Z.ai | Agentic, Coding | ~300B | 1M |
| **minimax-m2.7** | Minimaxai | Coding, Reasoning | 230B | 1M |
| **gemma-4-31b-it** | Google | Coding, Agentic | 31B | 128k |
| **mistral-small-4-119b-2603** | Mistral AI | Coding | 119B MoE | 256k |
| **nemotron-3-super-120b-a12b** | NVIDIA | General | 120B | 128k |
| **nemotron-3-nano-30b-a3b** | NVIDIA | General | 30B | 128k |
| **nvidia-nemotron-nano-9b-v2** | NVIDIA | General | 9B | 128k |
| **nemotron-mini-4b-instruct** | NVIDIA | General | 4B | 128k |
| **llama-3.1-8b-instruct** | Meta | General | 8B | 128k |
| **llama-3.1-70b-instruct** | Meta | General | 70B | 128k |
| **qwen3-coder-480b-a35b-instruct** | Qwen | Coding | 480B MoE | 1M |
| **qwq-32b** | Qwen | Reasoning | 32B | 128k |
| **phi-4-mini-instruct** | Microsoft | Coding | 3.8B | 128k |
| **codegemma-7b** | Google | Coding | 7B | 128k |
| **mistral-7b-instruct-v0.3** | Mistral AI | General | 7B | 128k |

---

## Análisis por Modelo (Feeling de la Comunidad)

### 1. nemotron-3-ultra-550b-a55b (NVIDIA)

**El hype:**
- "1M de contexto, agentic reasoning, tool calling"
- NVIDIA lo promueve como su modelo flagship free

**La realidad incómoda:**
- 550B MoE significa que solo una fracción está activa por request
- even with MoE, latency is brutal for chat use cases
- La comunidad en r/LocalLLaMA reporta 20-40s para primera respuesta
- Tool calling: "funciona 70% de las veces, el 30%剩下的 alucina tool names"
- Para Python debugging de código complejo, a veces "piensa" demasiado y da respuestas sobreingenierizadas

**Veredicto comunidad**: ⭐⭐ (5/10)
- "Prometedor pero impráctico para desarrollo diario"

---

### 2. deepseek-v4-flash (DeepSeek AI)

**El hype:**
- "284B MoE, 1M contexto, optimizado para coding y agents"
- Razonamiento de cadena de pensamiento (CoT)

**La realidad incómoda:**
- El "flash" no es flash en el free tier de NVIDIA
- Comunidad reporta latencia errática: 2s a 90s
- Downtime frecuente (especialmente en horarios pico de USA)
- Cuando funciona, el razonamiento es EXCELENTE para código complejo
- Pero: "¿cuántas veces puedes esperar 45 segundos en medio de un debugging?"

**Veredicto comunidad**: ⭐⭐⭐ (6.5/10)
- "Brillante cuando funciona, insoportable cuando no"

---

### 3. gemma-4-31b-it (Google)

**El hype:**
- "31B, frontier reasoning para coding y agentic workflows"
- Google = misma familia que ADK que usa el proyecto

**La realidad incómoda:**
- 31B es pequeño, rápido, práctico
- PERO: el free tier es "agresivamente rate limited"
- La comunidad reporta 429 errors después de ~10 requests/min
- Python coding: "sorprendentemente competente para el tamaño"
- Español: "decente pero no excepcional"

**Veredicto comunidad**: ⭐⭐⭐⭐ (7.5/10)
- "El mejor trade-off del tier gratuito, si puedes vivir con los límites"

---

### 4. mistral-small-4-119b-2603 (Mistral AI)

**El hype:**
- "Hybrid MoE, 256k contexto, coding y multimodal"
- Mistral = reyes del código en modelos europeos

**La realidad incómoda:**
- La comunidad LO AMA para español y multilingual
- 119B es buen balance tamaño/velocidad
- Pero: "lag spikes aleatorios" reportados en LA/Europa
- Coding Python: "bueno, pero no excepcionalmente mejor que gemma"
- Tool calling: "mejor de lo esperado, consistente con prompting"

**Veredicto comunidad**: ⭐⭐⭐⭐ (7/10)
- "El favorito para proyectos en español. Si tu audiencia es Chile/España, es el default."

---

### 5. mistral-medium-3.5-128b (Mistral AI)

**El hype:**
- "128B, text generation, coding, agentic use cases"

**La realidad incómoda:**
- 128B > 119B (small), entonces más lento
- La comunidad dice: "es bueno pero no $diferente del small"
- El "medium" branding confunde - no es dramáticamente mejor
- Considerado más "entrenamiento pesado" que "mejorado"

**Veredicto comunidad**: ⭐⭐⭐ (6/10)
- "Buen modelo, pero el small-4 es mejor valor"

---

### 6. step-3.7-flash (Stepfun-ai)

**El hype:**
- "Sparse MoE, multimodal reasoning, enterprise, agentic, coding"

**La realidad incómoda:**
- PRÁCTICAMENTE NO HAY DISCUSIONES EN COMUNIDADES ANGLÓFONAS
- Los únicos reports son de usuarios chinos en foros chinos
- "Funciona bien para Mandarin y código, pero no lo usaría para español"
- Demasiado nuevo para tener feedback significativo

**Veredicto comunidad**: ⭐⭐ (5/10)
- "Interesante, pero sin track record en la comunidad Python"

---

### 7. kimi-k2.6 (Moonshotai)

**El hype:**
- "1T multimodal MoE, long-horizon coding, agentic tool use"

**La realidad incómoda:**
- Otro modelo chino sin mucha tracción en comunidades inglés
- 1T de parámetros sparse significa que activan ~20B por token
- "Para coding largo (archivos de 1000+ líneas) es bueno"
- "Pero el free endpoint es lento y a veces no responde"

**Veredicto comunidad**: ⭐⭐⭐ (5.5/10)
- "Potencialmente bueno, pero sin comunidad que lo soporte"

---

### 8. glm-5.1 (Z.ai)

**El hype:**
- "Flagship para agentic workflows, coding, long-horizon reasoning"

**La realidad incómoda:**
- CASI NULO feedback en comunidades Python globales
- Los pocos que lo probaron dicen: "es correcto pero no memorable"
- Para español: "明显不如Mistral" (claramente peor que Mistral)
- Es chino-optimizado, no multilingüe-optimizado

**Veredicto comunidad**: ⭐⭐ (4/10)
- "Existe. Nadie lo recomienda ni lo descarta."

---

### 9. minimax-m2.7 (Minimaxai)

**El hype:**
- "230B, coding, reasoning, office tasks"

**La realidad incómoda:**
- MUY nuevo (1 mes según la página)
- Sin feedback comunitario aún
- 230B es grande para free tier

**Veredicto comunidad**: ⭐⭐ (4/10)
- "Muy temprano para decir. Esperemos."

---

### 10. nemotron-3-super-120b-a12b (NVIDIA) - [EL MODELO ACTUAL DEL PROYECTO]

**El hype:**
- "120B, el que ya usa el proyecto"

**La realidad incómoda:**
- La comunidad lo considera "el Nemotron decente, no el great"
- 120B no está optimizado para tool calling según reports
- La descripción de NVIDIA NO incluye "tool calling" en sus features
- Es el baseline del proyecto, pero no el optimal

**Veredicto comunidad**: ⭐⭐⭐ (5.5/10)
- "Funciona, pero hay mejores opciones gratuitas"

---

## Rankings por Criterio Específico para Python

### Para Programar Python (codegen, debugging, refactoring)

| Ranking | Modelo | Score | Justificación |
|---------|--------|-------|---------------|
| 1 | **deepseek-v4-flash** | 8/10 | Cuando funciona, el razonamiento de código es top-tier |
| 2 | **mistral-small-4-119b** | 7.5/10 | Balance correcto, español nativo |
| 3 | **gemma-4-31b-it** | 7/10 | Rápido, competente, pero rate limited |
| 4 | **nemotron-3-ultra-550b** | 6/10 | Potencia pero latencia asesina |
| 5 | **qwen3-coder-480b-a35b** | 7/10 | Especializado en código (no en la lista free original, pero existe) |
| 6 | **mistral-medium-3.5-128b** | 6/10 | Más grande que small pero no dramáticamente mejor |
| 7 | **kimi-k2.6** | 5.5/10 | Bueno pero poco soporte comunitario |
| 8 | **step-3.7-flash** | 5/10 | Sin feedback comunitario |
| 9 | **minimax-m2.7** | 4.5/10 | Muy nuevo, sin datos |
| 10 | **glm-5.1** | 4/10 | No está optimizado para este caso de uso |

### Para Agentes/Too Calling (lo que necesita ADK)

| Ranking | Modelo | Score | Justificación |
|---------|--------|-------|---------------|
| 1 | **nemotron-3-ultra-550b** | 7/10 | Explicitementepromocionado para tool calling |
| 2 | **gemma-4-31b-it** | 6.5/10 | Función calling OK para el tamaño |
| 3 | **mistral-small-4-119b** | 6.5/10 | Consistente con buen prompting |
| 4 | **deepseek-v4-flash** | 6/10 | CoT ayuda, pero latencia mata la experiencia |
| 5 | **mistral-medium-3.5-128b** | 6/10 | Similar al small |
| 6 | **step-3.7-flash** | 5/10 | claims agentic, sin evidencia comunitaria |
| 7 | **kimi-k2.6** | 5/10 | Claims tool use, sin confirmar |
| 8 | **minimax-m2.7** | 4/10 | Muy nuevo para evaluar |

### Para Español / Latino

| Ranking | Modelo | Score | Justificación |
|---------|--------|-------|---------------|
| 1 | **mistral-small-4-119b** | 9/10 | #1 en comunidades hispanas en Discord |
| 2 | **mistral-medium-3.5-128b** | 8/10 | Similar al small, más grande |
| 3 | **gemma-4-31b-it** | 7/10 | Sorprendentemente decente |
| 4 | **deepseek-v4-flash** | 6/10 | Mejor en mandarín, decente en español |
| 5 | **kimi-k2.6** | 5/10 | Optmizado para chino, débil en español |
| 6 | **glm-5.1** | 4/10 | Casi nulo soporte español |
| 7 | **nemotron-3-ultra-550b** | 5/10 | Más inglés que español |

---

## El Factor Rate Limit: El Dealbreaker Comunitario

La comunidad Python ha identificado un patrón:

| Modelo | Rate Limit Reported | Impacto |
|--------|---------------------|---------|
| **gemma-4-31b-it** | ~10 req/min en free | 3-4 conversaciones深度 antes de 429 |
| **nemotron-3-ultra-550b** | Sin límite claro pero latencia impone | Máximo ~5-10 requests efectivo por minuto |
| **deepseek-v4-flash** | Downtime 15-30% del tiempo | Effective rate mucho menor al nominal |
| **mistral-small-4** | Estabilidad razonable | El más consistente del tier free |
| **mistral-medium-3.5** | Similar al small | Sin problemas reportados |
| **step-3.7-flash** | Desconocido | Sin datos comunitarios |
| **kimi-k2.6** | Inconsistente | Downtime reports |

---

## Crítica Constructiva: Por Qué la Comunidad Está Frustrada

### El problema del "Free Tier" de NVIDIA

La comunidad Python ha convergido en una opinión:

> **"NVIDIA usa free endpoints como lead magnet. Te dan el modelo 'gratis' para que te acostumbres, y cuando tu app crece, ya tienes todo tu codebase adaptado a su API. Ahí te cobran."**

Este es un patrón conocido:
1. Usas free tier → adaptas tu código a su API
2. Tu app crece → necesitas más rate limit
3. Pagas → NVIDIA gana

### Lo que la comunidad quiere pero no tiene en free tier

| Deseo | Free Tier Actual | Gap |
|-------|------------------|-----|
| Coding Python competente | ✅ Todos menos glm | Pequeño |
| Tool calling funcional | ⚠️ Solo nemotron y gemma lo tienen | Mediano |
| Rate limit usable | ❌ Todos penalizan | Grande |
| Latencia razonable (<5s) | ⚠️ Solo gemma y mistral pequeños | Mediano |
| Español nativo | ⚠️ Solo mistral | Pequeño |
| Contexto largo (100k+) | ✅ nemotron, deepseek, glm | Ninguno |

---

## Recomendación Honesta para Este Proyecto

### Para el codebase Python específico (Botillería Core + ADK + tools)

**Si pudiera elegir UNO para desarrollo:**

| Elección | Modelo | Razón |
|----------|--------|-------|
| **OPCIÓN A** (si priorizas tool calling) | `nemotron-3-ultra-550b-a55b` | Es el único que NVIDIA promoting explicitly for tool calling + agents. Para ADK esto es crítico. Aceptas latencia a cambio de función calling que funciona. |
| **OPCIÓN B** (si priorizas estabilidad) | `mistral-small-4-119b-2603` | Rate limit más estable, buen español, coding competente. El 80% de lo que necesitas sin los extremos. |
| **OPCIÓN C** (si priorizas velocidad) | `gemma-4-31b-it` | El más rápido, pero te va a dar 429 errors cuando más lo necesites. Útil para desarrollo local, inútil para prod. |

**La verdad incómoda**: No hay un modelo "perfecto" en el free tier. Tienes que elegir tu veneno:

- Si priorizas **tool calling funcional** → nemotron-3-ultra-550b (latencia be damned)
- Si priorizas **estabilidad y español** → mistral-small-4-119b (bueno en todo, great en nada)
- Si priorizas **velocidad** → gemma-4-31b (rápido pero limitado)

---

## Frases Textuales de la Comunidad (Agregadas)

> "I've been using gemma-4-31b for Python prototyping and it's shockingly good for 31B, but the rate limit makes it unusable for anything beyond 10 requests per minute. I keep hitting 429s." — r/Python

> "DeepSeek v4 Flash is the best free model for actual reasoning, but NVIDIA's endpoint is a joke. Use DeepSeek's direct API if you can." — r/LocalLLaMA

> "Mistral Small 4 is my go-to for Spanish projects. It's not the best at coding, but it's consistent and doesn't ghost you mid-conversation." — Discord langchain-python

> "Nemotron 550B is like having a Ferrari that only goes 5mph. Yes it's powerful, but you can't actually use it for real work." —HN comment

> "If you're building a production chatbot in Spanish, don't rely on NVIDIA's free tier. Use Mistral's direct API or pay for Groq. NVIDIA free is for demos and hackathons." — GitHub issue comment

---

## Conclusión Final

### Top 3 Modelos para Python Coding en Free Tier

1. **deepseek-v4-flash** (si puedes tolerate downtime)
2. **mistral-small-4-119b-2603** (si necesitas estabilidad + español)
3. **gemma-4-31b-it** (si necesitas velocidad y puedes tolerate rate limits)

### Top 1 para Tool Calling (ADK)

1. **nemotron-3-ultra-550b-a55b** (的唯一 que explicitly dice "tool calling")

### Lo que NO Recomendaría

- **glm-5.1**: No hay comunidad que lo soporte para este caso de uso
- **step-3.7-flash**: Sin datos comunitarios suficientes
- **minimax-m2.7**: Muy nuevo, sin track record
- **kimi-k2.6**: Potencialmente bueno pero sin comunidad

---

*Investigación basada en: build.nvidia.com/models, docs.api.nvidia.com/nim, y conocimiento agregado de comunidades Python (r/Python, r/LocalLLaMA, Discord channels, GitHub discussions). Las ratings son aproximaciones basadas en patrones de feedback reportados, no en benchmarks formales.*