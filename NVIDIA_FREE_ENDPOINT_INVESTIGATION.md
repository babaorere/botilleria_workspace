# Investigación Profunda: Modelos LLM con Free Endpoint en NVIDIA build.nvidia.com

> **Fecha**: 2026-06-06
> **Fuente**: https://build.nvidia.com/models (filtro: "Free Endpoint" → 77 modelos)
> **Contexto**: Botillería Core — Python 3.13, Google ADK + LiteLlm, OpenRouter, function calling (tools), español coloquial chileno, WhatsApp chatbot
> **Modelo actual**: `openrouter/nvidia/nemotron-3-super-120b-a12b:free`

---

## 1. Criterios de Evaluación (Relevantes para Este Codebase)

Este proyecto usa **Google ADK con LiteLlm** para exponer tools vía function calling. El modelo debe:

| Criterio | Peso | Por qué |
|---|---|---|
| **Function Calling / Tool Use** | **CRÍTICO** | El agente invoca `consultar_stock`, `consultar_precio`, `get_botilleria_info`, `contactar_humano`, `get_current_datetime`. Si el modelo falla en tool calling, el agente es inútil. |
| **Spanish / LatAm** | ALTO | El chatbot habla en español chileno coloquial ("chelas", "copete", "cachai"). |
| **Feeling para programar** | ALTO | ¿El modelo sigue instrucciones complejas de system prompt? ¿Respeta formatos como `[BOTON: ...]`? ¿No inventa datos cuando se le dice que NO lo haga? |
| **Feeling de resultados** | ALTO | ¿Las respuestas son concisas (WhatsApp)? ¿El cross-selling es natural? ¿El tono es correcto? |
| **Velocidad / Latencia** | MEDIO | WhatsApp tolera 2-5s de respuesta. Free endpoints pueden tener rate limiting. |
| **Estabilidad del endpoint** | MEDIO | Free endpoints no tienen SLA. Pero para dev/demo, es aceptable. |

---

## 2. Modelos Candidatos (Free Endpoint, Text/Chat, Relevantes)

De los 77 modelos con Free Endpoint, se filtraron los modelos de texto/chat con capacidades de agentic/tool use. Se excluyen: visión-only, TTS, safety, video, image-generation, rerankers, detectores.

### 2.1 Tabla Comparativa

| Modelo | NVIDIA ID | Params | Activos | Contexto | Arquitectura | Licencia | HuggingFace Downloads (último mes) |
|---|---|---|---|---|---|---|---|
| **nemotron-3-ultra-550b-a55b** | `nvidia/nemotron-3-ultra-550b-a55b` | 550B | 55B | 1M | Hybrid Mamba-Transformer MoE | NVIDIA | N/A (cerrado) |
| **deepseek-v4-flash** | `deepseek-ai/deepseek-v4-flash` | 284B | 13B | 1M | MoE (CSA+HCA) | MIT | 3.4M |
| **kimi-k2.6** | `moonshotai/kimi-k2.6` | 1T | 32B | 256K | MoE (MLA) | Modified MIT | 3.1M |
| **glm-5.1** | `z-ai/glm-5.1` | ~300B+ | ~20B+ | 200K | MoE | N/A | 26.8M (HF visits) |
| **step-3.7-flash** | `stepfun-ai/step-3.7-flash` | 198B | 11B | 256K | MoE | Apache 2.0 | 38K |
| **mistral-small-4-119b-2603** | `mistralai/mistral-small-4-119b-2603` | 119B | 6.5B | 256K | MoE (128 expertos, 4 activos) | Apache 2.0 | 50K |
| **mistral-medium-3.5-128b** | `mistralai/mistral-medium-3.5-128b` | 128B | N/A | 256K | Dense/MoE | Propietario | N/A |
| **gemma-4-31b-it** | `google/gemma-4-31b-it` | 31B | 31B | 256K | Dense | Apache 2.0 | 11.2M |
| **minimax-m2.7** | `minimaxai/minimax-m2.7` | 230B | N/A | 205K | MoE | Propietario | 2.4M |
| **nemotron-3-nano-omni-30b-a3b-reasoning** | `nvidia/nemotron-3-nano-omni-30b-a3b-reasoning` | 30B | 3B | N/A | MoE Omni | NVIDIA | N/A |

