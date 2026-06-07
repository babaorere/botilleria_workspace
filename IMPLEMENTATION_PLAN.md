# 📋 PLAN DE IMPLEMENTACIÓN — BOTILLERÍA TELEGRAM (USER-FIRST)

Basado en: **PedidosYa / Rappi / Cornershop / Uber Eats Chile** + respuestas del usuario.

---

## 🎯 PRINCIPIOS UX (NO NEGOCIABLES)

| Principio | Regla |
|-----------|-------|
| **1 clic para lo común** | Top 4 acciones en teclado persistente (`ReplyKeyboardMarkup`) |
| **Submenús para lo raro** | `InlineKeyboardMarkup` en chat (desaparecen tras uso) |
| **Cero fatiga** | Máx 4 botones fila × 3 filas = 12 visibles. Nada de scroll infinito |
| **Híbrido real** | Botón → acción inmediata O botón → pregunta NL → botón de confirmación |
| **Contexto chileno** | Labels: "Carro", "Pedir", "Retiro", "Despacho", "¿Abierto?", "Humano" |
| **Estado visible** | Badge en botón: `🛒 Carro (3)` — siempre sabe cuántos items |

---

## ⌨️ ARQUITECTURA DE MENÚS (TELEGRAM)

### **Nivel 1 — Teclado Persistente (`ReplyKeyboardMarkup`)**
Siempre visible abajo. **4 botones fijos + 1 contextual**:

```
┌─────────────┬─────────────┬─────────────┬─────────────┐
│ 🔍  Catálogo │ 🛒 Carro (3) │ 📦 Mis Pedidos │ 👤 Mi Perfil │
├─────────────┴─────────────┴─────────────┴─────────────┤
│              🟢 ABIERTO  •  ¿Necesitas ayuda? 🤝       │
└────────────────────────────────────────────────────────┘
```

- **Catálogo** → abre submenú inline (categorías)
- **Carro (n)** → abre vista carrito inline (editar/cancelar/confirmar)
- **Mis Pedidos** → lista últimos 5 + botón "Ver todos"
- **Mi Perfil** → datos, direcciones, preferencias
- **Fila inferior**: Estado local (🟢/🔴) + botón "Humano" (siempre accesible)

---

### **Nivel 2 — Submenús Inline (`InlineKeyboardMarkup`)**

#### **A. Catálogo → Categorías (max 8 + "Ver todo")**
```
┌──────────────┬──────────────┬──────────────┐
│ 🍺 Cervezas  │ 🍷 Vinos     │ 🥃 Piscos    │
├──────────────┼──────────────┼──────────────┤
│ 🍾 Licores   │ 🥜 Snacks    │ 🧊 Sin Alc.  │
├──────────────┼──────────────┼──────────────┤
│ 🔥 Ofertas   │ 🆕 Nuevos    │ 📋 Ver todo  │
└──────────────┴──────────────┴──────────────┘
```

#### **B. Categoría → Productos (lista compacta, 5 por página)**
```
🍺 CERVEZAS (pág 1/3)
┌─────────────────────────────────────────────┐
│ ▸ Cristal 350cc — $1.200  [+]               │
│ ▸ Kunstmann Torobayo — $2.800  [+]          │
│ ▸ Austral Calafate — $3.100  [+]            │
│ ▸ Heineken 330cc — $1.500  [+]              │
│ ▸ Escudo 350cc — $1.100  [+]                │
├─────────────────────────────────────────────┤
│ ◀ Anterior    Pág 1/3    Siguiente ▶        │
└─────────────────────────────────────────────┘
```
- Botón `[+]` = agregar 1 al carro (feedback inmediato: "✅ Agregado")
- Tap en nombre → detalle + selector cantidad

#### **C. Carro (vista principal)**
```
🛒 TU CARRO (3 items — $12.450)
┌─────────────────────────────────────────────┐
│ 2× Cristal 350cc        $2.400  [−] [+] [🗑]│
│ 1× Kunstmann Torobayo   $2.800  [−] [+] [🗑]│
│ 3× Maní salado          $7.250  [−] [+] [🗑]│
├─────────────────────────────────────────────┤
│ 💰 Total: $12.450 CLP                        │
├──────────────┬──────────────┬────────────────┤
│ 🗑 Vaciar    │ ✏️ Seguir    │ 🟢 PEDIR AHORA │
│   carro      │  comprando   │   (confirmar)  │
└──────────────┴──────────────┴────────────────┘
```

#### **D. Confirmar Pedido (wizard 3 pasos, 1 por mensaje)**

**Paso 1 — Método:**
```
🚚 ¿CÓMO LO QUIERES?
┌──────────────────┬──────────────────┐
│ 🏪 RETIRO EN LOCAL     🚚 DESPACHO   │
│   (gratis)           ($2.500 / gratis│
│                      sobre $30k)     │
└──────────────────┴──────────────────┘
```

