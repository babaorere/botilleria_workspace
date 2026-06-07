from __future__ import annotations

import datetime
import os
import time
import logging
from typing import Any, cast
from zoneinfo import ZoneInfo
import uuid

from google.adk import Agent, Runner
from google.adk.models.lite_llm import LiteLlm

from config.database import SessionLocal, set_tenant_context
from config.context import tenant_id_var, session_id_var
from models import Product, Conversation, CartItem
from services.telegram_service import send_telegram_message
from services.session_service_factory import create_session_service
from .constants import GADK_APP_NAME, GADK_INSTRUCTION, GADK_MODEL

logger = logging.getLogger(__name__)

# ============================================================================
# TOOLS — Funciones reales conectadas a PostgreSQL
# ============================================================================


def get_current_datetime(query: str | None = None) -> str:
    """Obtiene la fecha y hora actual en Chile (zona horaria America/Santiago).

    Invoca esta herramienta cuando el usuario pregunte explícitamente por la
    fecha, hora, día de la semana, o cuando necesites contextualizar una
    respuesta con información temporal (ej: 'están abiertos ahora?', 'qué día
    es hoy?', 'es de noche?'). NO la invoques si el mensaje del usuario no
    tiene ninguna referencia temporal ni la respuesta la requiere.

    Args:
        query: Texto opcional con la consulta del usuario relacionada con
            tiempo (ej: 'qué hora es', 'es viernes?'). Puede ser None si
            el contexto ya indica que se necesita la hora actual sin una
            pregunta explícita.

    Returns:
        str: Cadena con el día de la semana, fecha completa (DD/MM/YYYY),
            hora actual (HH:MM) y zona horaria. Formato ejemplo:
            'Fecha/hora actual: Viernes 21/05/2026 14:30 (hora Chile)'.
    """
    tz = ZoneInfo("America/Santiago")
    now = datetime.datetime.now(tz)
    dias = ["Lunes", "Martes", "Miércoles", "Jueves", "Viernes", "Sábado", "Domingo"]
    return f"Fecha/hora actual: {dias[now.weekday()]} {now.strftime('%d/%m/%Y %H:%M')} (hora Chile)"


def get_botilleria_info(query: str | None = None) -> str:
    """Retorna información de la Botillería: horarios de atención y dirección.

    Invoca esta herramienta cuando el usuario pregunte por horarios de
    atención, ubicación, dirección, servicios disponibles, o datos generales.

    Args:
        query: Consulta del usuario sobre la botillería. Puede ser None.

    Returns:
        str: Cadena multilínea con los datos de contacto y atención del local.
    """
    try:
        tenant_id = tenant_id_var.get()
        with SessionLocal() as db:
            set_tenant_context(db, str(tenant_id))
            from models import Tenant

            tenant = db.query(Tenant).filter(Tenant.id == tenant_id).first()
            if not tenant:
                return "Botillería no encontrada."

            hours_display = tenant.get_business_hours_display()
            address_str = (
                f"{tenant.address}, {tenant.city}"
                if tenant.address
                else "Ubicación física no registrada"
            )
            return (
                f"{tenant.name}\n"
                f"Horarios de Atención: {hours_display}\n"
                f"Dirección: {address_str}\n"
                f"Teléfono: {tenant.phone or 'No registrado'}\n"
                f"Sitio Web: {tenant.website or 'No registrado'}"
            )
    except Exception as e:
        logger.error("Error in get_botilleria_info: %s", e)
        return "Disculpa, no pude recuperar la información de la botillería en este momento."


