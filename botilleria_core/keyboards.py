"""
Keyboard factories for Telegram bot interface.
Provides ReplyKeyboardMarkup (persistent) and InlineKeyboardMarkup (ephemeral) keyboards.
"""
from __future__ import annotations

from telegram import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton
from typing import List, Optional

from botilleria_core.config.database import SessionLocal
from botilleria_core.config.settings import settings
from botilleria_core.models import Tenant


def get_main_keyboard(tenant_id: int, is_open: bool = True) -> ReplyKeyboardMarkup:
    """
    Create persistent main keyboard with 4 core actions + status/help row.
    
    Layout:
    [🔍 Catálogo] [🛒 Carro] [📦 Mis Pedidos] [👤 Mi Perfil]
    [🟢 ABIERTO] [🤝 Humano]
    
    Args:
        tenant_id: Tenant ID for context
        is_open: Whether business is currently open
    
    Returns:
        ReplyKeyboardMarkup for persistent bottom menu
    """
    status_text = "🟢 ABIERTO" if is_open else "🔴 CERRADO"
    help_text = "🤝 Humano"  # Consistent label
    
    keyboard = [
        [
            KeyboardButton("🔍 Catálogo"),
            KeyboardButton("🛒 Carro"),  # Badge will be updated dynamically
            KeyboardButton("📦 Mis Pedidos"),
            KeyboardButton("👤 Mi Perfil"),
        ],
        [
            KeyboardButton(status_text),
            KeyboardButton(help_text),
        ]
    ]
    
    return ReplyKeyboardMarkup(
        keyboard,
        resize_keyboard=True,
        one_time_keyboard=False,  # Persistent
        input_field_placeholder="Selecciona una opción o escribe tu consulta..."
    )


def get_cart_keyboard(cart_count: int = 0) -> ReplyKeyboardMarkup:
    """
    Update just the cart button badge in main keyboard.
    Called when cart count changes.
    
    Args:
        cart_count: Number of items in cart
    
    Returns:
        ReplyKeyboardMarkup with updated cart button text
    """
    # This will be used to edit the existing keyboard via edit_message_reply_markup
    # We'll reconstruct just the cart button part in the handler
    pass  # Logic handled in telegram_service.py


def get_categories_keyboard(categories: List[str]) -> InlineKeyboardMarkup:
    """
    Create inline keyboard for product categories.
    Max 3 columns, rows as needed.
    
    Args:
        categories: List of category names
    
    Returns:
        InlineKeyboardMarkup with category buttons
    """
    keyboard = []
    row = []
    
    for i, category in enumerate(categories):
        # Emoji mapping for common categories
        emoji_map = {
            "Cervezas": "🍺",
            "Vinos": "🍷",
            "Piscos": "🥃",
            "Licores": "🍾",
            "Snacks": "🥜",
            "Sin Alcohol": "🥤",
            "Ofertas": "🔥",
            "Nuevos": "🆕"
        }
        emoji = emoji_map.get(category, "📦")
        
        row.append(InlineKeyboardButton(
            text=f"{emoji} {category}",
            callback_data=f"category:{category}"
        ))
        
        # Start new row every 3 buttons
        if (i + 1) % 3 == 0:
            keyboard.append(row)
            row = []
    
    # Add remaining buttons in last row
    if row:
        keyboard.append(row)
    
    # Add "Ver todo" button if we have categories
    if categories:
        keyboard.append([
            InlineKeyboardButton(
                text="📋 Ver todo",
                callback_data="category:all"
            )
        ])
    
    return InlineKeyboardMarkup(keyboard)


def get_products_keyboard(products: List[dict], page: int = 0, items_per_page: int = 5) -> InlineKeyboardMarkup:
    """
    Create inline keyboard for products in a category.
    Shows product name, price, and [+] button to add to cart.
    
    Args:
        products: List of product dicts with keys: id, name, price, stock
        page: Current page number (0-indexed)
        items_per_page: Number of products per page
    
    Returns:
        InlineKeyboardMarkup with product buttons and pagination
    """
    keyboard = []
    
    # Calculate pagination
    start_idx = page * items_per_page
    end_idx = start_idx + items_per_page
    page_products = products[start_idx:end_idx]
    total_pages = (len(products) + items_per_page - 1) // items_per_page
    
    # Product rows
    for product in page_products:
        stock_status = "✅" if product['stock'] > 0 else "❌"
        button_text = f"{stock_status} {product['name'][:20]}... - ${product['price']:,.0f}"
        
        keyboard.append([
            InlineKeyboardButton(
                text=button_text,
                callback_data=f"product_detail:{product['id']}"
            ),
            InlineKeyboardButton(
                text="[+]",
                callback_data=f"add_to_cart:{product['id']}"
            )
        ])
    
    # Pagination row
    nav_buttons = []
    if page > 0:
        nav_buttons.append(InlineKeyboardButton(
            text="◀ Anterior",
            callback_data=f"products_page:{page-1}"
        ))
    
    nav_buttons.append(InlineKeyboardButton(
        text=f"Pág {page+1}/{total_pages}",
        callback_data="page_info"  # Non-actionable
    ))
    
    if page < total_pages - 1:
        nav_buttons.append(InlineKeyboardButton(
            text="Siguiente ▶",
            callback_data=f"products_page:{page+1}"
        ))
    
    if nav_buttons:
        keyboard.append(nav_buttons)
    
    return InlineKeyboardMarkup(keyboard)