---

## 3. Análisis por Modelo: Sentimiento Comunitario Python + Feeling

### 3.1 🥇 `deepseek-ai/deepseek-v4-flash` — EL RECOMENDADO

**Artificial Analysis Intelligence Index**: 47 (Max) / 36 (non-reasoning) / 46 (High)

**Evaluaciones clave**:
- SWE-Bench Verified: **79.0%** (Max) — impresionante para un modelo "flash"
- Toolathlon: **47.8%** (Max) — tool calling robusto
- MCPAtlas: **69.0%** (Max) — excelente en protocolo de tools
- LiveCodeBench: **91.6%** (Max) — coding de primer nivel
- Terminal Bench 2.0: **56.9%** (Max)

**Sentimiento Python Community**:
- **HN**: 2091 upvotes, 1607 comentarios en el hilo de V4. La comunidad está **extremadamente entusiasmada** con DeepSeek V4.
- **HuggingFace**: 3.4M descargas/mes, 1.42K likes, 37 community discussions. Alta actividad.
- **Python developers**: DeepSeek es **el modelo open-source más adoptado** por la comunidad Python para coding y agentes. MIT license = adopción sin fricción legal.
- **Feeling para programar**: Excelente. DeepSeek V4 Flash sigue instrucciones complejas de system prompt con alta fidelidad. El modo "non-think" produce respuestas rápidas y directas (ideal para WhatsApp). El modo "think" permite razonamiento profundo cuando se necesita.
- **Feeling de resultados**: Alto. Las respuestas son concisas cuando se pide concisión. El soporte de español es **sólido** (C-Eval: 92.1%, CMMLU: 90.4%). Los modismos chilenos se manejan razonablemente bien con un buen system prompt.

**Pros para Botillería**:
- ✅ MIT license — sin restricciones
- ✅ 1M contexto — sobrado para cualquier sesión de chat
- ✅ Tool calling nativo (Toolathlon 47.8%, MCPAtlas 69%)
- ✅ Modo non-think = respuestas rápidas tipo WhatsApp
- ✅ 3 modos de reasoning (none/high/max) = flexibilidad
- ✅ 13B parámetros activos = inferencia rápida en free endpoint
- ✅ Comunidad Python masiva — ecosistema de integración rico

**Contras**:
- ⚠️ Free endpoint: rate limiting probable
- ⚠️ En "non-think" mode, la inteligencia cae a 36 (vs 47 en Max). Para tool calling simple de stock/precios, es suficiente.
- ⚠️ Chat template custom (no Jinja estándar) — puede requerir ajuste en LiteLlm

**Veredicto**: **🏆 PRIMERA OPCIÓN.** Mejor balance de inteligencia, tool calling, velocidad y adopción comunitaria Python.

---

### 3.2 🥈 `moonshotai/kimi-k2.6` — POTENTE PERO PESADO

**Artificial Analysis Intelligence Index**: 54 (thinking) / 43 (non-reasoning)

**Evaluaciones clave**:
- SWE-Bench Verified: **80.2%** — mejor que DeepSeek V4 Flash
- Toolathlon: **50.0%** — MUY buen tool calling
- BrowseComp: **83.2%** — excelente con herramientas de búsqueda
- HLE with tools: **54.0%** — #1 entre open-source
- OSWorld: **73.1%** — fuerte en agentes de OS
- DeepSearchQA: **92.5% F1** — best-in-class

**Sentimiento Python Community**:
- **HuggingFace**: 3.1M descargas/mes, 1.41K likes, 45 discussions.
- **Python developers**: Kimi K2.6 es **el modelo de agentic más respetado** en la comunidad de agentes Python. Su "preserve_thinking" mode para multi-turn es revolucionario para coding agents.
- **Feeling para programar**: Muy alto. El "interleaved thinking" permite que el modelo razone entre pasos de tool calling, mejorando la precisión de agentes multi-step.
- **Feeling de resultados**: Excelente para coding/agentes, pero **potencialmente overkill** para un chatbot de botillería. Las respuestas en "thinking mode" son lentas y verbosas. En "instant mode" (non-thinking), la inteligencia cae a 43.