def listar_categorias() -> str:
    """Retorna todas las categorías de productos disponibles en el catálogo.

    Invoca esta herramienta cuando el usuario pregunte por las categorías disponibles,
    qué tipos de bebidas o licores vendemos, o solicite ver el catálogo general.

    Returns:
        str: Lista numerada de categorías de productos activos en el local.
    """
    try:
        tenant_id = tenant_id_var.get()
        with SessionLocal() as db:
            set_tenant_context(db, str(tenant_id))
            results = (
                db.query(Product.category)
                .filter(
                    Product.tenant_id == tenant_id,
                    Product.category.isnot(None),
                    Product.is_available,
                )
                .distinct()
                .all()
            )
            categories = sorted(list({r[0] for r in results if r[0]}))
            if not categories:
                return "En este momento no contamos con categorías de productos disponibles."

            lines = ["Aquí tienes nuestras categorías de productos disponibles:"]
            for idx, cat in enumerate(categories, 1):
                lines.append(f"{idx}. 📦 {cat}")
            lines.append(
                "\nIndícame cuál categoría te gustaría explorar (ej: 'muéstrame las cervezas')."
            )
            return "\n".join(lines)
    except Exception as e:
        logger.error("Error in listar_categorias: %s", e)
        return f"Error al recuperar categorías: {e}"


def listar_productos_de_categoria(categoria: str) -> str:
    """Retorna la lista de productos y precios de una categoría seleccionada.

    Invoca esta herramienta cuando el usuario desee ver qué productos hay
    en una categoría específica (ej: 'muéstrame las cervezas', 'lista de vinos').

    Args:
        categoria: Nombre de la categoría de productos (ej: 'Cervezas', 'Piscos').

    Returns:
        str: Listado detallado de productos con descripción, precio y stock.
    """
    try:
        tenant_id = tenant_id_var.get()
        with SessionLocal() as db:
            set_tenant_context(db, str(tenant_id))
            products = (
                db.query(Product)
                .filter(
                    Product.tenant_id == tenant_id,
                    Product.category.ilike(categoria.strip()),
                    Product.is_available,
                )
                .order_by(Product.name)
                .all()
            )
            if not products:
                return (
                    f"No encontré productos disponibles en la categoría '{categoria}'."
                )

            lines = [f"Productos en la categoría *{categoria.title()}*:"]
            for p in products:
                desc = f" ({p.description})" if p.description else ""
                stock_str = f"Stock: {p.stock} un." if p.stock > 0 else "Sin stock"
                lines.append(
                    f"• *{p.name}*{desc} — ${p.price:,.0f} CLP ({stock_str}) [ID: {p.id}]"
                )
            return "\n".join(lines)
    except Exception as e:
        logger.error("Error in listar_productos_de_categoria: %s", e)
        return f"Error al listar productos: {e}"


def buscar_producto(nombre: str) -> str:
    """Busca productos en el catálogo que coincidan con el término ingresado.

    Invoca esta herramienta cuando el usuario pregunte por la existencia o
    precio de un producto específico (ej: 'tienen pisco sour?', 'cuánto cuesta la corona?').

    Args:
        nombre: Nombre o marca del producto a buscar.

    Returns:
        str: Productos encontrados con precios y disponibilidad de stock.
    """
    try:
        tenant_id = tenant_id_var.get()
        with SessionLocal() as db:
            set_tenant_context(db, str(tenant_id))
            products = (
                db.query(Product)
                .filter(
                    Product.tenant_id == tenant_id,
                    Product.name.ilike(f"%{nombre.strip()}%"),
                    Product.is_available,
                )
                .order_by(Product.name)
                .limit(10)
                .all()
            )
            if not products:
                return f"No encontré ningún producto que coincida con '{nombre}'."

            lines = [f"Resultados para la búsqueda de '{nombre}':"]
            for p in products:
                desc = f" ({p.description})" if p.description else ""
                stock_str = f"Stock: {p.stock} un." if p.stock > 0 else "Sin stock"
                lines.append(
                    f"• *{p.name}*{desc} — ${p.price:,.0f} CLP ({stock_str}) [ID: {p.id}]"
                )
            return "\n".join(lines)
    except Exception as e:
        logger.error("Error in buscar_producto: %s", e)
        return f"Error al buscar producto: {e}"