**Paso 2 — Datos (pre-llenados del perfil):**
```
👤 CONFIRMA TUS DATOS
Nombre: Juan Pérez ✓
Teléfono: +56 9 1234 5678 ✓
Dirección: Av. Siempre Viva 123, Santiago ✓
┌──────────────────┬──────────────────┐
│ ✅ TODO BIEN      | ✏️ CAMBIAR DATOS │
└──────────────────┴──────────────────┘
```

**Paso 3 — Confirmación final:**
```
✅ PEDIDO LISTO PARA ENVIAR
🛒 3 items — $12.450 + $0 despacho = $12.450
🏪 Retiro en local
👤 Juan Pérez — +56 9 1234 5678
┌──────────────────────────────────────────┐
│ 🟢 ENVIAR PEDIDO AL LOCAL                │
│ ❌ Cancelar                              │
└──────────────────────────────────────────┘
```

#### **E. Mis Pedidos (lista + acciones)**
```
📦 TUS ÚLTIMOS PEDIDOS
┌─────────────────────────────────────────────┐
│ 🟢 #1245 — $12.450 — RETIRADO  — [Ver] [🔁] │
│ 🟡 #1240 — $28.900 — EN CAMINO — [Ver] [💬] │
│ 🔴 #1235 — $9.800  — CANCELADO — [Ver]      │
├─────────────────────────────────────────────┤
│ 📋 Ver historial completo (últimos 20)      │
└─────────────────────────────────────────────┘
```
- `[🔁]` = Repetir pedido (carga mismo carro)
- `[💬]` = Contactar local sobre este pedido

#### **F. Mi Perfil**
```
👤 MI PERFIL
┌─────────────────────────────────────────────┐
│ 📝 Nombre: Juan Pérez        [Editar]       │
│ 📧 Email: juan@email.cl      [Editar]       │
│ 🆔 RUT: 12.345.678-9         [Editar]       │
│ 📍 Dir. principal: Av. X 123 [Editar]       │
│ 📍 + Agregar otra dirección                 │
├─────────────────────────────────────────────┤
│ 🔔 Notificaciones: ON/OFF                   │
│ 🌙 Modo oscuro: OFF                         │
└─────────────────────────────────────────────┘
```

---

## 🔄 FLUJO HÍBRIDO (BOTÓN ↔ LENGUAJE NATURAL)

| Entrada Usuario | Respuesta Bot | Próximo Paso |
|-----------------|---------------|--------------|
| **Botón "Catálogo"** | Inline categorías | Tap categoría |
| **Escribe "cervezas"** | Inline categorías (filtro) | Tap categoría |
| **Botón `[+]` en producto** | "✅ 1× Cristal agregado" | Carro badge +1 |
| **Escribe "agrega 2 cristal"** | "✅ 2× Cristal agregado" | Carro badge +2 |
| **Botón "Carro (3)"** | Vista carro inline | Edit/Confirmar |
| **Escribe "qué tengo en el carro"** | Vista carro inline | Edit/Confirmar |
| **Botón "Pedir ahora"** | Paso 1: Método | Tap Retiro/Despacho |
| **Escribe "quiero despacho a mi casa"** | Paso 1: auto-selecciona Despacho → Paso 2 | Confirmar datos |
| **Botón "Humano"** | "🤝 Te transfiero con un vendedor..." | Handoff |
| **Escribe "hablar con persona"** | "🤝 Te transfiero con un vendedor..." | Handoff |

**Regla de oro**: *Botón = acción inmediata. Texto NL = atajo al mismo flujo.*

---

## 🏗️ SPRINT PLAN (2 SEMANAS C/U)

### **SPRINT 1 — Core Carro + Menú Persistente (Semanas 1-2)**

| Task | Descripción | Archivos Clave |
|------|-------------|----------------|
| 1.1 | `ReplyKeyboardMarkup` persistente con 4 botones + estado local | `telegram_service.py`, `keyboards.py` (nuevo) |
| 1.2 | `InlineKeyboardMarkup` para categorías (RAG) | `agents/root_agent.py` → nueva tool `mostrar_catalogo()` |
| 1.3 | Vista carro inline: `[−] [+] [🗑]` por item + total | `keyboards.py`, `agregar_al_carrito` tool |
| 1.4 | Badge dinámico en botón "Carro (n)" | `telegram_service.py` (edit_message_reply_markup) |
| 1.5 | Indicador 🟢/🔴 "Abierto/Cerrado" en fila inferior | `get_botilleria_info` tool + keyboard update |
| 1.6 | Tests: agregar/quitar/cantidad/vaciar carro | `tests/test_cart_keyboard.py` |

**Definition of Done**: Usuario navega catálogo → agrega → ve carro → modifica → vacía — todo con botones, sin escribir.

---

### **SPRINT 2 — Wizard Confirmar Pedido + Perfil (Semanas 3-4)**