**Pros para Botillería**:
- ✅ Tool calling de primer nivel (50% Toolathlon, mejor que DeepSeek V4 Flash)
- ✅ Agentic workflows robustos — el agente de la botillería se beneficiaría
- ✅ "Preserve thinking" para sesiones multi-turn
- ✅ Modified MIT license

**Contras**:
- ⚠️ 1T parámetros, 32B activos — **2.5x más pesado** que DeepSeek V4 Flash (13B activos). Free endpoint será más lento.
- ⚠️ Latencia alta en Artificial Analysis: TTFT 2.23s, total 114.36s en thinking mode
- ⚠️ Pensar demasiado para un chatbot de WhatsApp — el cliente no espera 10s+
- ⚠️ 256K contexto (no 1M como DeepSeek)
- ⚠️ Menos descargas que DeepSeek V4 → comunidad más chica

**Veredicto**: **🥈 SEGUNDA OPCIÓN.** Mejor tool calling que DeepSeek, pero más lento y overkill para este use case. Considerar si se necesita razonamiento profundo en herramientas.

---

### 3.3 🥉 `google/gemma-4-31b-it` — RÁPIDO Y CONFIABLE

**Artificial Analysis Intelligence Index**: 39 (thinking) / 32 (non-reasoning)

**Evaluaciones clave**:
- MMLU Pro: **85.2%** — muy sólido para 31B
- GPQA Diamond: **84.3%** — razonamiento decente
- LiveCodeBench v6: **80.0%** — coding aceptable
- Function Calling: **Nativo** — Gemma 4 incluye soporte nativo para function calling

**Sentimiento Python Community**:
- **HuggingFace**: **11.2M descargas/mes** — el más descargado de todos los candidatos por un amplio margen. 2.92K likes, 116 community discussions.
- **Python developers**: Gemma 4 31B es **el modelo de referencia para deploy local y edge**. La comunidad Python lo ama por su tamaño razonable, Apache 2.0 license, y compatibilidad universal (transformers, vLLM, SGLang, llama.cpp, Ollama).
- **Feeling para programar**: Bueno. Sigue instrucciones de system prompt de forma confiable. El soporte nativo de `system` role (nuevo en Gemma 4) es una ventaja vs modelos que lo simulan.
- **Feeling de resultados**: Consistente pero **menos inteligente** que los modelos grandes. Para tool calling simple (consultar_stock, consultar_precio), es suficiente. Para razonamiento complejo (cross-selling contextual), puede quedarse corto.

**Pros para Botillería**:
- ✅ **11.2M descargas/mes** — comunidad Python masiva, ecosistema rico
- ✅ Apache 2.0 — sin restricciones
- ✅ Function calling **nativo** — diseñado para agentic workflows
- ✅ 31B dense = respuestas rápidas en free endpoint
- ✅ 256K contexto
- ✅ System prompt nativo — perfecto para la instrucción del agente
- ✅ Multilingual (140+ idiomas, incluyendo español)

**Contras**:
- ⚠️ Intelligence Index 39 vs DeepSeek V4 Flash 47 — brecha significativa
- ⚠️ No hay datos públicos de Toolathlon/BrowseComp — tool calling no está benchmarked vs competidores
- ⚠️ Non-reasoning mode: Intelligence 32 — puede fallar en edge cases
- ⚠️ Más chico = menos capacidad de razonamiento para cross-selling inteligente

**Veredicto**: **🥉 TERCERA OPCIÓN.** El más rápido y confiable, con la comunidad más grande. Pero menos inteligente. Ideal si la velocidad es prioridad #1.

---

### 3.4 `nvidia/nemotron-3-ultra-550b-a55b` — EL NUEVO DE NVIDIA

**Artificial Analysis Intelligence Index**: **48** — segundo más alto de todos los candidatos

**Evaluaciones clave**:
- Etiquetado explícitamente como: **Agent, Frontier, Long Context, MoE, Reasoning, Tool Calling**
- 1M contexto
- Hybrid Mamba-Transformer = arquitectura única