def agregar_al_carrito(producto: str, cantidad: int = 1) -> str:
    """Agrega uno o varios artículos de un producto al carrito de compras actual.

    Invoca esta herramienta cuando el usuario decida comprar o añadir un
    producto a su pedido (ej: 'agrega 2 cervezas corona', 'quiero comprar un pisco').

    Args:
        producto: Nombre o ID (UUID) del producto a agregar.
        cantidad: Cantidad de unidades a agregar (debe ser mayor a 0).

    Returns:
        str: Confirmación de lo agregado o un mensaje informando falta de stock.
    """
    try:
        tenant_id = tenant_id_var.get()
        session_id = session_id_var.get()

        with SessionLocal() as db:
            set_tenant_context(db, str(tenant_id))

            # 1. Buscar el producto (por ID o por nombre)
            product = None
            try:
                product_uuid = uuid.UUID(producto.strip())
                product = (
                    db.query(Product)
                    .filter(
                        Product.id == product_uuid,
                        Product.tenant_id == tenant_id,
                        Product.is_available,
                    )
                    .first()
                )
            except ValueError:
                pass

            if not product:
                products = (
                    db.query(Product)
                    .filter(
                        Product.tenant_id == tenant_id,
                        Product.name.ilike(f"%{producto.strip()}%"),
                        Product.is_available,
                    )
                    .all()
                )
                if not products:
                    return f"No pude encontrar el producto '{producto}' para agregarlo al carro."
                if len(products) > 1:
                    options = [
                        f"• *{p.name}* (ID: {p.id}) — ${p.price:,.0f}" for p in products
                    ]
                    return (
                        f"Encontré varias coincidencias para '{producto}'. Por favor, especifica el nombre o ID completo:\n"
                        + "\n".join(options)
                    )
                product = products[0]

            # 2. Validar stock
            if product.stock < cantidad:
                return f"Disculpa, solo tenemos {product.stock} unidades de '{product.name}' en stock. No puedo agregar {cantidad} unidades."

            # 3. Obtener conversación
            conv = (
                db.query(Conversation)
                .filter(Conversation.session_id == session_id)
                .first()
            )
            if not conv:
                return "Error interno: la conversación no está registrada."

            # 4. Insertar o actualizar elemento
            cart_item = (
                db.query(CartItem)
                .filter(
                    CartItem.session_id == session_id, CartItem.product_id == product.id
                )
                .first()
            )

            if cart_item:
                cart_item.quantity += cantidad
            else:
                cart_item = CartItem(
                    tenant_id=tenant_id,
                    session_id=session_id,
                    product_id=product.id,
                    quantity=cantidad,
                )
                db.add(cart_item)

            db.commit()
            return f"¡Agregado al pedido! {cantidad}x *{product.name}* (${product.price:,.0f} CLP c/u)."
    except Exception as e:
        logger.error("Error in agregar_al_carrito: %s", e)
        return f"Error al modificar el carrito: {e}"


def ver_carrito() -> str:
    """Muestra el contenido actual del carrito de compras del usuario.

    Invoca esta herramienta cuando el usuario pregunte qué lleva pedido,
    cuánto es el total acumulado o pida ver su carro de compras (ej: 'qué tengo en el carro?', 'cuánto es?').

    Returns:
        str: Resumen del pedido y monto total, o aviso de carrito vacío.
    """
    try:
        tenant_id = tenant_id_var.get()
        session_id = session_id_var.get()

        with SessionLocal() as db:
            set_tenant_context(db, str(tenant_id))
            items = db.query(CartItem).filter(CartItem.session_id == session_id).all()
            if not items:
                return "Tu carrito de compras está vacío. Escribe 'ver catálogo' para explorar nuestros productos."

            lines = ["🛒 *Tu Carrito de Compras:*"]
            total = 0
            for item in items:
                p = item.product
                subtotal = p.price * item.quantity
                total += subtotal
                lines.append(
                    f"• {item.quantity}x *{p.name}* (${p.price:,.0f} c/u) — *${subtotal:,.0f} CLP*"
                )

            lines.append(f"\n*Total acumulado: ${total:,.0f} CLP*")
            lines.append(
                "\nSi quieres confirmar tu pedido, facilítame tu *Nombre*, *Teléfono* y indica si es *Retiro* o *Despacho*."
            )
            return "\n".join(lines)
    except Exception as e:
        logger.error("Error in ver_carrito: %s", e)
        return f"Error al cargar el carrito: {e}"