| Task | Descripción |
|------|-------------|
| 2.1 | Wizard 3 pasos (Método → Datos → Confirmar) con `InlineKeyboardMarkup` |
| 2.2 | Pre-llenado desde perfil BD (nombre, tel, dirección principal) |
| 2.3 | Tool `confirmar_pedido` actualizada: acepta `metodo_entrega`, `direccion`, usa perfil |
| 2.4 | Notificación Telegram al local (formato existente) + limpiar carro |
| 2.5 | Submenú "Mi Perfil": ver/editar nombre, email, RUT, direcciones |
| 2.6 | Tool `actualizar_perfil(campo, valor)` + validación RUT/email |
| 2.7 | Dirección múltiple: "Principal" + "Otras" (selector en paso 2) |

---

### **SPRINT 3 — Mis Pedidos + Repetir + Humano (Semanas 5-6)**

| Task | Descripción |
|------|-------------|
| 3.1 | Submenú "Mis Pedidos": últimos 5 + "Ver todos" (paginado) |
| 3.2 | Detalle pedido: items, total, método, estado, timestamps |
| 3.3 | Botón `[🔁] Repetir` → carga items al carro actual |
| 3.4 | Botón `[💬] Contactar` → abre chat con local (forward al grupo Telegram) |
| 3.5 | Tool `contactar_humano` mejorada: contexto del pedido actual |
| 3.6 | Estados visuales: 🟢 Entregado 🟡 En camino 🔵 Preparando 🔴 Cancelado |

---

### **SPRINT 4 — Búsqueda NL + RAG + Pulido (Semanas 7-8)**

| Task | Descripción |
|------|-------------|
| 4.1 | Tool `buscar_producto_nl(consulta)` → usa RAG (zonas, ofertas, "sin alcohol") |
| 4.2 | Mapeo NL → botones: "cerveza barata" → filtra categoría + precio |
| 4.3 | Autocompletado inline: usuario escribe "cris..." → sugiere "Cristal 350cc" |
| 4.4 | Manejo "fuera de horario": botón "Pedir ahora" → 🔴 "Abierto 10:00-22:00" |
| 4.5 | Métricas: `callback_query` tracking (qué botones usan, cuáles no) |
| 4.6 | A/B interno: botón "Ofertas" vs "Promos" — medir CTR |
| 4.7 | Limpieza: eliminar tools no usadas, consolidar `keyboards.py` |

---

## 📊 MÉTRICAS DE ÉXITO (USER-FIRST)

| Métrica | Target Sprint 4 | Cómo Medir |
|---------|-----------------|------------|
| **Pasos hasta pedido** | ≤ 5 taps | Funnel: Catálogo → Producto → Carro → Método → Confirmar |
| **Tasa abandono carro** | < 20% | (Carros confirmados / Carros abiertos) |
| **Uso botones vs NL** | > 70% botones | `callback_query` count / `message` count |
| **Repetición pedido** | > 30% usuarios | `[🔁] Repetir` clicks / usuarios activos |
| **Handoff humano** | < 10% sesiones | `contactar_humano` / sesiones totales |
| **Tiempo medio pedido** | < 90 seg | Timestamp primer tap → confirmación |

---

## 🗂️ ARCHIVOS NUEVOS / MODIFICAR

```
botilleria_core/
├── keyboards.py                    # NUEVO: todas las factorías de teclados
├── telegram_service.py             # MODIFICAR: edit_message_reply_markup, badges
├── agents/root_agent.py            # MODIFICAR: tools catálogo, carro, perfil, pedidos
├── services/
│   ├── user_service.py             # MODIFICAR: CRUD perfil, direcciones
│   └── conversation_service.py     # MODIFICAR: historial pedidos por usuario
├── models/user.py                  # MODIFICAR: campos perfil, direcciones JSON
└── tests/
    ├── test_keyboards.py           # NUEVO
    ├── test_cart_flow.py           # NUEVO
    └── test_order_wizard.py        # NUEVO
```

---

## ❓ ANTES DE EMPEZAR — CONFIRMACIONES RÁPIDAS

1. **¿Modelo User actual tiene campos `full_name`, `email`, `rut`, `addresses` (JSON)?** Si no, migración BD en Sprint 2.
2. **¿RAG ya expone función `get_delivery_zone(chat_id)` → tarifa/gratis?** Para wizard paso 1.
3. **¿Grupo Telegram del local ya existe?** Para `contactar_humano` forward.
4. **¿Quieres que "Catálogo" muestre TODAS las categorías o solo las que tienen stock > 0?** (Recomiendo: solo stock > 0 + "Ver todo")
5. **¿Formato RUT chileno con puntos/guion (12.345.678-9) o solo dígitos?** Para validación.

---

## ✅ SPRINT 1: TAREAS A IMPLEMENTAR

Comenzando ahora con Sprint 1:
1. Crear `keyboards.py` con factorías de teclados
2. Modificar `telegram_service.py` para manejar teclados persistentes
3. Actualizar `agents/root_agent.py` con tool para mostrar categorías
4. Mejorar `agregar_al_carrito` para devolver feedback inmediato
5. Implementar badge dinámico en botón de carro
6. Añadir indicador de abierto/cerrado
7. Crear tests para validar el flujo

¡Arrancando con Sprint 1 ahora!