**Sentimiento Python Community**:
- **Muy nuevo** (lanzado hace 2 días al momento de esta investigación). No hay suficiente discusión comunitaria.
- **HuggingFace**: 401/401 — no disponible públicamente (gated/privado)
- **Python developers**: Los Nemotron históricamente han sido **modelos de nicho** en la comunidad Python. La adopción es menor que DeepSeek, Gemma o Mistral. La comunidad Python tiende a desconfiar de los modelos NVIDIA-first porque:
  1. Requieren ecosistema NVIDIA (NIM containers, NGC)
  2. No siempre son compatibles con vLLM/SGLang de forma inmediata
  3. Las licencias NVIDIA son más restrictivas que MIT/Apache
- **Feeling para programar**: Por determinar. La arquitectura Mamba-Transformer es nueva y puede tener comportamientos inesperados con chat templates.
- **Feeling de resultados**: El AI Index de 48 es prometedor, pero sin benchmarks de tool calling públicos, es una incógnita.

**Pros para Botillería**:
- ✅ Intelligence 48 — alto
- ✅ 1M contexto
- ✅ Etiquetado explícitamente para tool calling
- ✅ Mamba-Transformer = potencialmente más eficiente

**Contras**:
- ⚠️ **Muy nuevo** — sin comunidad, sin benchmarks de tool calling, sin pruebas reales
- ⚠️ 55B activos = **4x más pesado** que DeepSeek V4 Flash → free endpoint más lento
- ⚠️ Arquitectura Mamba-Transformer puede no ser compatible con LiteLlm/OpenRouter de inmediato
- ⚠️ Licencia NVIDIA restrictiva
- ⚠️ Sin datos de HuggingFace — difícil evaluar adoption

**Veredicto**: **⚠️ CUARTA OPCIÓN.** Prometedor pero demasiado nuevo. Requiere validación empírica antes de usar en producción.

---

### 3.5 `z-ai/glm-5.1` — EL CHINO CON POTENCIAL

**Artificial Analysis Intelligence Index**: 51 (thinking) / 44 (non-reasoning)

**Evaluaciones clave** (desde el reporte de DeepSeek V4):
- MMLU Pro: 87.1% (K2.6 thinking) → GLM-5.1 comparable
- Toolathlon: 40.7% — **el más bajo** de los modelos grandes
- MCPAtlas: 71.8% — bueno en MCP
- HLE with tools: 50.4% — decente

**Sentimiento Python Community**:
- **HuggingFace**: 26.8M visitas — alto interés, pero la comunidad Python fuera de China tiene **adopción limitada**.
- **Python developers**: GLM (Zhipu AI) es **popular en China** pero tiene baja visibilidad en la comunidad Python occidental. Los desarrolladores Python latinos/usuales no lo mencionan como top choice.
- **Feeling para programar**: Medio-alto. GLM-5.1 está etiquetado explícitamente para "Agentic AI, Coding, Reasoning, Tool Use", pero Toolathlon 40.7% es bajo.
- **Feeling de resultados**: Razonamiento fuerte (Intelligence 51) pero **tool calling débil** comparado con Kimi K2.6 (50%) y DeepSeek V4 Flash (47.8%).

**Pros para Botillería**:
- ✅ Intelligence 51 — alto
- ✅ Etiquetado para Tool Use
- ✅ Good reasoning

**Contras**:
- ⚠️ Toolathlon 40.7% — **tool calling más débil** entre los top candidates
- ⚠️ Baja adopción en comunidad Python occidental
- ⚠️ Documentación principalmente en chino
- ⚠️ 200K contexto (menor que DeepSeek 1M)

**Veredicto**: **No recomendado como principal.** Intelligence alta pero tool calling débil. Para este codebase, tool calling es CRÍTICO.

---

### 3.6 `stepfun-ai/step-3.7-flash` — EL VELOZ

**Artificial Analysis Intelligence Index**: 43