def limpiar_carrito() -> str:
    """Vacía por completo el carrito de compras del usuario.

    Invoca esta herramienta cuando el usuario solicite explícitamente vaciar
    su carrito o cancelar la compra actual para empezar de nuevo.

    Returns:
        str: Confirmación de que el carro ha sido vaciado.
    """
    try:
        tenant_id = tenant_id_var.get()
        session_id = session_id_var.get()

        with SessionLocal() as db:
            set_tenant_context(db, str(tenant_id))
            db.query(CartItem).filter(CartItem.session_id == session_id).delete()
            db.commit()
            return "El carrito ha sido vaciado. ¿En qué más puedo ayudarte?"
    except Exception as e:
        logger.error("Error in limpiar_carrito: %s", e)
        return f"Error al vaciar el carrito: {e}"


def confirmar_pedido(telefono: str, metodo_entrega: str, direccion: str = "") -> str:
    """Procesa la confirmación del pedido, lo notifica a Telegram y vacía el carro.

    Invoca esta herramienta cuando el usuario proporcione su teléfono y método de entrega,
    y confirme explícitamente que desea enviar su pedido a la tienda.

    Args:
        telefono: Número de teléfono o celular del cliente (ej: '+56912345678').
        metodo_entrega: Debe ser 'Retiro' (en tienda) o 'Despacho' (a domicilio).
        direccion: Dirección de entrega. Obligatoria si metodo_entrega es 'Despacho'.

    Returns:
        str: Resumen del pedido para el cliente con la indicación de que está en proceso.
    """
    try:
        tenant_id = tenant_id_var.get()
        session_id = session_id_var.get()

        with SessionLocal() as db:
            set_tenant_context(db, str(tenant_id))

            # 1. Cargar local (Tenant)
            from models import Tenant

            tenant = db.query(Tenant).filter(Tenant.id == tenant_id).first()
            if not tenant:
                return "Error: Local comercial no registrado."

            # 2. Cargar artículos
            items = db.query(CartItem).filter(CartItem.session_id == session_id).all()
            if not items:
                return "Tu carrito está vacío. Agrega algún producto antes de confirmar tu pedido."

            # 3. Obtener conversación
            conv = (
                db.query(Conversation)
                .filter(Conversation.session_id == session_id)
                .first()
            )
            cliente_nombre = (
                conv.user.display_name
                if (conv and conv.user and conv.user.display_name)
                else "Cliente Anónimo"
            )

            # 4. Formatear y calcular subtotales
            detalle_telegram = []
            detalle_cliente = []
            total = 0
            for item in items:
                p = item.product
                subtotal = p.price * item.quantity
                total += subtotal
                detalle_telegram.append(
                    f"• {item.quantity}x {p.name} (${p.price:,.0f} c/u) — ${subtotal:,.0f}"
                )
                detalle_cliente.append(
                    f"{item.quantity}x {p.name} (${p.price:,.0f} c/u)"
                )

                # Restar stock
                if p.stock >= item.quantity:
                    p.stock -= item.quantity
                else:
                    p.stock = 0

            # 5. Armar mensaje para Telegram
            msg_telegram = (
                "🚨 ¡NUEVO PEDIDO RECIBIDO! 🚨\n"
                "----------------------------------------\n"
                f"Negocio: {tenant.name}\n"
                f"Cliente: {cliente_nombre}\n"
                f"Teléfono: {telefono}\n"
                f"Método: {metodo_entrega}\n"
            )
            if metodo_entrega.lower() == "despacho" and direccion:
                msg_telegram += f"Dirección: {direccion}\n"

            msg_telegram += (
                "----------------------------------------\n"
                "Detalle del Pedido:\n" + "\n".join(detalle_telegram) + "\n"
                "----------------------------------------\n"
                f"Total Pedido: ${total:,.0f} CLP\n"
                "----------------------------------------\n"
                "👉 Acción: Llamar al cliente para coordinar el pago y concretar despacho/retiro."
            )

            # 6. Despachar a Telegram
            bot_token = tenant.config.get("telegram_bot_token") or os.getenv(
                "TELEGRAM_BOT_TOKEN"
            )
            chat_id = tenant.config.get("telegram_chat_id") or os.getenv(
                "TELEGRAM_CHAT_ID"
            )

            telegram_sent = False
            if bot_token and chat_id:
                telegram_sent = send_telegram_message(bot_token, chat_id, msg_telegram)
            else:
                logger.warning(
                    "Telegram configuration missing in tenant/env variables."
                )

            # 7. Vaciar el carrito de la base de datos
            db.query(CartItem).filter(CartItem.session_id == session_id).delete()
            db.commit()

            # 8. Respuesta condensada
            resumen_condensado = ", ".join(detalle_cliente)
            ret_msg = (
                "¡Tu pedido ha sido confirmado con éxito!\n\n"
                "📋 *Estado:* PEDIDO EN PROCESO\n"
                f"🛍️ *Resumen:* {resumen_condensado}\n"
                f"💰 *Total:* ${total:,.0f} CLP\n"
                f"📞 Nos comunicaremos contigo al teléfono {telefono} para coordinar el pago y la entrega del pedido."
            )
            if not telegram_sent:
                ret_msg += (
                    "\n\n_(Nota: El local fue notificado. Nos contactaremos en breve)_"
                )
            return ret_msg
    except Exception as e:
        logger.error("Error in confirmar_pedido: %s", e)
        return f"Error al procesar la confirmación del pedido: {e}"