def get_cart_items_keyboard(cart_items: List[dict]) -> InlineKeyboardMarkup:
    """
    Create inline keyboard for viewing/editing cart items.
    Shows each item with [−] [+] [🗑] buttons.
    
    Args:
        cart_items: List of cart item dicts with keys: product_id, name, quantity, price
    
    Returns:
        InlineKeyboardMarkup with cart item controls
    """
    keyboard = []
    
    for item in cart_items:
        # Item row: name, quantity controls, remove
        keyboard.append([
            InlineKeyboardButton(
                text=f"• {item['name'][:15]}...",
                callback_data=f"cart_item_detail:{item['product_id']}"  # Non-actionable, just for detail
            ),
            InlineKeyboardButton(
                text="[−]",
                callback_data=f"cart_remove_one:{item['product_id']}"
            ),
            InlineKeyboardButton(
                text=f"{item['quantity']}",
                callback_data="cart_qty_display"  # Non-actionable
            ),
            InlineKeyboardButton(
                text="[+]",
                callback_data=f"cart_add_one:{item['product_id']}"
            ),
            InlineKeyboardButton(
                text="[🗑]",
                callback_data=f"cart_remove_all:{item['product_id']}"
            )
        ])
    
    # Action row
    keyboard.append([
        InlineKeyboardButton(
            text="🗑 Vaciar Carro",
            callback_data="cart_clear_all"
        ),
        InlineKeyboardButton(
            text="🟢 PEDIR AHORA",
            callback_data="cart_checkout"
        )
    ])
    
    return InlineKeyboardMarkup(keyboard)


def get_order_method_keyboard() -> InlineKeyboardMarkup:
    """
    Keyboard for choosing delivery method (Retiro/Despacho).
    
    Returns:
        InlineKeyboardMarkup with two options
    """
    keyboard = [
        [
            InlineKeyboardButton(
                text="🏪 RETIRO EN LOCAL\n(Gratis)",
                callback_data="method:retiro"
            ),
            InlineKeyboardButton(
                text="🚚 DESPACHO\n($2.500 / gratis > $30k)",
                callback_data="method:despacho"
            )
        ]
    ]
    return InlineKeyboardMarkup(keyboard)


def get_order_confirmation_keyboard() -> InlineKeyboardMarkup:
    """
    Keyboard for final order confirmation.
    
    Returns:
        InlineKeyboardMarkup with Confirm/Cancel
    """
    keyboard = [
        [
            InlineKeyboardButton(
                text="✅ CONFIRMAR PEDIDO",
                callback_data="order_confirm"
            ),
            InlineKeyboardButton(
                text="❌ CANCELAR",
                callback_data="order_cancel"
            )
        ]
    ]
    return InlineKeyboardMarkup(keyboard)


def get_pagination_keyboard(current_page: int, total_pages: int, 
                          prev_callback: str, next_callback: str) -> InlineKeyboardMarkup:
    """
    Generic pagination keyboard.
    
    Args:
        current_page: Current page number (0-indexed)
        total_pages: Total number of pages
        prev_callback: Callback data prefix for previous page
        next_callback: Callback data prefix for next page
    
    Returns:
        InlineKeyboardMarkup with pagination controls
    """
    keyboard = []
    nav_buttons = []
    
    if current_page > 0:
        nav_buttons.append(InlineKeyboardButton(
            text="◀ Anterior",
            callback_data=f"{prev_callback}:{current_page-1}"
        ))
    
    nav_buttons.append(InlineKeyboardButton(
        text=f"Pág {current_page+1}/{total_pages}",
        callback_data="page_info"  # Non-actionable
    ))
    
    if current_page < total_pages - 1:
        nav_buttons.append(InlineKeyboardButton(
            text="Siguiente ▶",
            callback_data=f"{next_callback}:{current_page+1}"
        ))
    
    if nav_buttons:
        keyboard.append(nav_buttons)
    
    return InlineKeyboardMarkup(keyboard)