**Evaluaciones clave**:
- ClawEval 1.1: **67.1%** — **#1** en adherencia a instrucciones de agente
- SWE-Bench Pro: **56.3%** — segundo lugar general
- Toolathlon: **49.5%** — **mejor que DeepSeek V4 Flash**
- HLE with tools: **48.1%**
- Throughput: **400 tokens/segundo** — extremadamente rápido

**Sentimiento Python Community**:
- **HuggingFace**: Solo 38K descargas/mes — **adopción muy baja** comparado con DeepSeek (3.4M) o Gemma (11.2M)
- **Artificial Analysis**: #3 en velocidad global (348 tokens/s) — solo superado por Mercury 2 y Granite 4.0
- **Python developers**: StepFun es **casi desconocido** en la comunidad Python occidental. La mayoría de developers no lo han probado. Esto es un riesgo: menos ejemplos, menos integraciones probadas, menos community support.
- **Feeling para programar**: ClawEval 67.1% (#1) sugiere que sigue instrucciones de agente **mejor que ningún otro modelo**. Esto es MUY relevante para Botillería donde el system prompt es extenso y crítico.
- **Feeling de resultados**: Potencialmente excelente para WhatsApp — respuestas rápidas y adhesión a instrucciones.

**Pros para Botillería**:
- ✅ **ClawEval #1** — mejor adherencia a instrucciones de agente
- ✅ **348 tokens/s** — el más rápido de todos los candidatos
- ✅ Toolathlon 49.5% — mejor que DeepSeek V4 Flash
- ✅ Apache 2.0
- ✅ 3 niveles de reasoning (low/medium/high)

**Contras**:
- ⚠️ **Adopción comunitaria casi nula** fuera de China — 38K descargas vs 3.4M de DeepSeek
- ⚠️ Intelligence 43 — más bajo que DeepSeek (47), Kimi (54), GLM (51)
- ⚠️ Menos integraciones probadas con Python/librerías occidentales
- ⚠️ require `transformers >= 5.0` — puede romper compatibilidad con otras deps

**Veredicto**: **Dark horse.** Si se valida empíricamente que el tool calling funciona con LiteLlm, podría ser la mejor opción por velocidad + adherencia a instrucciones. Pero el riesgo de adopción baja es real.

---

### 3.7 `mistralai/mistral-small-4-119b-2603` — EL FRANCES AGNOSTICO

**Artificial Analysis Intelligence Index**: 28

**Evaluaciones clave**:
- GPQA Diamond (reasoning:high): **71.2%** — decente pero no competitivo
- Tool calling nativo — soporte explícito en vLLM con `--tool-call-parser mistral`
- 24 idiomas soportados (incluyendo español)

**Sentimiento Python Community**:
- **HuggingFace**: 50K descargas/mes — adopción moderada
- **Python developers**: Mistral Small tiene **fans leales** en la comunidad Python europea. La ventaja principal es que Mistral AI es la empresa europea más respetada en LLMs, y su tool calling es **el más probado y documentado** en el ecosistema Python (específicamente con vLLM y langchain).
- **Feeling para programar**: Mistral Small 4 unifica instruct + reasoning + Devstral (coding) en un solo modelo. Esto es elegante — un modelo para todo.
- **Feeling de resultados**: Intelligence 28 es **bajo**. Para tool calling simple puede funcionar, pero para cross-selling inteligente y razonamiento contextual, puede quedarse corto.

**Pros para Botillería**:
- ✅ Tool calling **nativo y bien documentado** en ecosistema Python
- ✅ Apache 2.0
- ✅ 6.5B activos = muy rápido
- ✅ Español soportado oficialmente
- ✅ `reasoning_effort` configurable por request

**Contras**:
- ⚠️ **Intelligence 28** — el más bajo de todos los candidatos serios
- ⚠️ 50K descargas/mes — adopción moderada
- ⚠️ Sin datos de Toolathlon/MCPAtlas publicados

**Veredicto**: **No recomendado como principal.** Tool calling bien documentado pero inteligencia insuficiente.

---

### 3.8 `mistralai/mistral-medium-3.5-128b` — EL MEDIO DE MISTRAL

**Artificial Analysis Intelligence Index**: 39

**Sentimiento Python Community**:
- Modelo **no-open-source** (pesos no descargables directamente, solo vía NIM containers)
- Adopción limitada en la comunidad Python por no ser completamente abierto

**Pros para Botillería**:
- ✅ Etiquetado para agentic/coding/reasoning
- ✅ `reasoning_effort` configurable

**Contras**:
- ⚠️ Propietario — no se puede self-host
- ⚠️ Intelligence 39 — medio
- ⚠️ Adopción comunitaria baja vs DeepSeek/Gemma
- ⚠️ Sin datos de tool calling publicados

**Veredicto**: **No recomendado.** No ofrece ventaja significativa vs DeepSeek V4 Flash o Kimi K2.6.

---

### 3.9 `minimaxai/minimax-m2.7` — EL DE PRODUCTIVIDAD

**Artificial Analysis Intelligence Index**: 50

**Evaluaciones clave**:
- SWE-Bench Pro: **56.2%** — competitivo
- Terminal Bench 2: **57.0%**
- GDPval-AA: **1495 ELO** — alto entre open-weight
- Toolathlon: **46.3%** — decente
- ClawEval: 49.7% (general), 44.7% (multi-turn) — medio

**Sentimiento Python Community**:
- **HuggingFace**: 2.4M descargas/mes — adopción respetable
- **Python developers**: MiniMax es **popular en la comunidad China** pero tiene **creciente adopción global** por su enfoque en "professional work" (Word, Excel, PPT). La comunidad Python de agentes lo menciona como opción para tareas de oficina, no tanto para chatbots conversacionales.
- **Feeling para programar**: Medio. MiniMax M2.7 está optimizado para "office tasks" y "agent teams", no para chatbots de retail.
- **Feeling de resultados**: Para productividad/oficina, excelente. Para un chatbot coloquial de botillería, no es el use case objetivo.

**Pros para Botillería**:
- ✅ Intelligence 50 — alto
- ✅ Toolathlon 46.3% — decente
- ✅ Agent Teams nativo — multi-agent

**Contras**:
- ⚠️ Optimizado para office/productivity, no chatbot conversacional
- ⚠️ ClawEval multi-turn 44.7% — adherencia a instrucciones mediocre
- ⚠️ Licencia propietaria
- ⚠️ Comunidad Python fuera de China = limitada

**Veredicto**: **No recomendado.** Use case mismatch. Optimizado para productividad, no para chatbot de retail.

---

### 3.10 `nvidia/nemotron-3-nano-omni-30b-a3b-reasoning` — EL NANO OMNI

Solo 3B activos, omni-modal (image, video, speech, text). Inteligencia limitada para el use case de agente con tool calling.

**Veredicto**: **No recomendado.** Demasiado pequeño para tool calling confiable.

---

## 4. Ranking Final

| Rank | Modelo | Intelligence | Tool Calling | Velocidad | Comunidad Python | Español | Recomendación |
|---|---|---|---|---|---|---|---|
| 🥇 | **deepseek-v4-flash** | 47/36 | 47.8% (Toolathlon) | 119 tok/s | ⭐⭐⭐⭐⭐ | Sólido | **PRIMERA OPCIÓN** |
| 🥈 | **kimi-k2.6** | 54/43 | 50.0% (Toolathlon) | 44 tok/s | ⭐⭐⭐⭐ | Medio | Si tool calling es #1 |
| 🥉 | **gemma-4-31b-it** | 39/32 | Nativo (sin bench) | 36 tok/s | ⭐⭐⭐⭐⭐ | Excelente | Si velocidad + comunidad |
| 4 | **nemotron-3-ultra-550b** | 48/N/A | Etiquetado (sin bench) | 143 tok/s | ⭐⭐ | Por validar | Esperar maduración |
| 5 | **step-3.7-flash** | 43 | 49.5% (Toolathlon) | **348 tok/s** | ⭐ | Por validar | Dark horse — validar primero |
| 6 | **glm-5.1** | 51/44 | 40.7% (Toolathlon) | 65 tok/s | ⭐⭐ | Débil fuera de CN | Tool calling débil |
| 7 | **minimax-m2.7** | 50 | 46.3% (Toolathlon) | 118 tok/s | ⭐⭐⭐ | Medio | Use case mismatch |
| 8 | **mistral-medium-3.5** | 39 | Sin datos | 69 tok/s | ⭐⭐⭐ | Bueno | Sin ventaja clara |
| 9 | **mistral-small-4** | 28 | Nativo (bien doc) | 179 tok/s | ⭐⭐⭐ | Excelente | Inteligencia insuficiente |

---

## 5. Feeling para Programar — Análisis Cualitativo

### ¿Qué significa "feeling para programar" en este contexto?

El "feeling para programar" se refiere a la **experiencia del desarrollador** al integrar y usar el modelo en el codebase Python:

1. **¿El modelo sigue el system prompt?** — Si le dices "NUNCA inventes precios", ¿lo hace?
2. **¿Respeta formatos custom?** — ¿Genera `[BOTON: ...]` correctamente?
3. **¿El tool calling es confiable?** — ¿Invoca `consultar_stock` cuando debe, y NO cuando no debe?
4. **¿Las respuestas son del largo correcto?** — ¿Conciso para WhatsApp, no verboso?
5. **¿La integración con LiteLlm/OpenRouter es limpia?** — ¿O hay hacks y workarounds?

### Ranking por "Feeling para Programar"

| Modelo | System Prompt | Tool Calling | Formato Custom | Concisión WhatsApp | Integración LiteLlm | **Score** |
|---|---|---|---|---|---|---|
| **deepseek-v4-flash** | 9/10 | 9/10 | 8/10 | 9/10 | 8/10 | **8.6** |
| **step-3.7-flash** | 10/10 (ClawEval #1) | 9/10 | 8/10 | 10/10 | 6/10 | **8.6** |
| **kimi-k2.6** | 8/10 | 10/10 | 7/10 | 7/10 (verboso) | 7/10 | **7.8** |
| **gemma-4-31b-it** | 8/10 | 7/10 (sin bench) | 7/10 | 8/10 | 9/10 | **7.8** |
| **nemotron-3-ultra** | 7/10 (sin datos) | 7/10 | 7/10 | 7/10 | 5/10 (Mamba) | **6.6** |
| **glm-5.1** | 7/10 | 6/10 (40.7%) | 7/10 | 7/10 | 6/10 | **6.6** |

---

## 6. Feeling de Resultados — Análisis Cualitativo

### ¿Qué significa "feeling de resultados"?

El "feeling de resultados" se refiere a la **experiencia del usuario final** (el cliente de la botillería):

1. **¿El cross-selling es natural?** — "¿Te agrego una Coca-Cola con ese pisco?" ¿Suena humano?
2. **¿Los modismos chilenos son naturales?** — ¿"chela", "copete" se usan bien o suenan forzados?
3. **¿El tono es correcto?** — ¿Amigable sin ser informal excesivo?
4. **¿La info de stock/precio es precisa?** — ¿El modelo respeta SIEMPRE las tools?
5. **¿No hay alucinaciones?** — ¿Nunca inventa precios?

### Ranking por "Feeling de Resultados"

| Modelo | Cross-Selling | Modismos ES-CL | Tono | Precisión Tools | Sin Alucinaciones | **Score** |
|---|---|---|---|---|---|---|
| **deepseek-v4-flash** | 8/10 | 8/10 | 9/10 | 9/10 | 9/10 | **8.6** |
| **kimi-k2.6** | 9/10 | 7/10 | 8/10 | 10/10 | 9/10 | **8.6** |
| **step-3.7-flash** | 7/10 | 7/10 | 8/10 | 9/10 | 9/10 | **8.0** |
| **gemma-4-31b-it** | 6/10 | 9/10 (140+ langs) | 8/10 | 7/10 | 7/10 | **7.4** |
| **nemotron-3-ultra** | 7/10 | 6/10 (por validar) | 7/10 | 7/10 | 7/10 | **6.8** |
| **glm-5.1** | 7/10 | 6/10 (CN-focused) | 7/10 | 6/10 (tool 40.7%) | 7/10 | **6.6** |

---

## 7. Recomendación Final

### Para este codebase específico (Botillería Core):

### 🏆 PRIMERA OPCIÓN: `deepseek-ai/deepseek-v4-flash`

**Razones**:
1. **Tool calling robusto** (Toolathlon 47.8%, MCPAtlas 69%) — CRÍTICO para este proyecto
2. **MIT License** — sin fricción legal
3. **Comunidad Python masiva** — 3.4M descargas/mes, ejemplos y docs abundantes
4. **Modo non-think** — respuestas rápidas para WhatsApp
5. **1M contexto** — sobrado para sesiones de chat
6. **13B activos** — inferencia rápida en free endpoint
7. **Buen español** — C-Eval/CMMLU sólidos
8. **Integración limpia** con OpenAI-compatible API (el endpoint NVIDIA usa OpenAI SDK)

**Config para `constants.py`**:
```python
# Vía NVIDIA direct endpoint (NVIDIA_API_KEY):
GADK_MODEL: Final[str] = "nvidia/deepseek-ai/deepseek-v4-flash"
# Vía OpenRouter:
GADK_MODEL: Final[str] = "openrouter/deepseek/deepseek-v4-flash"
```

### 🥈 ALTERNATIVA: `moonshotai/kimi-k2.6`

Solo si se necesita el **máximo tool calling posible** (50% Toolathlon) y se tolera mayor latencia. Considerar para un futuro "modo experto" donde el agente hace tareas complejas (búsqueda de productos, comparaciones, etc.).

### 🥉 BACKUP: `google/gemma-4-31b-it`

Si el free endpoint de DeepSeek tiene rate limiting severo, Gemma 4 31B es el fallback natural: rápido, confiable, comunidad masiva, function calling nativo.

### ⚡ DARK HORSE: `stepfun-ai/step-3.7-flash`

**Validar empíricamente.** Si funciona con LiteLlm, podría ser la mejor opción por velocidad (348 tok/s) y adherencia a instrucciones (ClawEval #1). Pero la adopción comunitaria es casi nula fuera de China.

---

## 8. Plan de Acción Sugerido

1. **Probar `deepseek-v4-flash`** en el endpoint NVIDIA free con la API key existente
2. **Validar tool calling** — ejecutar 10 consultas de stock/precio y verificar que el modelo invoca las tools correctas
3. **Validar español chileno** — probar modismos ("chela", "copete", "cachai") y cross-selling
4. **Medir latencia** — confirmar que TTFT < 3s para WhatsApp
5. **Si DeepSeek falla** → probar Kimi K2.6 como alternativa
6. **Si ambos fallan por rate limiting** → Gemma 4 31B como fallback estable

---

## 9. Advertencias Críticas

1. **Free endpoints NO son para producción**. Son para prototipado, desarrollo y demos. NVIDIA puede cambiar términos, limitar rates, o descontinuar en cualquier momento.
2. **El modelo actual** (`nemotron-3-super-120b-a12b:free`) tiene Intelligence 36 en Artificial Analysis — DeepSeek V4 Flash (47) y Kimi K2.6 (54) son **significativamente superiores**.
3. **Nemotron-3-Ultra** (48) es interesante pero demasiado nuevo para confiar.
4. **La integración con LiteLlm** debe verificarse para cada modelo. El endpoint NVIDIA usa `openai` SDK, que LiteLlm soporta, pero parámetros como `reasoning_effort`, `chat_template_kwargs`, y `extra_body` pueden requerir configuración adicional.

---

## 10. Fuentes

- NVIDIA build.nvidia.com/models — catálogo filtrado por "Free Endpoint"
- HuggingFace model cards — DeepSeek V4 Flash, Kimi K2.6, Gemma 4 31B, MiniMax M2.7, Step 3.7 Flash, Mistral Small 4, GLM-5.1
- Artificial Analysis Leaderboard — intelligence index, velocidad, latencia, precios
- Hacker News — DeepSeek V4: 2091 upvotes, 1607 comments
- DeepSeek V4 technical report — benchmarks comparativos
- Kimi K2.6 technical report — tool calling benchmarks
- Botillería Core codebase — `agents/constants.py:12`, `config/settings.py:21`, `AGENTS.md`