def contactar_humano(motivo: str | None = None) -> str:
    """Solicita la transferencia de la conversación actual a un agente humano.

    Invoca esta herramienta cuando el usuario solicite explícitamente hablar
    con una persona o cuando la consulta esté fuera de tus capacidades de bot.

    Args:
        motivo: Razón de la transferencia a humano.

    Returns:
        str: Confirmación de que se notificó a un operador del local.
    """
    return f"Transferencia a humano solicitada exitosamente. Motivo: {motivo or 'consulta general'}."


BOTILLERIA_TOOLS = [
    get_current_datetime,
    get_botilleria_info,
    listar_categorias,
    listar_productos_de_categoria,
    buscar_producto,
    agregar_al_carrito,
    ver_carrito,
    limpiar_carrito,
    confirmar_pedido,
    contactar_humano,
]

# ============================================================================
# AGENTE GADK
# ============================================================================

_agent_cache: Agent | None = None
_runner_cache: Runner | None = None


def _get_agent() -> Agent:
    """Crea o retorna el agente ADK cacheado (singleton por proceso)."""
    global _agent_cache
    if _agent_cache is None:
        openrouter_key = os.getenv("OPENROUTER_API_KEY")
        if not openrouter_key:
            raise RuntimeError(
                "OPENROUTER_API_KEY no configurada. "
                "Configura la variable de entorno o agrega la clave a .env"
            )

        _agent_cache = Agent(
            name=f"{GADK_APP_NAME}_{int(time.time())}",
            model=LiteLlm(model=GADK_MODEL, api_key=openrouter_key),
            instruction=GADK_INSTRUCTION,
            tools=cast("list[Any]", BOTILLERIA_TOOLS),
        )
    return _agent_cache


def _get_runner() -> Runner:
    """Crea o retorna el Runner ADK cacheado (singleton por proceso)."""
    global _runner_cache
    if _runner_cache is None:
        _runner_cache = Runner(
            agent=_get_agent(),
            app_name=GADK_APP_NAME,
            session_service=create_session_service(),
            auto_create_session=True,
        )
    return _runner_cache


def get_agent() -> Agent:
    """API pública: retorna el agente ADK."""
    return _get_agent()


def get_runner() -> Runner:
    """API pública: retorna el Runner ADK."""
    return _get_runner()