def get_profile_keyboard() -> InlineKeyboardMarkup:
    """
    Keyboard for profile management options.
    
    Returns:
        InlineKeyboardMarkup with profile actions
    """
    keyboard = [
        [
            InlineKeyboardButton(text="📝 Editar Nombre", callback_data="profile_edit:name"),
            InlineKeyboardButton(text="📧 Editar Email", callback_data="profile_edit:email"),
        ],
        [
            InlineKeyboardButton(text="🆔 Editar RUT", callback_data="profile_edit:rut"),
            InlineKeyboardButton(text="📍 Editar Dirección", callback_data="profile_edit:address"),
        ],
        [
            InlineKeyboardButton(text="📍 + Agregar Dirección", callback_data="profile_add_address"),
            InlineKeyboardButton(text="🔔 Notificaciones", callback_data="profile_toggle_notifications"),
        ],
        [
            InlineKeyboardButton(text="🗑 Eliminar Cuenta", callback_data="profile_delete"),
            InlineKeyboardButton(text="🔙 Volver al Menú", callback_data="profile_back_to_main"),
        ]
    ]
    return InlineKeyboardMarkup(keyboard)


def get_order_history_keyboard(orders: List[dict], page: int = 0, items_per_page: int = 5) -> InlineKeyboardMarkup:
    """
    Keyboard for order history list.
    
    Args:
        orders: List of order dicts
        page: Current page number
        items_per_page: Orders per page
    
    Returns:
        InlineKeyboardMarkup with order items and actions
    """
    keyboard = []
    
    # Calculate pagination
    start_idx = page * items_per_page
    end_idx = start_idx + items_per_page
    page_orders = orders[start_idx:end_idx]
    total_pages = (len(orders) + items_per_page - 1) // items_per_page
    
    # Order rows
    for order in page_orders:
        status_emoji = {
            "pendiente": "🟡",
            "preparando": "🔵",
            "en_camino": "🟠",
            "entregado": "🟢",
            "cancelado": "🔴"
        }.get(order.get('status', 'pendiente'), "⚪")
        
        keyboard.append([
            InlineKeyboardButton(
                text=f"{status_emoji} #{order['id']} - ${order['total']:,.0f}",
                callback_data=f"order_detail:{order['id']}"
            ),
            InlineKeyboardButton(
                text="[🔁] Repetir",
                callback_data=f"order_repeat:{order['id']}"
            ) if order.get('status') in ['entregado', 'preparando'] else InlineKeyboardButton(
                text=" ",  # Disabled
                callback_data="disabled"
            )
        ])
    
    # Pagination
    if total_pages > 1:
        nav_buttons = []
        if page > 0:
            nav_buttons.append(InlineKeyboardButton(
                text="◀ Anterior",
                callback_data=f"history_page:{page-1}"
            ))
        
        nav_buttons.append(InlineKeyboardButton(
            text=f"Pág {page+1}/{total_pages}",
            callback_data="page_info"
        ))
        
        if page < total_pages - 1:
            nav_buttons.append(InlineKeyboardButton(
                text="Siguiente ▶",
                callback_data=f"history_page:{page+1}"
            ))
        
        if nav_buttons:
            keyboard.append(nav_buttons)
    
    # Action buttons
    keyboard.append([
        InlineKeyboardButton(text="📋 Ver Todo (últimos 20)", callback_data="history_view_all"),
        InlineKeyboardButton(text="🔙 Volver", callback_data="history_back_to_main")
    ])
    
    return InlineKeyboardMarkup(keyboard)


def get_empty_state_keyboard() -> InlineKeyboardMarkup:
    """
    Keyboard for empty states (empty cart, no orders, etc.).
    
    Returns:
        InlineKeyboardMarkup with helpful actions
    """
    keyboard = [
        [
            InlineKeyboardButton(text="🔍 Explorar Catálogo", callback_data="browse_categories"),
            InlineKeyboardButton(text="🛒 Ver Carro", callback_data="view_cart")
        ],
        [
            InlineKeyboardButton(text="👤 Mi Perfil", callback_data="view_profile"),
            InlineKeyboardButton(text="🤝 Contactar Humano", callback_data="contact_human")
        ]
    ]
    return InlineKeyboardMarkup(keyboard)


# Helper functions for dynamic updates

def get_cart_button_text(cart_count: int) -> str:
    """
    Get the text for the cart button with badge.
    
    Args:
        cart_count: Number of items in cart
    
    Returns:
        Formatted string for cart button
    """
    if cart_count > 0:
        return f"🛒 Carro ({cart_count})"
    else:
        return "🛒 Carro"


def get_status_button_text(is_open: bool) -> str:
    """
    Get the text for the status button.
    
    Args:
        is_open: Whether business is open
    
    Returns:
        Formatted string for status button
    """
    return "🟢 ABIERTO" if is_open else "🔴 CERRADO"


async def update_tenant_status(tenant_id: int) -> bool:
    """
    Check if tenant is currently open based on business hours.
    
    Args:
        tenant_id: Tenant ID to check
    
    Returns:
        True if open, False if closed
    """
    try:
        with SessionLocal() as db:
            tenant = db.query(Tenant).filter(Tenant.id == tenant_id).first()
            if not tenant:
                return False
            
            # Simple check - in reality this would use tenant's business hours
            # For now, we'll use a placeholder - real implementation in get_botilleria_info tool
            return True  # Placeholder
    except Exception:
        return False